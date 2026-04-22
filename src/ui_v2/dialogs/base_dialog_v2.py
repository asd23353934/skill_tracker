"""
V2 對話框基底 — 無框、可拖曳、黑灰風格
依 docs/DESIGN_V2.md
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap


class _CloseBtn(QPushButton):
    """自繪 × 關閉鈕（hover 顯紅）"""
    def __init__(self, parent, on_click):
        super().__init__(parent)
        self._hover = False
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        self.clicked.connect(on_click)

    def enterEvent(self, e):  # noqa: N802
        self._hover = True; self.update(); super().enterEvent(e)
    def leaveEvent(self, e):  # noqa: N802
        self._hover = False; self.update(); super().leaveEvent(e)

    def paintEvent(self, e):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hover:
            p.setBrush(QColor(T.RED))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 6, 6)
        col = "#ffffff" if self._hover else T.TEXT_DIM
        pix = lucide_pixmap("x", col, 14, stroke=1.8)
        x = (self.width() - 14) // 2
        y = (self.height() - 14) // 2
        p.drawPixmap(x, y, pix)
        p.end()


class BaseDialogV2(QDialog):
    """V2 對話框基底

    用法：
        dlg = MyDialog(parent, title="標題")
        dlg.body_layout().addWidget(...)
        dlg.footer_layout().addWidget(cta)
    """

    def __init__(self, parent=None, title: str = "", width: int = 460, height: int = 520):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(width, height)
        self._drag_pos = None
        self._build(title)

    def _build(self, title: str):
        # 外層空白 → 內層卡片（圓角 + 陰影感）
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("dlg_card")
        self._card.setStyleSheet(
            f"QFrame#dlg_card {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_LG}px; }}"
        )
        outer.addWidget(self._card)

        root = QVBoxLayout(self._card)
        root.setContentsMargins(T.S_LG, T.S_LG, T.S_LG, T.S_LG)
        root.setSpacing(T.S_MD)

        # ── 標題列 ──
        head = QHBoxLayout()
        head.setSpacing(T.S_SM)
        self._title_lbl = T.make_label(title, T.FONT_SECTION)
        head.addWidget(self._title_lbl)
        head.addStretch()
        head.addWidget(_CloseBtn(self, self.reject))
        root.addLayout(head)

        # ── 主內容區 ──
        self._body = QWidget()
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(T.S_MD)
        root.addWidget(self._body, 1)

        # ── 底部按鈕列 ──
        self._footer = QHBoxLayout()
        self._footer.setSpacing(T.S_SM)
        self._footer.addStretch()
        root.addLayout(self._footer)

    def body_layout(self) -> QVBoxLayout:
        return self._body_lay

    def footer_layout(self) -> QHBoxLayout:
        return self._footer

    def set_title(self, text: str):
        self._title_lbl.setText(text)

    # ── 拖曳 ──
    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):  # noqa: N802
        if self._drag_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e):  # noqa: N802
        self._drag_pos = None
