"""
技能欄位元件
RPG 風格 Banner 標題 + 卡片垂直排列
"""

import customtkinter as ctk
from src.ui.theme import AppTheme
from src.ui.skill_card import SkillCard


class SkillColumn(ctk.CTkFrame):
    """RPG 風格技能欄位 — 卡片垂直排列"""

    def __init__(self, parent, title, category, app,
                 banner_color=None, border_color=None):
        """初始化技能欄位

        Args:
            parent: 父元件
            title: 欄位標題
            category: 技能分類 ('player', 'boss', 'item')
            app: App 實例
            banner_color: 橫幅背景色 (RPG 色調)
            border_color: 橫幅邊框色
        """
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.category = category
        self.skill_items = {}

        # 預設色彩
        if banner_color is None:
            banner_color = AppTheme.BG_SECONDARY
        if border_color is None:
            border_color = AppTheme.GOLD_MUTED

        # ===== 欄位標題 (RPG Banner) =====
        title_frame = ctk.CTkFrame(
            self,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=banner_color,
            border_width=1,
            border_color=border_color,
        )
        title_frame.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            title_frame,
            text=f"— {title} —",
            font=AppTheme.FONT_TITLE_SM,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(padx=10, pady=4)

        # ===== 可滾動內容 =====
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=AppTheme.BG_DEEP,
            corner_radius=AppTheme.CORNER_MD,
            scrollbar_button_color=AppTheme.BG_TERTIARY,
            scrollbar_button_hover_color=AppTheme.GOLD_PRIMARY,
        )
        self.scroll_frame.pack(fill="both", expand=True)

        self._populate(category)

    def _populate(self, category):
        """填充技能分組"""
        categories = self.app.skill_manager.get_categories(category)
        if not categories:
            return

        for subcategory, skill_ids in sorted(categories.items()):
            self._create_group(subcategory, skill_ids)

    def _create_group(self, subcategory, skill_ids):
        """建立技能分組 — RPG 分隔 + 卡片垂直排列

        Args:
            subcategory: 子分類名稱
            skill_ids: 技能 ID 列表
        """
        # 分組標題（RPG 分隔線風格）
        header = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=AppTheme.BG_DEEP,
            corner_radius=3,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        header.pack(fill="x", pady=(4, 2), padx=3)

        ctk.CTkLabel(
            header,
            text=f"  {subcategory}  ",
            font=AppTheme.FONT_BODY_SM_BOLD,
            text_color=AppTheme.GOLD_PRIMARY,
        ).pack(padx=6, pady=2)

        # 卡片垂直排列容器
        for skill_id in skill_ids:
            skill = self.app.skill_manager.get_skill(skill_id)
            if skill:
                card = SkillCard(self.scroll_frame, skill_id, skill, self.app)
                card.pack(fill="x", padx=3, pady=1)
                self.skill_items[skill_id] = card
