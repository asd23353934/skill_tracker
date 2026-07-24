"""
V2 側邊欄 — 主要頁面導覽（唯一導覽方式）
頂部 logo｜中段頁面 icon｜底部設定/退出
唯一的右側分隔線（其他元件無邊線）
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, QSize, Signal
from PySide6.QtGui import QPixmap
from src.infrastructure.helpers import resource_path
from src.ui_v2.theme_v2 import V2Theme as T
from src.ui_v2.lucide import lucide_icon
from src.ui_v2.page_registry import PAGE_REGISTRY


class _ClickableLabel(QLabel):
    """可點擊的 QLabel（QLabel 預設不發 clicked 訊號）"""
    clicked = Signal()

    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


class AppLogo(QLabel):
    """app icon (icon.png) 縮放至 size×size 顯示。"""
    def __init__(self, parent=None, size=36):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setStyleSheet("background: transparent; border: none;")
        pix = QPixmap(resource_path("icon.png"))
        if not pix.isNull():
            self.setPixmap(pix.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


# 向後相容別名（外部如有 import 仍可運作）
TriangleLogo = AppLogo


class SidebarV2(QWidget):
    """主要頁面導覽側邊欄（導覽項目讀自 page_registry.PAGE_REGISTRY）"""

    def __init__(self, parent, on_change, on_settings_click=None, on_changelog_click=None):
        super().__init__(parent)
        self.on_change = on_change
        self._on_settings_click = on_settings_click
        self._on_changelog_click = on_changelog_click
        self.current   = "skill"
        self._items    = {}
        self._build()

    def _build(self):
        self.setObjectName("sidebar_v2")
        self.setFixedWidth(T.SIDEBAR_W)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"QWidget#sidebar_v2 {{ background: transparent;"
            f" border-right: 1px solid {T.BORDER}; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 16, 0, 16)
        lay.setSpacing(4)

        # ── 頂部 logo ──
        logo_wrap = QFrame()
        lw = QVBoxLayout(logo_wrap)
        lw.setContentsMargins(0, 0, 0, 0)
        lw.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lw.addWidget(AppLogo(self, 36))
        lay.addWidget(logo_wrap)

        # ── 頁面 icons（上下置中）──
        lay.addStretch()
        for spec in PAGE_REGISTRY:
            btn = self._make_btn(spec.icon, spec.tooltip)
            btn.clicked.connect(lambda _=False, k=spec.key: self._select(k))
            self._items[spec.key] = btn
            lay.addWidget(btn)
        lay.addStretch()

        # ── 底部設定（小巧、低調）──
        settings = QPushButton()
        settings.setIcon(lucide_icon("settings", T.TEXT_MUTED, 18, stroke=1.6))
        settings.setIconSize(QSize(18, 18))
        settings.setFixedSize(36, 36)
        settings.setCursor(Qt.CursorShape.PointingHandCursor)
        settings.setToolTip("設定")
        settings.setStyleSheet(
            f"QPushButton {{ background: transparent;"
            f" border: none; border-radius: {T.R_MD}px; padding: 0; }}"
            f"QPushButton:hover {{ background: {T.BG_SURFACE}; }}"
        )
        settings.clicked.connect(
            lambda: self._on_settings_click() if self._on_settings_click else None
        )
        settings_wrap = QFrame()
        sw = QHBoxLayout(settings_wrap)
        sw.setContentsMargins(0, 0, 0, 0)
        sw.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sw.addWidget(settings)
        lay.addWidget(settings_wrap)

        # ── 版本號（最底、小號淡色）──
        try:
            from version import get_version
            ver_text = f"v{get_version()}"
        except Exception:
            ver_text = ""
        if ver_text:
            ver_lbl = _ClickableLabel(ver_text)
            ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ver_lbl.setStyleSheet(
                f"color: {T.TEXT_MUTED}; background: transparent;"
                f" font-size: 9px; font-weight: 500;"
            )
            ver_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            ver_lbl.setToolTip("點擊查看更新日記")
            ver_lbl.clicked.connect(self._open_changelog)
            lay.addWidget(ver_lbl)
        lay.addSpacing(6)

        # 活動指示條（左側橘色 3px）
        self._indicator = QFrame(self)
        self._indicator.setObjectName("indicator")
        self._indicator.setStyleSheet(
            f"QFrame#indicator {{ background: {T.ORANGE}; border: none;"
            f" border-top-right-radius: 2px;"
            f" border-bottom-right-radius: 2px; }}"
        )
        self._indicator.setFixedWidth(3)
        self._anim = None

        self._apply_states()
        QTimer.singleShot(0, self._snap_indicator)

    def _open_changelog(self):
        if self._on_changelog_click:
            self._on_changelog_click()

    def _make_btn(self, icon_name, tip):
        b = QPushButton()
        b._icon_name = icon_name
        b.setFixedSize(T.SIDEBAR_W, 44)
        b.setIconSize(QSize(20, 20))
        b.setToolTip(tip)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(
            f"QPushButton {{ background: transparent;"
            f" border: none; padding: 0; }}"
        )
        return b

    def _apply_states(self):
        for k, b in self._items.items():
            color = T.ORANGE if k == self.current else T.TEXT_DIM
            b.setIcon(lucide_icon(b._icon_name, color, 20, stroke=1.6))

    def _select(self, key):
        if key == self.current:
            return
        self.current = key
        self._apply_states()
        self._animate_indicator()
        self.on_change(key)

    def _target_rect(self) -> QRect | None:
        btn = self._items.get(self.current)
        if btn is None:
            return None
        inset = 10
        return QRect(0, btn.y() + inset, 3, btn.height() - inset * 2)

    def _snap_indicator(self):
        r = self._target_rect()
        if r:
            self._indicator.setGeometry(r)
            self._indicator.raise_()

    def _animate_indicator(self):
        target = self._target_rect()
        if target is None:
            return
        self._indicator.raise_()
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        self._anim = QPropertyAnimation(self._indicator, b"geometry", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(self._indicator.geometry())
        self._anim.setEndValue(target)
        self._anim.start()

    def resizeEvent(self, e):  # noqa: N802
        super().resizeEvent(e)
        self._snap_indicator()
