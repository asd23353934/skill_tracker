"""
基礎對話框 — PySide6 版本
QDialog 基礎類別
"""

import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFrame, QApplication
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QIcon
from src.ui.theme import AppTheme
from src.infrastructure.helpers import resource_path


class BaseDialog(QDialog):
    """基礎對話框"""

    def __init__(self, parent, title: str, width: int = 400, height: int = 300):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(width, height)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )

        # 設定視窗圖示
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        # 置中（相對螢幕）
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)

        self.result = None

        self.setStyleSheet(
            f"QDialog {{ background-color: {AppTheme.BG_DEEP}; }}"
        )

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.inner = QFrame()
        self.inner.setObjectName("dialog_inner")
        self.inner.setStyleSheet(
            f"QFrame#dialog_inner {{"
            f" background: {AppTheme.GRADIENT_CARD};"
            f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        outer_layout.addWidget(self.inner)

        self._fade_anim = None

    def showEvent(self, event):  # noqa: N802
        """顯示時播放淡入動畫"""
        super().showEvent(event)
        if self._fade_anim and self._fade_anim.state() == QPropertyAnimation.State.Running:
            self._fade_anim.stop()
        self.setWindowOpacity(0.0)
        self._fade_anim = AppTheme.make_anim(
            self, b"windowOpacity", 0.0, 1.0, duration=160)
        self._fade_anim.start()

    def close(self):
        """關閉對話框"""
        self.reject()
