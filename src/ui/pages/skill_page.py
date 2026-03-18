"""
技能倒數頁面 — PySide6 版本
三欄技能卡片列表：玩家技能 | BOSS 技能 | 道具
RPG Banner 色調區分各欄
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
)
from src.ui.theme import AppTheme
from src.ui.skill_column import SkillColumn


class SkillPage(QWidget):
    """技能倒數頁面 — 三欄技能卡片列表"""

    def __init__(self, parent, app):
        """初始化技能頁

        Args:
            parent: 父元件
            app:    App 主應用實例
        """
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        """建構三欄技能頁面 UI"""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 頁首列 ──
        bar = QFrame()
        bar.setObjectName("skill_page_bar")
        bar.setStyleSheet(
            f"QFrame#skill_page_bar {{"
            f" background: {AppTheme.BG_SECONDARY};"
            f" border-bottom: 1px solid {AppTheme.GOLD_MUTED}; }}"
        )
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(12, 6, 12, 6)
        bar_lay.setSpacing(8)

        title_lbl = QLabel("🍁 技能倒數")
        title_lbl.setStyleSheet(
            f"color: {AppTheme.GOLD_LIGHT}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        bar_lay.addWidget(title_lbl)
        bar_lay.addStretch()

        # 全選按鈕組
        tg_frame = QFrame()
        tg_frame.setObjectName("skill_toggle_group")
        tg_frame.setStyleSheet(
            f"QFrame#skill_toggle_group {{"
            f" background: {AppTheme.BG_TERTIARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px; }}"
        )
        tg_lay = QHBoxLayout(tg_frame)
        tg_lay.setContentsMargins(6, 0, 6, 0)
        tg_lay.setSpacing(2)

        tg_lbl = QLabel("全選")
        tg_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_MUTED}; font-size: 10px;"
            f" background: transparent; border: none;"
        )
        tg_lay.addWidget(tg_lbl)

        toggle_defs = [
            ("常駐",    "permanent", AppTheme.ACCENT_YELLOW, "#e5a800", "#000000"),
            ("循環",    "loop",      AppTheme.ACCENT_GREEN,  "#0d9668", "#ffffff"),
            ("提前提示", "alert",    AppTheme.ACCENT_ORANGE, "#e07a2a", "#ffffff"),
        ]
        for text, key, color, hover, fg in toggle_defs:
            tb = QPushButton(text)
            tb.setFixedHeight(20)
            tb.clicked.connect(
                lambda checked=False, k=key: self.app.toggle_all(k)
            )
            tb.setStyleSheet(
                f"QPushButton {{ background: {color}; color: {fg};"
                f" border: none; border-radius: 3px;"
                f" padding: 0 6px; font-size: 10px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: {hover}; }}"
            )
            tg_lay.addWidget(tb)

        bar_lay.addWidget(tg_frame)
        root.addWidget(bar)

        # ── 三欄內容 ──
        columns_widget = QWidget()
        columns_widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(columns_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # banner_color 已棄用；只傳 border_color 作欄位底線強調色
        columns = [
            ("玩家技能", "player", AppTheme.BANNER_BORDER_PLAYER),  # 藍 #3b82f6
            ("BOSS 技能", "boss",  AppTheme.BANNER_BORDER_BOSS),    # 紅 #ef4444
            ("道具",     "item",  AppTheme.BANNER_BORDER_ITEM),     # 綠 #10b981
        ]

        for title, category, border_color in columns:
            col = SkillColumn(
                columns_widget, title, category, self.app,
                border_color=border_color,
            )
            layout.addWidget(col, 1)   # stretch=1 確保三欄等寬填滿頁面

        root.addWidget(columns_widget, 1)
