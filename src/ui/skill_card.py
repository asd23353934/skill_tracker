"""
RPG 風格技能卡片元件
三欄佈局：左(圖示+名稱) | 中(兩行控件) | 右(設定按鈕)
"""

import customtkinter as ctk
from src.ui.theme import AppTheme


class SkillCard(ctk.CTkFrame):
    """RPG 風格技能卡片 — 三欄佈局"""

    def __init__(self, parent, skill_id, skill, app):
        super().__init__(
            parent,
            corner_radius=4,
            fg_color=AppTheme.BG_CARD,
            border_width=1,
            border_color=AppTheme.BORDER_GOLD_SUBTLE,
            height=56,
        )
        self.pack_propagate(False)

        self.skill_id = skill_id
        self.skill = skill
        self.app = app

        self._build_ui()

        # Hover 效果
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _build_ui(self):
        """建構卡片 UI — 左中右三欄"""

        # ===== 左欄：圖示 + 名稱 =====
        icon_frame = ctk.CTkFrame(
            self,
            fg_color=AppTheme.BG_DEEP,
            corner_radius=4,
            width=40,
            height=40,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        icon_frame.pack(side="left", padx=(4, 0), pady=4)
        icon_frame.pack_propagate(False)

        ctk_img = self.app.skill_manager.ctk_images_card.get(self.skill_id)
        if ctk_img:
            ctk.CTkLabel(icon_frame, image=ctk_img, text="").place(
                relx=0.5, rely=0.5, anchor="center"
            )

        # 狀態圓點
        self._build_status_dots(icon_frame)

        # 名稱（固定寬度，靠左對齊）
        ctk.CTkLabel(
            self,
            text=self.skill["name"],
            font=AppTheme.FONT_CARD_NAME,
            text_color=AppTheme.TEXT_GOLD,
            anchor="w",
            width=58,
        ).pack(side="left", padx=(5, 0))

        # ===== 右欄：設定按鈕 (固定寬度) =====
        right = ctk.CTkFrame(self, fg_color="transparent", width=28)
        right.pack(side="right", fill="y", padx=(0, 2), pady=4)
        right.pack_propagate(False)

        ctk.CTkButton(
            right,
            text="⋮",
            command=lambda: self.app.show_skill_detail(self.skill_id),
            width=22,
            height=40,
            corner_radius=3,
            fg_color="transparent",
            hover_color=AppTheme.BG_TERTIARY,
            text_color=AppTheme.TEXT_MUTED,
            font=(AppTheme.FONT_FAMILY, 14),
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ===== 中欄：兩行控件（垂直置中）=====
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)

        # 用 place 把內容容器垂直置中
        inner = ctk.CTkFrame(center, fg_color="transparent")
        inner.place(relx=0, rely=0.5, anchor="w")

        # --- 第一行：冷卻秒數 ↺ | 快捷鍵 ↺ ---
        mid_row1 = ctk.CTkFrame(inner, fg_color="transparent")
        mid_row1.pack(anchor="w", pady=(0, 1))

        original_cooldown = self.app.get_original_cooldown(self.skill_id)
        is_modified = (
            original_cooldown and self.skill["cooldown"] != original_cooldown
        )

        self.cooldown_btn = ctk.CTkButton(
            mid_row1,
            text=f"{self.skill['cooldown']}秒",
            command=lambda: self.app.edit_cooldown(self.skill_id),
            width=50,
            height=18,
            corner_radius=3,
            fg_color=(
                AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY
            ),
            hover_color=(
                "#2563eb" if is_modified else AppTheme.BG_SECONDARY
            ),
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_CARD_BADGE,
        )
        self.cooldown_btn.pack(side="left", padx=(0, 1))
        self.app.cooldown_buttons[self.skill_id] = self.cooldown_btn

        ctk.CTkButton(
            mid_row1,
            text="↺",
            command=lambda: self.app.reset_cooldown(self.skill_id),
            width=16,
            height=18,
            corner_radius=3,
            fg_color="transparent",
            hover_color=AppTheme.ACCENT_RED,
            text_color=AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_CARD_BADGE,
        ).pack(side="left", padx=(0, 6))

        # 快捷鍵
        hotkey_text = self.skill.get("hotkey", "") or "未設定"
        has_hotkey = bool(self.skill.get("hotkey"))

        self.hotkey_btn = ctk.CTkButton(
            mid_row1,
            text=hotkey_text,
            command=lambda: self.app.hotkey_manager.begin_capture(
                self.skill_id, self.skill["name"]
            ),
            width=54,
            height=18,
            corner_radius=3,
            fg_color=(
                AppTheme.ACCENT_YELLOW if has_hotkey else AppTheme.BG_TERTIARY
            ),
            hover_color=(
                "#e5a800" if has_hotkey else AppTheme.BG_SECONDARY
            ),
            text_color=(
                "#000000" if has_hotkey else AppTheme.TEXT_MUTED
            ),
            font=AppTheme.FONT_CARD_BADGE,
        )
        self.hotkey_btn.pack(side="left", padx=(0, 1))
        self.app.hotkey_buttons[self.skill_id] = self.hotkey_btn

        ctk.CTkButton(
            mid_row1,
            text="↺",
            command=lambda: self.app.reset_hotkey(self.skill_id),
            width=16,
            height=18,
            corner_radius=3,
            fg_color="transparent",
            hover_color=AppTheme.ACCENT_RED,
            text_color=AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_CARD_BADGE,
        ).pack(side="left")

        # --- 第二行：常駐 | 循環 | 提醒 | 秒數 ---
        mid_row2 = ctk.CTkFrame(inner, fg_color="transparent")
        mid_row2.pack(anchor="w", pady=(1, 0))

        # 常駐
        self.permanent_var = ctk.BooleanVar(
            value=self.app.skill_permanent.get(self.skill_id, False)
        )
        self.app.permanent_vars[self.skill_id] = self.permanent_var

        ctk.CTkCheckBox(
            mid_row2,
            text="常駐",
            variable=self.permanent_var,
            command=lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "permanent", self.permanent_var
            ),
            width=46,
            height=16,
            checkbox_width=12,
            checkbox_height=12,
            corner_radius=2,
            fg_color=AppTheme.ACCENT_YELLOW,
            hover_color="#e5a800",
            text_color=AppTheme.TEXT_SECONDARY,
            font=AppTheme.FONT_CARD_BADGE,
        ).pack(side="left", padx=(0, 2))

        # 循環
        self.loop_var = ctk.BooleanVar(
            value=self.app.skill_loop.get(self.skill_id, False)
        )
        self.app.loop_vars[self.skill_id] = self.loop_var

        ctk.CTkCheckBox(
            mid_row2,
            text="循環",
            variable=self.loop_var,
            command=lambda: self.app.update_skill_setting_exclusive(
                self.skill_id, "loop", self.loop_var
            ),
            width=46,
            height=16,
            checkbox_width=12,
            checkbox_height=12,
            corner_radius=2,
            fg_color=AppTheme.ACCENT_GREEN,
            hover_color="#0d9668",
            text_color=AppTheme.TEXT_SECONDARY,
            font=AppTheme.FONT_CARD_BADGE,
        ).pack(side="left", padx=(0, 2))

        # 提醒
        self.alert_var = ctk.BooleanVar(
            value=self.app.skill_alert_enabled.get(self.skill_id, False)
        )
        self.app.alert_enabled_vars[self.skill_id] = self.alert_var

        ctk.CTkCheckBox(
            mid_row2,
            text="提醒",
            variable=self.alert_var,
            command=lambda: self.app.update_alert_setting(
                self.skill_id, self.alert_var
            ),
            width=46,
            height=16,
            checkbox_width=12,
            checkbox_height=12,
            corner_radius=2,
            fg_color=AppTheme.ACCENT_ORANGE,
            hover_color="#e07a2a",
            text_color=AppTheme.TEXT_SECONDARY,
            font=AppTheme.FONT_CARD_BADGE,
        ).pack(side="left", padx=(0, 3))

        # 提前提示秒數
        alert_seconds = self.app.skill_alert_seconds_overrides.get(
            self.skill_id, None
        )
        if alert_seconds is not None:
            alert_text = f"{alert_seconds}s"
            alert_fg = AppTheme.ACCENT_ORANGE
            alert_hover = "#e07a2a"
        else:
            global_val = self.app.alert_before_seconds
            alert_text = f"{global_val}s"
            alert_fg = AppTheme.BG_TERTIARY
            alert_hover = AppTheme.BG_SECONDARY

        self.alert_seconds_btn = ctk.CTkButton(
            mid_row2,
            text=alert_text,
            command=lambda: self.app.edit_alert_seconds(self.skill_id),
            width=28,
            height=16,
            corner_radius=3,
            fg_color=alert_fg,
            hover_color=alert_hover,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_CARD_BADGE,
        )
        self.alert_seconds_btn.pack(side="left")
        self.app.alert_seconds_buttons[self.skill_id] = self.alert_seconds_btn

    def _build_status_dots(self, icon_frame):
        """在圖示右上角放置狀態圓點"""
        dot_frame = ctk.CTkFrame(icon_frame, fg_color="transparent")
        dot_frame.place(relx=1.0, rely=0.0, anchor="ne", x=-1, y=1)

        is_permanent = self.app.skill_permanent.get(self.skill_id, False)
        is_loop = self.app.skill_loop.get(self.skill_id, False)
        is_alert = self.app.skill_alert_enabled.get(self.skill_id, False)

        dots = [
            (is_permanent, AppTheme.STATUS_PERMANENT, AppTheme.STATUS_PERMANENT_DIM),
            (is_loop, AppTheme.STATUS_LOOP, AppTheme.STATUS_LOOP_DIM),
            (is_alert, AppTheme.STATUS_ALERT, AppTheme.STATUS_ALERT_DIM),
        ]

        for active, color_on, color_off in dots:
            ctk.CTkFrame(
                dot_frame,
                width=5,
                height=5,
                corner_radius=3,
                fg_color=color_on if active else color_off,
            ).pack(side="left", padx=0)

    # --------------------------------------------------
    # 互動事件
    # --------------------------------------------------
    def _on_enter(self, event):
        """滑鼠進入 — 金色邊框"""
        self.configure(border_color=AppTheme.GOLD_PRIMARY)

    def _on_leave(self, event):
        """滑鼠離開 — 恢復柔和邊框"""
        self.configure(border_color=AppTheme.BORDER_GOLD_SUBTLE)
