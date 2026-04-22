"""
浮動圖片頁面 — V2
垂直列表，每列：縮圖 | 名稱+檔名 | 顯示/隱藏 + 透明度 + 刪除
依 docs/DESIGN_V2.md

══════════════════════════════════════════════════════════════
綁定契約
══════════════════════════════════════════════════════════════
建構參數：
    OverlayPageV2(parent, app=None)
        app 提供 overlay_manager / config_manager / toast / after / overlay_page
        app=None 時顯示假資料（純預覽模式）

讀取：
    app.overlay_manager.get_all() -> list[dict]
        每筆：{ id, name, file, alpha, x, y, width, height }
    開啟中判斷：overlay_id in app.overlay_manager.active_windows

操作：
    [新增圖片]  → QFileDialog → app.overlay_manager.add_overlay(src, name)
    [顯示/隱藏] → app.overlay_manager.toggle(id)
    [透明度滑桿] → app.overlay_manager.set_alpha(id, 0.10~1.00)
    [刪除]      → 確認後 app.overlay_manager.delete_overlay(id, delete_file=False)

寫回：
    上述 manager 內部會呼叫 config_manager.save()，本頁不直接寫 config

刷新時機：
    - __init__ 第一次 build
    - 新增/刪除 後 rebuild_cards
    - 視窗 X 關閉時 manager 回呼 refresh_toggle(id)，只更新該卡

不在本頁職責：
    - 視窗位置 / 大小（由 OverlayWindow 拖曳寫回）
    - 全域 overlay 開關
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QSlider, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QPixmap

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap, lucide_icon
from src.infrastructure.helpers import user_data_path


_SUPPORTED_FILTER = "圖片與 GIF (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有檔案 (*.*)"


# 假資料（app=None 時使用）
DEMO_OVERLAYS = [
    {"id": "d1", "name": "地圖標記",  "file": "marker.png",    "alpha": 0.85},
    {"id": "d2", "name": "計時器框",  "file": "timer_box.gif", "alpha": 0.60},
    {"id": "d3", "name": "BUFF 提示", "file": "buff.png",      "alpha": 1.00},
    {"id": "d4", "name": "怪物路徑",  "file": "path.png",      "alpha": 0.45},
    {"id": "d5", "name": "血條疊加",  "file": "hp_bar.gif",    "alpha": 0.75},
]


# ════════════════════════════════════════════════════════════
# Thumb — 縮圖框（讀真實檔案；無檔則 image icon）
# ════════════════════════════════════════════════════════════

class _Thumb(QFrame):
    SIZE = 72

    def __init__(self, image_path: str | None = None):
        super().__init__()
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setStyleSheet(
            f"QFrame {{ background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_MD}px; }}"
        )
        self._pix: QPixmap | None = None
        if image_path:
            pm = QPixmap(image_path)
            if not pm.isNull():
                self._pix = pm.scaled(
                    self.SIZE - 6, self.SIZE - 6,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        p = QPainter(self)
        if self._pix is not None:
            x = (self.SIZE - self._pix.width()) // 2
            y = (self.SIZE - self._pix.height()) // 2
            p.drawPixmap(x, y, self._pix)
        else:
            pix = lucide_pixmap("image", T.TEXT_MUTED, 28, stroke=1.4)
            x = (self.SIZE - 28) // 2
            y = (self.SIZE - 28) // 2
            p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# ToggleVisibilityBtn
# ════════════════════════════════════════════════════════════

class _VisToggle(QPushButton):
    def __init__(self, visible: bool, on_toggle=None):
        super().__init__()
        self._visible  = visible
        self._on_toggle = on_toggle
        self.setFixedHeight(28)
        self.setMinimumWidth(86)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._toggle)
        self._apply()

    def _toggle(self):
        if self._on_toggle is not None:
            self._on_toggle()
            return
        self._visible = not self._visible
        self._apply()

    def set_visible(self, v: bool):
        self._visible = v
        self._apply()

    def is_visible(self) -> bool:
        return self._visible

    def _apply(self):
        if self._visible:
            color  = T.GREEN
            text   = "顯示中"
            icon   = "eye"
            bg     = T.alpha(color, 38)
            bg_h   = T.alpha(color, 70)
        else:
            color  = T.TEXT_MUTED
            text   = "已隱藏"
            icon   = "eye-off"
            bg     = T.BG_INPUT
            bg_h   = T.BG_HOVER
        self.setIcon(lucide_icon(icon, color, 14, stroke=1.6))
        self.setIconSize(QSize(14, 14))
        self.setText(f"  {text}")
        self.setStyleSheet(
            f"QPushButton {{ color: {color}; background: {bg};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; font-weight: 600;"
            f" text-align: left; }}"
            f"QPushButton:hover {{ background: {bg_h}; }}"
        )


# ════════════════════════════════════════════════════════════
# DeleteBtn
# ════════════════════════════════════════════════════════════

class _DelBtn(QPushButton):
    def __init__(self, on_click=None):
        super().__init__()
        self._hover = False
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("刪除")
        self.setStyleSheet(
            f"QPushButton {{ background: transparent;"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px; }}"
            f"QPushButton:hover {{ background: {T.RED}; border-color: {T.RED}; }}"
        )
        if on_click is not None:
            self.clicked.connect(on_click)

    def enterEvent(self, e):  # noqa: N802
        self._hover = True; self.update(); super().enterEvent(e)
    def leaveEvent(self, e):  # noqa: N802
        self._hover = False; self.update(); super().leaveEvent(e)

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        col = "#ffffff" if self._hover else T.TEXT_DIM
        pix = lucide_pixmap("trash-2", col, 14, stroke=1.6)
        p = QPainter(self)
        x = (self.width() - 14) // 2
        y = (self.height() - 14) // 2
        p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# AlphaSlider
# ════════════════════════════════════════════════════════════

def _alpha_slider(value: int) -> QSlider:
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(10, 100)
    s.setValue(value)
    s.setFixedWidth(140)
    s.setStyleSheet(
        f"QSlider::groove:horizontal {{ background: {T.BG_INPUT};"
        f" height: 4px; border-radius: 2px; }}"
        f"QSlider::sub-page:horizontal {{ background: {T.ORANGE};"
        f" height: 4px; border-radius: 2px; }}"
        f"QSlider::handle:horizontal {{ background: {T.ORANGE};"
        f" width: 12px; height: 12px; margin: -5px 0;"
        f" border-radius: 6px; border: 2px solid {T.BG_SURFACE}; }}"
        f"QSlider::handle:horizontal:hover {{ background: #ff9d5a; }}"
    )
    return s


# ════════════════════════════════════════════════════════════
# OverlayCard — 單列
# ════════════════════════════════════════════════════════════

class OverlayCard(QFrame):
    HEIGHT = 96

    def __init__(self, parent, data: dict, app=None, page=None):
        super().__init__(parent)
        self.data       = data
        self.app        = app
        self.page       = page
        self.overlay_id = data.get("id", "")
        self.setFixedHeight(self.HEIGHT)
        self.setObjectName("ovl_card")
        self.setStyleSheet(
            f"QFrame#ovl_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
            f"QFrame#ovl_card:hover {{ border-color: {T.BORDER_HOVER}; }}"
        )
        self._build()

    def _build(self):
        name  = self.data.get("name", "未命名")
        file  = self.data.get("file", "")
        alpha = float(self.data.get("alpha", 0.9))
        if self.app is not None:
            visible = self.overlay_id in self.app.overlay_manager.active_windows
            image_path = user_data_path(f"overlays/{file}") if file else None
        else:
            visible = False
            image_path = None

        L = QHBoxLayout(self)
        L.setContentsMargins(T.S_MD, T.S_SM, T.S_MD, T.S_SM)
        L.setSpacing(T.S_LG)

        # 縮圖
        L.addWidget(_Thumb(image_path))

        # 中：名稱 + 檔名
        mid = QVBoxLayout()
        mid.setContentsMargins(0, 0, 0, 0)
        mid.setSpacing(2)
        mid.addStretch()
        name_lbl = T.make_label(name, T.FONT_CARD_TITLE, color_override=T.TEXT_HI)
        mid.addWidget(name_lbl)
        file_lbl = QLabel(file)
        file_lbl.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 10px; background: transparent;"
        )
        mid.addWidget(file_lbl)
        mid.addStretch()
        L.addLayout(mid, 1)

        # 右：可見性 + 透明度 + 刪除
        self._vis_btn = _VisToggle(visible, on_toggle=self._on_toggle)
        L.addWidget(self._vis_btn)

        # 透明度
        alpha_wrap = QHBoxLayout()
        alpha_wrap.setSpacing(8)
        alpha_wrap.setContentsMargins(0, 0, 0, 0)

        a_lbl = QLabel("透明度")
        a_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        alpha_wrap.addWidget(a_lbl)

        slider = _alpha_slider(int(alpha * 100))
        alpha_wrap.addWidget(slider)

        pct = QLabel(f"{int(alpha * 100)}%")
        pct.setFixedWidth(34)
        pct.setStyleSheet(
            f"color: {T.ORANGE}; font-size: 11px; font-weight: 700;"
            f" background: transparent;"
        )
        slider.valueChanged.connect(lambda v: pct.setText(f"{v}%"))
        slider.valueChanged.connect(self._on_alpha)
        alpha_wrap.addWidget(pct)

        L.addLayout(alpha_wrap)

        L.addWidget(_DelBtn(on_click=self._on_delete))

    # ── 操作 ──
    def _on_toggle(self):
        if self.app is None:
            self._vis_btn.set_visible(not self._vis_btn.is_visible())
            return
        self.app.overlay_manager.toggle(self.overlay_id)
        self.sync_toggle_state()

    def _on_alpha(self, value: int):
        if self.app is None:
            return
        self.app.overlay_manager.set_alpha(self.overlay_id, value / 100.0)

    def _on_delete(self):
        if self.app is None:
            return
        name = self.data.get("name", "此圖片")
        reply = QMessageBox.question(
            self, "刪除確認",
            f"確定要刪除「{name}」嗎？\n（僅移除設定，不刪除圖片檔案）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.app.overlay_manager.delete_overlay(self.overlay_id, delete_file=False)
            if self.page is not None:
                self.page.rebuild_cards()

    def sync_toggle_state(self):
        if self.app is None:
            return
        is_open = self.overlay_id in self.app.overlay_manager.active_windows
        self._vis_btn.set_visible(is_open)


# ════════════════════════════════════════════════════════════
# OverlayPageV2
# ════════════════════════════════════════════════════════════

class OverlayPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._cards: dict = {}        # overlay_id → OverlayCard
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # ── 工具列 ──
        bar = QHBoxLayout()
        bar.setSpacing(T.S_SM)
        bar.addWidget(T.make_label("浮動圖片", T.FONT_SECTION))

        hint = T.make_label("PNG / JPG / GIF | 拖曳移動 | hover 顯示 X 關閉",
                            T.FONT_CAPTION)
        bar.addSpacing(T.S_SM)
        bar.addWidget(hint)
        bar.addStretch()

        add_btn = QPushButton("新增圖片")
        add_btn.setIcon(lucide_icon("plus", "#ffffff", 14, stroke=2.0))
        add_btn.setIconSize(QSize(14, 14))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setFixedHeight(T.BTN_H)
        add_btn.setStyleSheet(
            f"QPushButton {{ color: #ffffff; background: {T.ORANGE};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 14px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
        add_btn.clicked.connect(self._add_image)
        bar.addWidget(add_btn)
        root.addLayout(bar)

        # ── 卡片捲動區（容器，rebuild 時清空再填）──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._inner)
        self._list_layout.setContentsMargins(0, 0, T.S_XS, 0)
        self._list_layout.setSpacing(T.S_SM)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._inner)
        root.addWidget(scroll, 1)

        self.rebuild_cards()

    # ──────────────────────────────────────────
    # 對外 API（manager 會呼叫）
    # ──────────────────────────────────────────
    def rebuild_cards(self):
        # 清空
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._cards.clear()

        if self.app is not None:
            data_list = self.app.overlay_manager.get_all()
        else:
            data_list = DEMO_OVERLAYS

        if not data_list:
            empty = QLabel("尚未新增任何圖片\n點擊「新增圖片」上傳 PNG / JPG / GIF")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {T.TEXT_MUTED}; font-size: 13px;"
                f" background: transparent; padding: 40px;"
            )
            self._list_layout.addWidget(empty)
            return

        for data in data_list:
            card = OverlayCard(self._inner, data, app=self.app, page=self)
            self._list_layout.addWidget(card)
            self._cards[data.get("id", "")] = card

    def refresh_toggle(self, overlay_id: str):
        card = self._cards.get(overlay_id)
        if card is not None:
            card.sync_toggle_state()

    # ──────────────────────────────────────────
    # 新增
    # ──────────────────────────────────────────
    def _add_image(self):
        if self.app is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "選擇圖片或 GIF", "", _SUPPORTED_FILTER
        )
        if not path:
            return
        name = os.path.splitext(os.path.basename(path))[0]
        item = self.app.overlay_manager.add_overlay(path, name)
        if item is None:
            self.app.toast.show("上傳失敗，不支援的圖片格式或檔案複製失敗。", "error")
            return
        self.rebuild_cards()
