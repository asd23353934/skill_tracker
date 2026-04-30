"""
V2 頁首 — 純拖曳區 + 視窗控制按鈕（min / max / close）+ 更新提示 chip
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QIcon
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap


class WinCtrlBtn(QPushButton):
    """自繪視窗控制按鈕：細線 minimize / square maximize / cross close"""

    KIND_MIN   = "min"
    KIND_MAX   = "max"
    KIND_CLOSE = "close"

    def __init__(self, parent, kind, on_click):
        super().__init__(parent)
        self._kind = kind
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(on_click)
        self._hover = False
        self.setStyleSheet("background: transparent; border: none;")

    def enterEvent(self, e):  # noqa: N802
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):  # noqa: N802
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, e):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景（hover 時變色）
        if self._hover:
            bg = QColor(T.RED) if self._kind == self.KIND_CLOSE else QColor(T.BG_HOVER)
            p.setBrush(bg)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 6, 6)

        if self._hover and self._kind == self.KIND_CLOSE:
            col = "#ffffff"
        elif self._hover:
            col = T.TEXT_HI
        else:
            col = T.TEXT_DIM

        name_map = {
            self.KIND_MIN:   "minus",
            self.KIND_MAX:   "square",
            self.KIND_CLOSE: "x",
        }
        pix = lucide_pixmap(name_map[self._kind], col, 14, stroke=1.6)
        x = (self.width() - 14) // 2
        y = (self.height() - 14) // 2
        p.drawPixmap(x, y, pix)
        p.end()


class UpdateChip(QPushButton):
    """有新版時出現的可點擊提示按鈕（橘框 lucide icon + 版本字串）"""

    def __init__(self, parent):
        super().__init__(parent)
        self._latest = ""
        self._icon_idle = None
        self._icon_hover = None
        self.setVisible(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(22)
        self.setIconSize(QSize(12, 12))
        self.setStyleSheet(
            f"QPushButton {{"
            f" background: transparent;"
            f" color: {T.ORANGE};"
            f" border: 1px solid {T.ORANGE};"
            f" border-radius: 11px;"
            f" padding: 0 10px 0 6px;"
            f" font-family: 'Microsoft JhengHei';"
            f" font-size: 11px;"
            f" font-weight: 500; }}"
            f"QPushButton:hover {{"
            f" background: {T.ORANGE};"
            f" color: white; }}"
        )

    def set_latest(self, version: str):
        if not version:
            self.setVisible(False)
            self._latest = ""
            return
        self._latest = version
        self._icon_idle  = QIcon(lucide_pixmap("arrow-up-circle", T.ORANGE, 12, stroke=2.0))
        self._icon_hover = QIcon(lucide_pixmap("arrow-up-circle", "#ffffff", 12, stroke=2.0))
        self.setIcon(self._icon_idle)
        self.setText(f"v{version}")
        self.setToolTip(f"點擊更新到 v{version}")
        self.setVisible(True)

    def enterEvent(self, e):  # noqa: N802
        if self._icon_hover:
            self.setIcon(self._icon_hover)
        super().enterEvent(e)

    def leaveEvent(self, e):  # noqa: N802
        if self._icon_idle:
            self.setIcon(self._icon_idle)
        super().leaveEvent(e)


class HeaderV2(QFrame):
    """精簡頁首：左拖曳 padding + 右更新提示 + 視窗控制按鈕"""

    update_requested = Signal()

    def __init__(self, parent, window):
        super().__init__(parent)
        self.window_ref = window
        self._drag_pos  = None
        self._build()

    def _build(self):
        self.setFixedHeight(T.HEADER_H)
        self.setObjectName("header_v2")
        self.setStyleSheet(
            f"QFrame#header_v2 {{ background: transparent; border: none; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(28, 10, 14, 10)
        lay.setSpacing(6)
        lay.addStretch()
        self.update_chip = UpdateChip(self)
        self.update_chip.clicked.connect(self.update_requested.emit)
        lay.addWidget(self.update_chip)
        lay.addSpacing(6)
        lay.addWidget(WinCtrlBtn(self, WinCtrlBtn.KIND_MIN, self.window_ref.showMinimized))
        lay.addWidget(WinCtrlBtn(self, WinCtrlBtn.KIND_MAX, self._toggle_max))
        lay.addWidget(WinCtrlBtn(self, WinCtrlBtn.KIND_CLOSE, self.window_ref.close))

    def set_update_available(self, version: str):
        """有新版時呼叫；version 為空字串會隱藏 chip。"""
        self.update_chip.set_latest(version or "")

    def _toggle_max(self):
        if self.window_ref.isMaximized():
            self.window_ref.showNormal()
        else:
            self.window_ref.showMaximized()

    # 拖曳
    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window_ref.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):  # noqa: N802
        if self._drag_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.window_ref.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e):  # noqa: N802
        self._drag_pos = None
