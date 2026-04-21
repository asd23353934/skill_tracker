"""
底部狀態列元件 — PyDracula 風格
顯示當前配置名稱（左）、版本號（右）、QSizeGrip 調整大小
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizeGrip
from PySide6.QtCore import Qt
from src.ui.theme import AppTheme


class StatusBar(QWidget):
    """底部狀態列 — 配置名稱 + 版本 + 縮放控制點"""

    HEIGHT = 26

    def __init__(self, parent, app):
        """初始化底部狀態列

        Args:
            parent: 父元件
            app:    App 主應用實例
        """
        super().__init__(parent)
        self.app = app
        self.setFixedHeight(self.HEIGHT)
        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        self.setObjectName("status_bar")
        self.setStyleSheet(
            f"QWidget#status_bar {{"
            f" background: {AppTheme.GRADIENT_STATUSBAR};"
            f" border-top: 1px solid {AppTheme.BORDER_GOLD_SUBTLE}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(8)

        # 配置徽章（左側）
        self.profile_lbl = QLabel(f"📋 {self.app.current_profile_name}")
        self.profile_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(self.profile_lbl)

        layout.addStretch()

        # 版本號（右側）
        try:
            from version import get_version
            ver_str = f"v{get_version()}"
        except Exception:
            ver_str = "v?"

        ver_lbl = QLabel(ver_str)
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ver_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 11px;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(ver_lbl)

        # QSizeGrip（右下角縮放控制點）
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        grip.setStyleSheet("background: transparent;")
        layout.addWidget(grip)

    # ==================== 公開方法 ====================

    def update_profile(self, name: str):
        """更新配置名稱顯示

        Args:
            name: 新配置名稱
        """
        self.profile_lbl.setText(f"📋 {name}")
