"""
頻道廣播黑名單管理對話框
檢視與移除已封鎖的玩家
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame,
)
from PySide6.QtCore import Qt

from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class BroadcastBlacklistDialog(BaseDialog):
    """黑名單管理對話框"""

    def __init__(self, parent, broadcast_page):
        """初始化

        Args:
            parent: 父元件（App）
            broadcast_page: BroadcastPage 實例
        """
        super().__init__(parent, "黑名單管理", width=400, height=360)
        self.broadcast_page = broadcast_page
        self._rows = []
        self._build_content()

    def _build_content(self):
        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 標題
        title = QLabel("🚫 已封鎖的玩家")
        title.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT};"
            f" font-size: 14px;"
            f" font-weight: bold;"
            f" font-family: {AppTheme.FONT_FAMILY};"
        )
        layout.addWidget(title)

        # 列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: transparent; border: none; }}"
            f"QScrollBar:vertical {{"
            f" background: {AppTheme.BG_DEEP};"
            f" width: 6px; border-radius: 3px; }}"
            f"QScrollBar::handle:vertical {{"
            f" background: {AppTheme.GOLD_MUTED};"
            f" border-radius: 3px; min-height: 20px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{"
            f" height: 0px; }}"
        )

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)

        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll)

        self._refresh_list()

        # 關閉按鈕
        close_btn = QPushButton("關閉")
        close_btn.setFixedHeight(30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px;"
            f" font-family: {AppTheme.FONT_FAMILY}; }}"
            f"QPushButton:hover {{"
            f" background-color: {AppTheme.BG_CARD_HOVER}; }}"
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _refresh_list(self):
        """重新載入黑名單列表"""
        # 清除舊的
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        blacklist = self.broadcast_page.app.broadcast_manager.get_blacklist()

        if not blacklist:
            empty = QLabel("黑名單是空的")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color: {AppTheme.TEXT_MUTED};"
                f" font-size: 12px;"
                f" font-family: {AppTheme.FONT_FAMILY};"
                f" padding: 20px;"
            )
            self._list_layout.addWidget(empty)
            self._rows.append(empty)
            return

        for tag in blacklist:
            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{"
                f" background: {AppTheme.BG_CARD};"
                f" border: 1px solid {AppTheme.BORDER_GOLD_SUBTLE};"
                f" border-radius: 4px; }}"
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 6, 10, 6)
            row_layout.setSpacing(8)

            label = QLabel(tag)
            label.setStyleSheet(
                f"color: {AppTheme.TEXT_PRIMARY};"
                f" font-size: 12px;"
                f" font-family: {AppTheme.FONT_FAMILY};"
                f" background: transparent;"
            )
            row_layout.addWidget(label)
            row_layout.addStretch()

            remove_btn = QPushButton("移除")
            remove_btn.setFixedSize(50, 24)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet(
                f"QPushButton {{"
                f" background-color: {AppTheme.ACCENT_RED};"
                f" color: {AppTheme.TEXT_PRIMARY};"
                f" border: none;"
                f" border-radius: 3px;"
                f" font-size: 11px;"
                f" font-family: {AppTheme.FONT_FAMILY}; }}"
                f"QPushButton:hover {{"
                f" background-color: {AppTheme.ACCENT_RED_HOVER}; }}"
            )
            remove_btn.clicked.connect(lambda checked=False, t=tag: self._remove(t))
            row_layout.addWidget(remove_btn)

            self._list_layout.addWidget(row)
            self._rows.append(row)

    def _remove(self, friend_tag: str):
        """移除黑名單項目"""
        self.broadcast_page.app.broadcast_manager.remove_from_blacklist(friend_tag)
        self._refresh_list()
