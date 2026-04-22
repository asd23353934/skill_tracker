"""
V2 頁首 — 無底線、無 tabs
左：頭像 + 問候語｜右：下拉選擇 + 圖示按鈕 + 視窗控制
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
)
from src.ui_v2.components import ArrowComboBox
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QPen
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_pixmap


class GlyphBtn(QPushButton):
    """自繪線條圖示按鈕（避免字型渲染不一致）

    kind: 'bell' | 'user'
    """
    def __init__(self, parent, kind: str):
        super().__init__(parent)
        self._kind  = kind
        self._hover = False
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ background: {T.BG_SURFACE};"
            f" border: 1px solid {T.BORDER}; border-radius: {T.R_SM}px; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" border-color: {T.BORDER_HOVER}; }}"
        )

    def enterEvent(self, e):  # noqa: N802
        self._hover = True; self.update(); super().enterEvent(e)

    def leaveEvent(self, e):  # noqa: N802
        self._hover = False; self.update(); super().leaveEvent(e)

    def paintEvent(self, e):  # noqa: N802
        super().paintEvent(e)
        col = T.TEXT_HI if self._hover else T.TEXT_DIM
        pix = lucide_pixmap(self._kind, col, 16, stroke=1.6)
        p = QPainter(self)
        x = (self.width() - 16) // 2
        y = (self.height() - 16) // 2
        p.drawPixmap(x, y, pix)
        p.end()


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


class HeaderV2(QFrame):
    """頂部問候列（80px 高，無底線）"""

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
        lay.setContentsMargins(28, 14, 14, 14)
        lay.setSpacing(14)

        # ── 左：頭像 + 問候 ──
        avatar = QFrame()
        avatar.setFixedSize(44, 44)
        avatar.setStyleSheet(
            f"QFrame {{ background: qlineargradient("
            f" x1:0, y1:0, x2:1, y2:1,"
            f" stop:0 {T.PURPLE}, stop:1 {T.PINK});"
            f" border-radius: 22px;"
            f" border: 2px solid {T.BG_ELEVATED}; }}"
        )
        lay.addWidget(avatar)

        text_box = QVBoxLayout()
        text_box.setSpacing(0)
        text_box.setContentsMargins(0, 0, 0, 0)
        greet = QLabel("Good Evening, 玩家！")
        greet.setStyleSheet(
            f"color: {T.TEXT_HI}; font-size: 18px; font-weight: 700;"
            f" background: transparent;"
        )
        sub = QLabel("今天也來追蹤你的技能冷卻吧 ✦")
        sub.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 11px; background: transparent;"
        )
        text_box.addWidget(greet)
        text_box.addWidget(sub)
        lay.addLayout(text_box)

        lay.addStretch()

        # ── 右：下拉 + 動作 + 視窗控制 ──
        combo = ArrowComboBox()
        combo.addItems(["默認配置", "輔助配置", "BOSS 配置"])
        combo.setFixedHeight(36)
        combo.setMinimumWidth(140)
        combo.setStyleSheet(
            f"QComboBox {{ background: {T.BG_SURFACE}; color: {T.TEXT};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; padding: 0 12px;"
            f" font-size: 12px; }}"
            f"QComboBox:hover {{ border-color: {T.BORDER_HOVER}; }}"
            f"QComboBox::drop-down {{ border: none; width: 18px; }}"
        )
        lay.addWidget(combo)

        # 主 CTA（橘色方形圖示按鈕）
        from PySide6.QtGui import QIcon
        cta = QPushButton()
        cta.setIcon(QIcon(lucide_pixmap("plus", "#ffffff", 18, stroke=2.0)))
        cta.setIconSize(QSize(18, 18))
        cta.setFixedSize(36, 36)
        cta.setCursor(Qt.CursorShape.PointingHandCursor)
        cta.setStyleSheet(
            f"QPushButton {{ background: {T.ORANGE};"
            f" border: none; border-radius: {T.R_SM}px; padding: 0; }}"
            f"QPushButton:hover {{ background: #ff9d5a; }}"
        )
        lay.addWidget(cta)

        # 通知 / 個人（自繪）
        lay.addWidget(GlyphBtn(self, "bell"))
        lay.addWidget(GlyphBtn(self, "user"))

        lay.addSpacing(6)

        # 視窗控制（自繪細線）
        lay.addWidget(WinCtrlBtn(self, WinCtrlBtn.KIND_MIN, self.window_ref.showMinimized))
        lay.addWidget(WinCtrlBtn(self, WinCtrlBtn.KIND_MAX, self._toggle_max))
        lay.addWidget(WinCtrlBtn(self, WinCtrlBtn.KIND_CLOSE, self.window_ref.close))

    def _toggle_max(self):
        if self.window_ref.isMaximized():
            self.window_ref.showNormal()
        else:
            self.window_ref.showMaximized()

    def _icon_btn(self, glyph):
        b = QPushButton(glyph)
        b.setFixedSize(36, 36)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(
            f"QPushButton {{ background: {T.BG_SURFACE}; color: {T.TEXT_DIM};"
            f" border: 1px solid {T.BORDER};"
            f" border-radius: {T.R_SM}px; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {T.BG_HOVER};"
            f" color: {T.TEXT_HI}; border-color: {T.BORDER_HOVER}; }}"
        )
        return b

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
