"""
技能倒數頁面 — PySide6 版本
三欄技能卡片列表：玩家技能 | BOSS 技能 | 道具
RPG Banner 色調區分各欄
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout
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
        layout = QHBoxLayout(self)
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
                self, title, category, self.app,
                border_color=border_color,
            )
            layout.addWidget(col, 1)   # stretch=1 確保三欄等寬填滿頁面
