"""
技能項目元件
單一技能的 UI 行：圖示、名稱、冷卻、快捷鍵、勾選框
"""

import customtkinter as ctk
from src.ui.theme import AppTheme


class SkillItem(ctk.CTkFrame):
    """單一技能項目"""

    def __init__(self, parent, skill_id, skill, app):
        super().__init__(
            parent,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_PRIMARY,
            border_width=1,
            border_color=AppTheme.BG_TERTIARY,
        )
        self.pack(fill="x", padx=8, pady=2)

        self.skill_id = skill_id
        self.skill = skill
        self.app = app

        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        # 左側：圖示 + 資訊
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=4)

        # 技能圖示
        ctk_img = self.app.skill_manager.ctk_images_small.get(self.skill_id)
        if ctk_img:
            ctk.CTkLabel(left, image=ctk_img, text="").pack(side="left", padx=(0, 8))

        # 資訊欄
        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        # 技能名稱
        ctk.CTkLabel(
            info,
            text=self.skill["name"],
            font=AppTheme.FONT_BODY_MD_BOLD,
            text_color=AppTheme.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        # 按鈕列（冷卻 + 快捷鍵）
        btns = ctk.CTkFrame(info, fg_color="transparent")
        btns.pack(anchor="w", pady=(2, 0))

        # 冷卻時間按鈕
        original_cooldown = self.app.get_original_cooldown(self.skill_id)
        is_modified = original_cooldown and self.skill["cooldown"] != original_cooldown

        self.cooldown_btn = ctk.CTkButton(
            btns,
            text=f"{self.skill['cooldown']}秒",
            command=lambda: self.app.edit_cooldown(self.skill_id),
            width=70,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
            hover_color=AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_SECONDARY,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM_BOLD,
        )
        self.cooldown_btn.pack(side="left", padx=(0, 2))
        self.app.cooldown_buttons[self.skill_id] = self.cooldown_btn

        # 重置冷卻按鈕
        ctk.CTkButton(
            btns,
            text="↺",
            command=lambda: self.app.reset_cooldown(self.skill_id),
            width=26,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.BG_SECONDARY,
            text_color=AppTheme.TEXT_SECONDARY,
            font=("Arial", 13, "bold"),
        ).pack(side="left", padx=(0, 6))

        # 快捷鍵按鈕
        hotkey_text = self.skill.get("hotkey", "") or "未設定"
        has_hotkey = bool(self.skill.get("hotkey"))

        self.hotkey_btn = ctk.CTkButton(
            btns,
            text=hotkey_text,
            command=lambda: self.app.hotkey_manager.begin_capture(
                self.skill_id, self.skill["name"]
            ),
            width=70,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_YELLOW if has_hotkey else AppTheme.BG_TERTIARY,
            hover_color="#e5a800" if has_hotkey else AppTheme.BG_SECONDARY,
            text_color="#000000" if has_hotkey else AppTheme.TEXT_SECONDARY,
            font=AppTheme.FONT_BODY_SM_BOLD,
        )
        self.hotkey_btn.pack(side="left", padx=(0, 2))
        self.app.hotkey_buttons[self.skill_id] = self.hotkey_btn

        # 重置快捷鍵按鈕
        ctk.CTkButton(
            btns,
            text="↺",
            command=lambda: self.app.reset_hotkey(self.skill_id),
            width=26,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.BG_SECONDARY,
            text_color=AppTheme.TEXT_SECONDARY,
            font=("Arial", 13, "bold"),
        ).pack(side="left")

        # 右側：勾選框
        options = ctk.CTkFrame(self, fg_color="transparent")
        options.pack(side="right", padx=(4, 8), pady=4)

        self._create_checkboxes(options)

    def _create_checkboxes(self, parent):
        """建立技能選項勾選框"""
        # 常駐
        self.permanent_var = ctk.BooleanVar(
            value=self.app.skill_permanent.get(self.skill_id, False)
        )
        self.app.permanent_vars[self.skill_id] = self.permanent_var

        ctk.CTkCheckBox(
            parent,
            text="常駐",
            variable=self.permanent_var,
            command=lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "permanent", self.permanent_var
            ),
            width=65,
            height=24,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_YELLOW,
            hover_color="#e5a800",
            text_color=AppTheme.ACCENT_YELLOW,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left", padx=2)

        # 循環
        self.loop_var = ctk.BooleanVar(
            value=self.app.skill_loop.get(self.skill_id, False)
        )
        self.app.loop_vars[self.skill_id] = self.loop_var

        ctk.CTkCheckBox(
            parent,
            text="循環",
            variable=self.loop_var,
            command=lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "loop", self.loop_var
            ),
            width=65,
            height=24,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_GREEN,
            hover_color="#0d9668",
            text_color=AppTheme.ACCENT_GREEN,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left", padx=2)

        # 提前提示
        self.alert_var = ctk.BooleanVar(
            value=self.app.skill_alert_enabled.get(self.skill_id, False)
        )
        self.app.alert_enabled_vars[self.skill_id] = self.alert_var

        ctk.CTkCheckBox(
            parent,
            text="提前提示",
            variable=self.alert_var,
            command=lambda: self.app.update_alert_setting(
                self.skill_id, self.alert_var
            ),
            width=85,
            height=24,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_ORANGE,
            hover_color="#e07a2a",
            text_color=AppTheme.ACCENT_ORANGE,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left", padx=2)

        # 提前提示秒數按鈕
        alert_seconds = self.app.skill_alert_seconds_overrides.get(self.skill_id, None)
        alert_text = f"{alert_seconds}s" if alert_seconds is not None else "全域"

        self.alert_seconds_btn = ctk.CTkButton(
            parent,
            text=alert_text,
            command=lambda: self.app.edit_alert_seconds(self.skill_id),
            width=45,
            height=24,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_ORANGE if alert_seconds is not None else AppTheme.BG_TERTIARY,
            hover_color="#e07a2a" if alert_seconds is not None else AppTheme.BG_SECONDARY,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM_BOLD,
        )
        self.alert_seconds_btn.pack(side="left", padx=2)
        self.app.alert_seconds_buttons[self.skill_id] = self.alert_seconds_btn
