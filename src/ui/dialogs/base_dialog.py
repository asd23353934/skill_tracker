"""
基礎對話框 — PySide6 版本
QDialog 基礎類別 — RPG 金色邊框風格
"""

import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFrame, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.ui.theme import AppTheme
from src.ui.helpers import resource_path


class BaseDialog(QDialog):
    """基礎對話框 — RPG 金色邊框"""

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

        # ===== RPG 金色邊框效果 =====
        # 外層 QDialog 背景為金色，3px padding 產生金色邊框效果
        self.setStyleSheet(
            f"QDialog {{ background-color: {AppTheme.GOLD_DARK}; }}"
        )

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(3, 3, 3, 3)
        outer_layout.setSpacing(0)

        self.inner = QFrame()
        self.inner.setObjectName("dialog_inner")
        self.inner.setStyleSheet(
            f"QFrame#dialog_inner {{"
            f" background-color: {AppTheme.BG_DEEP};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_MD}px; }}"
        )
        outer_layout.addWidget(self.inner)

    def close(self):
        """關閉對話框"""
        self.reject()
