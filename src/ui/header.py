"""
標題列元件
RPG 風格雙重金色邊框橫幅，包含標題、配置名稱、操作按鈕
"""

import customtkinter as ctk
from src.ui.theme import AppTheme


class Header(ctk.CTkFrame):
    """RPG 風格標題列 — 雙重金色邊框"""

    def __init__(self, parent, app):
        # 外層金色邊框
        super().__init__(
            parent,
            corner_radius=AppTheme.CORNER_LG,
            fg_color=AppTheme.GOLD_PRIMARY,
            height=AppTheme.HEADER_HEIGHT,
        )
        self.pack_propagate(False)
        self.app = app

        # 內層內容框（深色背景 + 暗金邊框）
        self.inner = ctk.CTkFrame(
            self,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.BG_CARD,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        self.inner.pack(fill="both", expand=True, padx=2, pady=2)
        self.inner.pack_propagate(False)

        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        # ===== 左側：裝飾標題 + 配置 =====
        left = ctk.CTkFrame(self.inner, fg_color="transparent")
        left.pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            left,
            text="🍁 技能追蹤器 🍁",
            font=AppTheme.FONT_RPG_TITLE,
            text_color=AppTheme.GOLD_LIGHT,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            left,
            text="Artale 楓之谷",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(side="left", padx=(0, 12))

        # 配置徽章（遊戲成就風格）
        badge = ctk.CTkFrame(
            left,
            corner_radius=6,
            fg_color=AppTheme.BG_DARKEST,
            border_width=1,
            border_color=AppTheme.GOLD_DARK,
        )
        badge.pack(side="left", padx=4)

        ctk.CTkLabel(
            badge,
            text="📋",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.GOLD_PRIMARY,
        ).pack(side="left", padx=(8, 2), pady=4)

        self.profile_label = ctk.CTkLabel(
            badge,
            text=self.app.current_profile_name,
            font=AppTheme.FONT_BODY_MD_BOLD,
            text_color=AppTheme.GOLD_PRIMARY,
        )
        self.profile_label.pack(side="left", padx=(0, 8), pady=4)

        # ===== 右側：按鈕組 =====
        right = ctk.CTkFrame(self.inner, fg_color="transparent")
        right.pack(side="right", padx=16, pady=10)

        # 快捷鍵提示標籤
        self.hotkey_hint = ctk.CTkLabel(
            right,
            text="",
            font=AppTheme.FONT_BODY_LG_BOLD,
            text_color=AppTheme.ACCENT_GREEN,
        )
        self.hotkey_hint.pack(side="left", padx=(0, 12))

        # 更新按鈕（初始隱藏）
        self.update_btn = ctk.CTkButton(
            right,
            text="⬆ 有新版本",
            command=self.app.show_update_dialog,
            width=110,
            height=34,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.ACCENT_GREEN,
            hover_color="#0d9668",
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            font=AppTheme.FONT_BTN_SM,
        )
        # 不 pack，等有更新時顯示

        # 清空按鍵
        ctk.CTkButton(
            right,
            text="清空按鍵",
            command=self.app.clear_all_hotkeys,
            width=100,
            height=34,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.ACCENT_RED,
            hover_color="#dc2626",
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="left", padx=3)

        # 配置管理
        ctk.CTkButton(
            right,
            text="💾 配置管理",
            command=self.app.show_profile_manager,
            width=110,
            height=34,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.ACCENT_PURPLE,
            hover_color="#7c3aed",
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="left", padx=3)

        # 全選按鈕組（金色細邊框容器）
        toggle_group = ctk.CTkFrame(
            right,
            fg_color=AppTheme.BG_DEEP,
            corner_radius=6,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        toggle_group.pack(side="left", padx=6)

        ctk.CTkLabel(
            toggle_group,
            text="全選:",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(side="left", padx=(8, 4), pady=4)

        ctk.CTkButton(
            toggle_group,
            text="常駐",
            command=lambda: self.app.toggle_all("permanent"),
            width=55,
            height=28,
            corner_radius=4,
            fg_color=AppTheme.ACCENT_YELLOW,
            hover_color="#e5a800",
            text_color="#000000",
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="left", padx=2, pady=4)

        ctk.CTkButton(
            toggle_group,
            text="循環",
            command=lambda: self.app.toggle_all("loop"),
            width=55,
            height=28,
            corner_radius=4,
            fg_color=AppTheme.ACCENT_GREEN,
            hover_color="#0d9668",
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="left", padx=2, pady=4)

        ctk.CTkButton(
            toggle_group,
            text="提前提示",
            command=lambda: self.app.toggle_all("alert"),
            width=75,
            height=28,
            corner_radius=4,
            fg_color=AppTheme.ACCENT_ORANGE,
            hover_color="#e07a2a",
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="left", padx=(2, 6), pady=4)

        # 設定
        ctk.CTkButton(
            right,
            text="⚙ 設定",
            command=self.app.show_settings,
            width=90,
            height=34,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.BG_DEEP,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="left", padx=3)

    # ==================== 公開方法 ====================

    def show_update_button(self):
        """顯示更新按鈕"""
        self.update_btn.pack(side="left", padx=3)

    def update_profile_name(self, name):
        """更新配置名稱"""
        self.profile_label.configure(text=name)

    def show_hotkey_hint(self, text, color):
        """顯示快捷鍵提示"""
        self.hotkey_hint.configure(text=text, text_color=color)

    def clear_hotkey_hint(self):
        """清除快捷鍵提示"""
        self.hotkey_hint.configure(text="")
