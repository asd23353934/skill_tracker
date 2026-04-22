"""
MapleWorld 資源中心 — V2
頂部：路徑列 + 掃描；中段：Tab（Unity / WebView）+ 過濾列；底部：縮圖瀑布
依 docs/DESIGN_V2.md

══════════════════════════════════════════════════════════════
綁定契約（限縮版）
══════════════════════════════════════════════════════════════
建構參數：
    MapleWorldPageV2(parent, app=None)

接線範圍（本次只接讀已快取部分）：
    - showEvent 第一次顯示 → 列出 _MAPLEWORLD_DIR 內現有 PNG
    - 依檔名前綴 web_/cdn_ 分到 WebView，其餘到 Unity tab
    - 縮圖以 QPixmap 同步載入（每 tab 限 _MAX_RENDER 張，避免慢）
    - 搜尋框即時 filter
    - Tab 切換 → 重渲對應分類

延後（標 TODO，沿用 v1 / 共用 helper 待議）：
    - [掃描資源]：v1 mapleworld_page._start_scan，含 .win.mod 解碼
    - [瀏覽] 寫回 settings
    - [縮圖點擊] 放大預覽 dialog
    - 類別 chip（角色/怪物/地圖…）

不在本頁職責：
    - 解碼 / 下載 / 檔案寫入
    - 圖片版權 / 法務聲明文字（已由 UI 顯示）
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QScrollArea, QGridLayout, QFileDialog,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QPixmap

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap, lucide_icon
from src.infrastructure.helpers import user_data_path


_MAPLEWORLD_DIR = user_data_path(os.path.join("images", "mapleworld"))
_DEFAULT_GAME_PATH = os.path.normpath(
    os.path.expandvars(r"%LOCALAPPDATA%\..\LocalLow\nexon\MapleStory Worlds")
)
_MAX_RENDER = 120        # 單 tab 最多渲染張數，避免 14k+ 卡 UI

# 縮圖快取：避免搜尋/換 tab 時對相同檔重複從硬碟解碼
# key=image_path, value=(scaled QPixmap, orig_w, orig_h)
_THUMB_CACHE: dict[str, tuple[QPixmap, int, int]] = {}


# Tab 定義：(key, label, lucide-icon, accent)
TABS = [
    ("unity", "Unity 遊戲資源",  "gamepad-2", T.ORANGE),
    ("web",   "WebView 網頁快取", "globe",    T.CYAN),
]


# ════════════════════════════════════════════════════════════
# AssetCard
# ════════════════════════════════════════════════════════════

class _AssetCard(QFrame):
    CARD_W = 148
    CARD_H = 168
    THUMB_H = 108

    def __init__(self, name: str, image_path: str | None, accent: str):
        super().__init__()
        self._name       = name
        self._accent     = accent
        self._image_path = image_path
        self._pix: QPixmap | None = None
        self._w_px = self._h_px = 0
        if image_path:
            cached = _THUMB_CACHE.get(image_path)
            if cached is None:
                pm = QPixmap(image_path)
                if not pm.isNull():
                    scaled = pm.scaled(
                        self.CARD_W - T.S_SM * 2, self.THUMB_H - 4,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    cached = (scaled, pm.width(), pm.height())
                    _THUMB_CACHE[image_path] = cached
            if cached is not None:
                self._pix, self._w_px, self._h_px = cached
        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setObjectName("asset_card")
        self.setStyleSheet(
            f"QFrame#asset_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
            f"QFrame#asset_card:hover {{ border-color: {T.BORDER_HOVER}; }}"
        )
        self._build()

    def _build(self):
        L = QVBoxLayout(self)
        L.setContentsMargins(T.S_SM, T.S_SM, T.S_SM, T.S_SM)
        L.setSpacing(T.S_XS)

        thumb = _ThumbBox(self._pix, self._accent, self.THUMB_H)
        L.addWidget(thumb)

        name_lbl = QLabel(self._name)
        name_lbl.setStyleSheet(
            f"color: {T.TEXT_HI}; font-size: 11px; font-weight: 600;"
            f" background: transparent;"
        )
        L.addWidget(name_lbl)

        meta_text = (f"PNG  ·  {self._w_px}×{self._h_px}"
                     if self._w_px else "PNG")
        meta = QLabel(meta_text)
        meta.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 9px; background: transparent;"
        )
        L.addWidget(meta)


class _ThumbBox(QFrame):
    def __init__(self, pix: QPixmap | None, accent: str, height: int):
        super().__init__()
        self._pix    = pix
        self._accent = accent
        self.setFixedHeight(height)
        self.setStyleSheet(
            f"QFrame {{ background: {T.alpha(accent, 28)};"
            f" border: 1px solid {T.BORDER_SOFT};"
            f" border-radius: {T.R_MD}px; }}"
        )

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        p = QPainter(self)
        if self._pix is not None:
            x = (self.width()  - self._pix.width())  // 2
            y = (self.height() - self._pix.height()) // 2
            p.drawPixmap(x, y, self._pix)
        else:
            pix = lucide_pixmap("image", self._accent, 36, stroke=1.4)
            x = (self.width()  - 36) // 2
            y = (self.height() - 36) // 2
            p.drawPixmap(x, y, pix)
        p.end()


# ════════════════════════════════════════════════════════════
# Tab 列
# ════════════════════════════════════════════════════════════

class _TabBtn(QPushButton):
    def __init__(self, label: str, icon: str, accent: str, active: bool, on_click=None):
        super().__init__()
        self._label  = label
        self._icon   = icon
        self._accent = accent
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        if on_click is not None:
            self.clicked.connect(on_click)
        self.toggled.connect(self._apply)
        self._apply()

    def _apply(self):
        if self.isChecked():
            color = self._accent
            bg    = T.alpha(self._accent, 32)
        else:
            color = T.TEXT_DIM
            bg    = "transparent"
        self.setIcon(lucide_icon(self._icon, color, 14, stroke=1.6))
        self.setIconSize(QSize(14, 14))
        self.setText(f"  {self._label}")
        self.setStyleSheet(
            f"QPushButton {{ color: {color}; background: {bg};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 14px; font-size: 12px; font-weight: 600;"
            f" text-align: left; }}"
            f"QPushButton:hover {{ color: {T.TEXT_HI}; }}"
        )


# ════════════════════════════════════════════════════════════
# MapleWorldPageV2
# ════════════════════════════════════════════════════════════

class MapleWorldPageV2(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._current_tab = "unity"
        self._search_text = ""
        self._loaded = False
        # 全部檔名列表（一次列目錄，不重複 IO）
        self._files: dict[str, list[str]] = {"unity": [], "web": []}
        self._build()

    def showEvent(self, e):  # noqa: N802
        super().showEvent(e)
        if not self._loaded:
            self._loaded = True
            self._scan_dir()
            self._render_grid()

    # ──────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(T.S_2XL, T.S_SM, T.S_2XL, T.S_2XL)
        root.setSpacing(T.S_LG)

        # 標題
        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        head.addWidget(T.make_label("資源中心", T.FONT_SECTION))
        head.addSpacing(T.S_SM)
        head.addWidget(T.make_label(
            "讀取本機 MapleStory Worlds 快取 · 圖片版權屬 Nexon · 僅供個人使用",
            T.FONT_CAPTION,
        ))
        head.addStretch()
        root.addLayout(head)

        # 路徑列
        root.addWidget(self._build_path_card())

        # Tab 列 + 統計
        tab_row = QHBoxLayout()
        tab_row.setSpacing(T.S_XS)
        self._tab_btns: dict[str, _TabBtn] = {}
        for key, label, icon, accent in TABS:
            btn = _TabBtn(label, icon, accent,
                          active=(key == self._current_tab),
                          on_click=lambda _=False, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn
            tab_row.addWidget(btn)
        tab_row.addStretch()

        self._stat_lbl = QLabel("尚未載入")
        self._stat_lbl.setStyleSheet(
            f"color: {T.TEXT_MUTED}; font-size: 11px; background: transparent;"
        )
        tab_row.addWidget(self._stat_lbl)
        root.addLayout(tab_row)

        # 搜尋列
        filt_row = QHBoxLayout()
        filt_row.setSpacing(T.S_XS)
        search = QLineEdit()
        search.setPlaceholderText("搜尋資源名稱…")
        search.setFixedHeight(28)
        search.setFixedWidth(260)
        search.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 10px; font-size: 11px; }}"
            f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}"
        )
        search.textChanged.connect(self._on_search)
        filt_row.addWidget(search)
        filt_row.addStretch()
        root.addLayout(filt_row)

        # 縮圖 grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._inner)
        self._grid.setContentsMargins(0, 0, T.S_XS, 0)
        self._grid.setHorizontalSpacing(T.S_SM)
        self._grid.setVerticalSpacing(T.S_SM)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._inner)
        root.addWidget(scroll, 1)

    def _build_path_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("path_card")
        card.setStyleSheet(
            f"QFrame#path_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_LG}px; }}"
        )
        card.setFixedHeight(56)
        ph = QHBoxLayout(card)
        ph.setContentsMargins(T.S_LG, T.S_SM, T.S_SM, T.S_SM)
        ph.setSpacing(T.S_SM)

        folder_lbl = QLabel()
        folder_lbl.setFixedSize(18, 18)
        folder_lbl.setPixmap(lucide_pixmap("folder-open", T.YELLOW, 18, stroke=1.6))
        folder_lbl.setStyleSheet("background: transparent;")
        ph.addWidget(folder_lbl)

        ph.addWidget(T.make_label("遊戲路徑", T.FONT_BODY,
                                  color_override=T.TEXT_DIM))

        self._path_input = QLineEdit(_DEFAULT_GAME_PATH)
        self._path_input.setFixedHeight(30)
        self._path_input.setStyleSheet(
            f"QLineEdit {{ color: {T.TEXT}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 10px; font-size: 11px;"
            f" font-family: 'Consolas', monospace; }}"
            f"QLineEdit:focus {{ border-color: {T.ORANGE}; }}"
        )
        ph.addWidget(self._path_input, 1)

        browse_btn = QPushButton("瀏覽")
        browse_btn.setFixedHeight(30)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setIcon(lucide_icon("folder-open", T.TEXT, 13, stroke=1.6))
        browse_btn.setIconSize(QSize(13, 13))
        browse_btn.setStyleSheet(
            f"QPushButton {{ color: {T.TEXT}; background: {T.BG_INPUT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" border-color: {T.BORDER_HOVER}; }}"
        )
        browse_btn.clicked.connect(self._browse)
        ph.addWidget(browse_btn)

        scan_btn = QPushButton("掃描資源")
        scan_btn.setFixedHeight(30)
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.setIcon(lucide_icon("search", "#ffffff", 13, stroke=1.8))
        scan_btn.setIconSize(QSize(13, 13))
        scan_btn.setStyleSheet(
            f"QPushButton {{ color: #ffffff; background: {T.ORANGE};"
            f" border: none; border-radius: {T.R_SM}px;"
            f" padding: 0 14px; font-size: 11px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
        scan_btn.clicked.connect(self._on_scan)
        ph.addWidget(scan_btn)

        return card

    # ──────────────────────────────────────────
    # 操作
    # ──────────────────────────────────────────
    def _scan_dir(self):
        if not os.path.isdir(_MAPLEWORLD_DIR):
            return
        try:
            files = sorted(
                f for f in os.listdir(_MAPLEWORLD_DIR)
                if f.lower().endswith(".png")
            )
        except OSError:
            return
        for f in files:
            if f.startswith("web_") or f.startswith("cdn_"):
                self._files["web"].append(f)
            else:
                self._files["unity"].append(f)

    def _switch_tab(self, key: str):
        if key == self._current_tab:
            self._tab_btns[key].setChecked(True)
            return
        self._current_tab = key
        for k, btn in self._tab_btns.items():
            btn.setChecked(k == key)
        self._render_grid()

    def _on_search(self, text: str):
        self._search_text = text.strip().lower()
        self._render_grid()

    def _on_scan(self):
        if self.app is not None and hasattr(self.app, "toast"):
            self.app.toast.show("掃描功能尚未接到 V2，請暫用 V1 版", "info")

    def _browse(self):
        path = QFileDialog.getExistingDirectory(
            self, "選擇遊戲資料夾", self._path_input.text()
        )
        if path:
            self._path_input.setText(os.path.normpath(path))

    # ──────────────────────────────────────────
    # 渲染
    # ──────────────────────────────────────────
    def _render_grid(self):
        # 清空 grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        files = self._files.get(self._current_tab, [])
        if self._search_text:
            matches = [f for f in files if self._search_text in f.lower()]
        else:
            matches = files

        total = len(matches)
        shown = min(total, _MAX_RENDER)

        # 統計列
        full_total = sum(len(v) for v in self._files.values())
        if not self._loaded or full_total == 0:
            self._stat_lbl.setText("尚未載入快取（執行 V1 掃描以填入 images/mapleworld/）")
        elif self._search_text:
            self._stat_lbl.setText(
                f"搜尋結果 {total}（顯示 {shown}） · 全庫 {full_total}"
            )
        else:
            self._stat_lbl.setText(
                f"本 tab {total}（顯示 {shown}） · 全庫 {full_total}"
            )

        if shown == 0:
            empty = QLabel("沒有符合的資源" if self._search_text else
                           "此 tab 尚無已快取的圖片")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {T.TEXT_MUTED}; font-size: 13px;"
                f" background: transparent; padding: 40px;"
            )
            self._grid.addWidget(empty, 0, 0, 1, 7)
            return

        accent = next((a for k, _, _, a in TABS if k == self._current_tab),
                      T.PURPLE)
        cols = 7
        for i, fname in enumerate(matches[:shown]):
            r, c = divmod(i, cols)
            name = os.path.splitext(fname)[0]
            path = os.path.join(_MAPLEWORLD_DIR, fname)
            self._grid.addWidget(_AssetCard(name, path, accent), r, c)
