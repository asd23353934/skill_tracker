"""
技能倒數頁面
Header + 三欄技能卡片列表，RPG Banner 色調區分
"""

import customtkinter as ctk
from src.ui.theme import AppTheme
from src.ui.header import Header
from src.ui.skill_column import SkillColumn


class SkillPage(ctk.CTkFrame):
    """技能倒數頁面"""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        """建構技能倒數頁面 UI"""
        # 標題列
        self.app.header = Header(self, self.app)
        self.app.header.pack(fill="x", padx=10, pady=(10, 5))

        # 主內容區 - 三欄佈局
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # 設定三欄等寬
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.columnconfigure(2, weight=1)
        main_container.rowconfigure(0, weight=1)

        # 玩家技能（藍色調 Banner）
        self.app.player_col = SkillColumn(
            main_container, "玩家技能", "player", self.app,
            banner_color=AppTheme.BANNER_PLAYER,
            border_color=AppTheme.BANNER_BORDER_PLAYER,
        )
        self.app.player_col.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # BOSS 技能（紅色調 Banner）
        self.app.boss_col = SkillColumn(
            main_container, "BOSS 技能", "boss", self.app,
            banner_color=AppTheme.BANNER_BOSS,
            border_color=AppTheme.BANNER_BORDER_BOSS,
        )
        self.app.boss_col.grid(row=0, column=1, sticky="nsew", padx=4)

        # 道具（綠色調 Banner）
        self.app.items_col = SkillColumn(
            main_container, "道具", "item", self.app,
            banner_color=AppTheme.BANNER_ITEM,
            border_color=AppTheme.BANNER_BORDER_ITEM,
        )
        self.app.items_col.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
