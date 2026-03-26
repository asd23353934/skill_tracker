"""
頻道廣播免責聲明對話框
首次啟動時顯示，告知使用者功能特性與風險
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
)
from PySide6.QtCore import Qt

from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class BroadcastDisclaimerDialog(BaseDialog):
    """免責聲明對話框"""

    def __init__(self, parent):
        super().__init__(parent, "免責聲明", width=460, height=340)
        self.accepted = False
        self._build_content()

    def _build_content(self):
        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 標題
        title = QLabel("⚠️ 頻道廣播功能 — 免責聲明")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {AppTheme.ACCENT_YELLOW};"
            f" font-size: 15px;"
            f" font-weight: bold;"
            f" font-family: {AppTheme.FONT_FAMILY};"
        )
        layout.addWidget(title)

        # 說明內容
        disclaimer_text = (
            "本功能透過<b>被動封包監聽</b>擷取遊戲頻道廣播訊息，"
            "<b>不會修改任何遊戲資料或封包</b>。\n\n"
            "使用前請注意：\n\n"
            "• 需要安裝 <b>Npcap</b> 驅動程式\n"
            "• 需要以<b>管理員身分</b>執行程式\n"
            "• 僅監聽本機網路流量，不涉及第三方伺服器\n"
            "• 使用此功能的<b>風險由使用者自行承擔</b>\n"
            "• 開發者不對任何因使用此功能造成的後果負責"
        )

        content = QLabel(disclaimer_text)
        content.setWordWrap(True)
        content.setTextFormat(Qt.TextFormat.RichText)
        content.setStyleSheet(
            f"color: {AppTheme.TEXT_PRIMARY};"
            f" font-size: 12px;"
            f" font-family: {AppTheme.FONT_FAMILY};"
            f" line-height: 1.5;"
        )
        layout.addWidget(content)

        layout.addStretch()

        # 按鈕列
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        decline_btn = QPushButton("取消")
        decline_btn.setFixedSize(100, 32)
        decline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        decline_btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_SECONDARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px;"
            f" font-family: {AppTheme.FONT_FAMILY}; }}"
            f"QPushButton:hover {{"
            f" background-color: {AppTheme.BG_CARD_HOVER}; }}"
        )
        decline_btn.clicked.connect(self.reject)
        btn_row.addWidget(decline_btn)

        accept_btn = QPushButton("我已了解，啟動")
        accept_btn.setFixedSize(140, 32)
        accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        accept_btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {AppTheme.ACCENT_GREEN};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" border: none;"
            f" border-radius: 4px;"
            f" font-weight: bold;"
            f" font-family: {AppTheme.FONT_FAMILY}; }}"
            f"QPushButton:hover {{"
            f" background-color: {AppTheme.ACCENT_GREEN_HOVER}; }}"
        )
        accept_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(accept_btn)

        layout.addLayout(btn_row)

    def _on_accept(self):
        self.accepted = True
        self.accept()
