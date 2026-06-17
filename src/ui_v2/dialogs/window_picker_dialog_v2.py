"""
視窗挑選器 — V2（縮圖卡片網格）

列出目前開啟的頂層視窗，每張卡片顯示該視窗的「畫面縮圖」+ 標題，供使用者用畫面
辨識並選定「快捷鍵限定」的目標視窗。點選 → 橘框高亮；雙擊或「確認」→ 選定。
附「重新整理」重新列舉並重抓縮圖。

縮圖透過 src.infrastructure.window_enum.capture_window_thumbnail（PrintWindow，與
z-order 無關）擷取；最小化 / 擷取失敗的視窗以 lucide 圖示 + 標題的退回卡片呈現。

選定結果：dlg.exec() 回 Accepted 後，讀 dlg.selected_exe() / dlg.selected_label()。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import QImage, QPixmap, QFont, QFontMetrics, QPainter, QColor, QPen

from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.dialogs.base_dialog_v2 import BaseDialogV2
from src.ui_v2.lucide import lucide_pixmap
from src.infrastructure import window_enum

_COLS = 2
_THUMB_W = 232
_THUMB_H = 130
_CARD_W = _THUMB_W + 16
_CARD_H = _THUMB_H + 44


def _thumb_pixmap(data_wh) -> QPixmap | None:
    """window_enum 的 (bgra_bytes, w, h) → QPixmap；失敗回 None。"""
    if not data_wh:
        return None
    data, w, h = data_wh
    if not data or w <= 0 or h <= 0:
        return None
    # BGRA top-down → QImage Format_RGB32（小端序對應 BGRX，忽略 alpha）
    # 顯式 bytesPerLine = w*4，把「32-bit 無列填充」契約寫明（與 window_enum 的 tw*th*4 對齊）
    img = QImage(data, w, h, w * 4, QImage.Format.Format_RGB32).copy()
    if img.isNull():
        return None
    return QPixmap.fromImage(img)


class _WindowCard(QFrame):
    """單一視窗卡片：縮圖 + 標題

    全部自繪、**完全不放任何子 widget**，整張卡片任意位置的點擊都由 mousePressEvent
    處理。（本對話框已關閉 WA_TranslucentBackground 改為不透明視窗，見
    WindowPickerDialogV2.__init__，否則截圖縮圖 alpha=0 區會發生點擊穿透。）
    """

    def __init__(self, info: dict, pixmap: QPixmap | None, on_select, on_confirm):
        super().__init__()
        self.info = info
        self._selected = False
        self._on_select = on_select
        self._on_confirm = on_confirm
        self.setFixedSize(_CARD_W, _CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 縮圖：縮放置中；無則用 lucide 退回圖示（最小化 / 擷取失敗）
        if pixmap is not None and not pixmap.isNull():
            self._pix = pixmap.scaled(
                _THUMB_W, _THUMB_H,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            self._pix = lucide_pixmap("image", T.TEXT_DIM, 40)

        fm = QFontMetrics(QFont(T.FONT_FAMILY, 11))
        self._title = fm.elidedText(info.get("title", ""),
                                    Qt.TextElideMode.ElideRight, _THUMB_W)

    def set_selected(self, value: bool):
        self._selected = value
        self.update()

    def paintEvent(self, e):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 卡片底 + 邊框（選取時橘框）
        p.setPen(QPen(QColor(T.ORANGE if self._selected else T.BORDER), 1))
        p.setBrush(QColor(T.BG_HOVER if self._selected else T.BG_ELEVATED))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1),
                          T.R_SM, T.R_SM)
        # 縮圖底
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(T.BG_INPUT))
        p.drawRoundedRect(QRectF(8, 8, _THUMB_W, _THUMB_H), T.R_SM, T.R_SM)
        # 縮圖（置中）
        if self._pix and not self._pix.isNull():
            px = 8 + (_THUMB_W - self._pix.width()) // 2
            py = 8 + (_THUMB_H - self._pix.height()) // 2
            p.drawPixmap(int(px), int(py), self._pix)
        # 標題
        p.setPen(QColor(T.TEXT))
        p.setFont(QFont(T.FONT_FAMILY, 11))
        p.drawText(QRect(8, 8 + _THUMB_H + 4, _THUMB_W, 22),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   self._title)
        p.end()

    def mousePressEvent(self, e):  # noqa: N802
        self._on_select(self)
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):  # noqa: N802
        self._on_select(self)
        self._on_confirm()


class WindowPickerDialogV2(BaseDialogV2):
    """視窗挑選器（縮圖卡片網格）"""

    def __init__(self, parent=None, app=None):
        super().__init__(parent, title="選擇目標視窗", width=620, height=560)
        # 本對話框需「整片卡片皆可點」。半透明視窗（WA_TranslucentBackground）在 alpha=0
        # 的區域（如 PrintWindow 截圖縮圖）會發生 Windows 視窗層級的「點擊穿透」——事件
        # 直接落到背後視窗、根本到不了挑選器，導致截圖卡片選不到（純文字/退回圖示卡因
        # 不透明而正常）。故關閉半透明、改為不透明視窗（標準矩形命中測試，全區可點）。
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(f"QDialog {{ background: {T.BG_SURFACE}; }}")
        self.app = app
        self._cards: list[_WindowCard] = []
        self._selected_info: dict | None = None
        self._build_body()
        self._build_footer()
        self._reload()

    # ── 主內容 ──
    def _build_body(self):
        body = self.body_layout()

        # 頂部：說明 + 重新整理
        top = QHBoxLayout()
        hint = QLabel("點選要限定的視窗（雙擊直接選定）")
        hint.setStyleSheet(f"color: {T.TEXT_DIM}; background: transparent; font-size: 11px;")
        top.addWidget(hint)
        top.addStretch()
        refresh = QPushButton("重新整理")
        refresh.setFixedHeight(28)
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.setStyleSheet(
            f"QPushButton {{ background: {T.BG_INPUT}; color: {T.TEXT};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 12px; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {T.TEXT_HI}; border-color: {T.BORDER_HOVER}; }}"
        )
        refresh.clicked.connect(self._reload)
        top.addWidget(refresh)
        body.addLayout(top)

        # 捲動區 + 卡片網格
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {T.BG_INPUT}; border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; }}"
        )
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(10, 10, 10, 10)
        self._grid.setSpacing(10)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._grid_host)
        body.addWidget(self._scroll, 1)

    def _build_footer(self):
        footer = self.footer_layout()
        cancel = QPushButton("取消")
        cancel.setFixedHeight(30)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {T.TEXT_DIM};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px;"
            f" padding: 0 16px; font-size: 12px; }}"
            f"QPushButton:hover {{ color: {T.TEXT_HI}; border-color: {T.BORDER_HOVER}; }}"
        )
        cancel.clicked.connect(self.reject)

        self._confirm_btn = QPushButton("確認")
        self._confirm_btn.setFixedHeight(30)
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setStyleSheet(
            f"QPushButton {{ background: {T.ORANGE}; color: #ffffff; border: none;"
            f" border-radius: {T.R_SM}px; padding: 0 18px; font-size: 12px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
            f"QPushButton:disabled {{ background: {T.BG_ELEVATED}; color: {T.TEXT_DIM}; }}"
        )
        self._confirm_btn.clicked.connect(self._confirm)

        footer.addWidget(cancel)
        footer.addWidget(self._confirm_btn)

    # ── 列舉 + 縮圖 ──
    def _reload(self):
        # 清空舊卡片
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards = []
        self._selected_info = None
        self._confirm_btn.setEnabled(False)

        current_exe = (getattr(self.app, "hotkey_app_target_exe", "") or "").lower()
        windows = window_enum.list_windows()
        for idx, info in enumerate(windows):
            pixmap = _thumb_pixmap(window_enum.capture_window_thumbnail(
                info["hwnd"], _THUMB_W, _THUMB_H))
            card = _WindowCard(info, pixmap, self._select_card, self._confirm)
            self._grid.addWidget(card, idx // _COLS, idx % _COLS)
            self._cards.append(card)
            # 預選目前已設定的目標
            if current_exe and info.get("exe", "").lower() == current_exe and self._selected_info is None:
                self._select_card(card)

        if not windows:
            empty = QLabel("找不到可選的視窗")
            empty.setStyleSheet(f"color: {T.TEXT_DIM}; background: transparent;")
            self._grid.addWidget(empty, 0, 0)

    def _select_card(self, card: _WindowCard):
        for c in self._cards:
            c.set_selected(c is card)
        self._selected_info = card.info
        self._confirm_btn.setEnabled(True)

    def _confirm(self):
        if self._selected_info is not None:
            self.accept()

    # ── 結果 ──
    def selected_exe(self) -> str:
        return (self._selected_info or {}).get("exe", "")

    def selected_label(self) -> str:
        return (self._selected_info or {}).get("title", "")
