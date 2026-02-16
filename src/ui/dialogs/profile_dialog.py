"""
配置管理對話框
RPG 金色邊框風格
"""

import customtkinter as ctk
from tkinter import messagebox
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class ProfileManagerDialog(BaseDialog):
    """配置管理對話框"""

    def __init__(self, parent, config_manager, current_settings, main_app):
        super().__init__(parent, "配置管理", 600, 520)
        self.config_manager = config_manager
        self.current_settings = current_settings
        self.main_app = main_app
        self.current_profile = self.config_manager.get_current_profile()
        self.selected_index = None

        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        container = self.inner

        # 標題
        title_frame = ctk.CTkFrame(container, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            title_frame,
            text="⚔ 配置管理",
            font=AppTheme.FONT_TITLE_MD,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(side="left")

        # 當前配置
        current_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        current_frame.pack(side="right")

        ctk.CTkLabel(
            current_frame,
            text="當前:",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 4))

        self.current_label = ctk.CTkLabel(
            current_frame,
            text=self.current_profile,
            font=AppTheme.FONT_BODY_MD_BOLD,
            text_color=AppTheme.GOLD_LIGHT,
        )
        self.current_label.pack(side="left")

        # 配置列表（使用可滾動框架 + 可選取行）
        list_container = ctk.CTkFrame(
            container,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.BG_CARD,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        list_container.pack(fill="both", expand=True, padx=20, pady=8)

        self.list_frame = ctk.CTkScrollableFrame(
            list_container,
            fg_color=AppTheme.BG_CARD,
            corner_radius=0,
            scrollbar_button_color=AppTheme.BG_TERTIARY,
            scrollbar_button_hover_color=AppTheme.GOLD_PRIMARY,
        )
        self.list_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.profile_rows = []
        self._refresh_list()

        # 按鈕組
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=8)

        buttons = [
            ("➕ 新增", AppTheme.ACCENT_GREEN, "#0d9668", self._create_new_profile),
            ("📋 複製", AppTheme.ACCENT_BLUE, "#2563eb", self._copy_profile),
            ("✏ 重命名", AppTheme.GOLD_PRIMARY, AppTheme.GOLD_DARK, self._rename_profile),
            ("🔄 切換", AppTheme.ACCENT_PURPLE, "#7c3aed", self._switch_profile),
            ("🗑 刪除", AppTheme.ACCENT_RED, "#dc2626", self._delete_profile),
        ]

        for text, color, hover, cmd in buttons:
            ctk.CTkButton(
                btn_frame,
                text=text,
                command=cmd,
                width=95,
                height=32,
                corner_radius=AppTheme.CORNER_MD,
                fg_color=color,
                hover_color=hover,
                font=AppTheme.FONT_BTN_SM,
                border_width=1,
                border_color=AppTheme.GOLD_MUTED,
            ).pack(side="left", padx=3)

        # 提示
        ctk.CTkLabel(
            container,
            text="💡 雙擊配置名稱可快速切換 | 所有修改會自動保存到當前配置",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(pady=(0, 12))

    def _refresh_list(self):
        """刷新配置列表"""
        for row in self.profile_rows:
            row.destroy()
        self.profile_rows = []
        self.selected_index = None

        profiles = self.config_manager.list_profiles()
        for i, profile in enumerate(profiles):
            is_current = profile == self.current_profile
            row = self._create_row(profile, i, is_current)
            self.profile_rows.append(row)

    def _create_row(self, profile_name, index, is_current):
        """建立配置行"""
        row = ctk.CTkFrame(
            self.list_frame,
            fg_color=AppTheme.BG_CARD_ACTIVE if is_current else "transparent",
            corner_radius=4,
            height=36,
        )
        row.pack(fill="x", padx=4, pady=1)
        row.pack_propagate(False)

        display = f"★ {profile_name}" if is_current else f"    {profile_name}"
        label = ctk.CTkLabel(
            row,
            text=display,
            font=AppTheme.FONT_BODY_LG_BOLD if is_current else AppTheme.FONT_BODY_LG,
            text_color=AppTheme.GOLD_LIGHT if is_current else AppTheme.TEXT_PRIMARY,
            anchor="w",
        )
        label.pack(side="left", padx=12, fill="y")

        # 綁定點擊和雙擊
        for widget in (row, label):
            widget.bind("<Button-1>", lambda e, idx=index: self._select_row(idx))
            widget.bind("<Double-Button-1>", lambda e: self._switch_profile())

        row._profile_name = profile_name
        row._index = index
        return row

    def _select_row(self, index):
        """選取配置行"""
        # 取消先前的選取
        for row in self.profile_rows:
            is_current = row._profile_name == self.current_profile
            row.configure(
                fg_color=AppTheme.BG_CARD_ACTIVE if is_current else "transparent"
            )

        # 高亮選取行
        if index < len(self.profile_rows):
            self.profile_rows[index].configure(fg_color=AppTheme.BG_CARD_HOVER)
            self.selected_index = index

    def _get_selected_name(self):
        """取得選取的配置名稱"""
        if self.selected_index is None or self.selected_index >= len(self.profile_rows):
            return None
        return self.profile_rows[self.selected_index]._profile_name

    def _create_new_profile(self):
        """新增配置"""
        dialog = ctk.CTkInputDialog(
            text="輸入新配置名稱:", title="新增配置"
        )
        name = dialog.get_input()

        if name and name.strip():
            name = name.strip()
            if name in self.config_manager.list_profiles():
                messagebox.showerror("錯誤", f"配置 '{name}' 已存在!", parent=self)
                return

            all_skills = self.main_app.skill_manager.get_all_skills().keys()
            initial_settings = {
                "hotkeys": {},
                "permanent": {sid: False for sid in all_skills},
                "loop": {sid: False for sid in all_skills},
                "alert_enabled": {sid: False for sid in all_skills},
                "cooldown_overrides": {},
            }
            if self.config_manager.save_profile(name, initial_settings):
                self._refresh_list()

    def _copy_profile(self):
        """複製配置"""
        source = self._get_selected_name()
        if not source:
            messagebox.showwarning("提示", "請先選擇要複製的配置!", parent=self)
            return

        dialog = ctk.CTkInputDialog(
            text=f"輸入新配置名稱:\n(將複製自 '{source}')", title="複製配置"
        )
        new_name = dialog.get_input()

        if new_name and new_name.strip():
            new_name = new_name.strip()
            if new_name in self.config_manager.list_profiles():
                messagebox.showerror("錯誤", f"配置 '{new_name}' 已存在!", parent=self)
                return

            source_data = self.config_manager.load_profile(source)
            if source_data and self.config_manager.save_profile(new_name, source_data):
                self._refresh_list()

    def _rename_profile(self):
        """重命名配置"""
        old_name = self._get_selected_name()
        if not old_name:
            messagebox.showwarning("提示", "請先選擇要重命名的配置!", parent=self)
            return

        dialog = ctk.CTkInputDialog(
            text=f"輸入新名稱:\n(當前: '{old_name}')", title="重命名配置"
        )
        new_name = dialog.get_input()

        if new_name and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            if new_name in self.config_manager.list_profiles():
                messagebox.showerror("錯誤", f"配置 '{new_name}' 已存在!", parent=self)
                return

            if self.config_manager.rename_profile(old_name, new_name):
                if old_name == self.current_profile:
                    self.current_profile = new_name
                    self.config_manager.set_current_profile(new_name)
                    self.current_label.configure(text=new_name)
                    self.main_app.current_profile_name = new_name
                    self.main_app.header.update_profile_name(new_name)
                self._refresh_list()

    def _switch_profile(self):
        """切換配置"""
        name = self._get_selected_name()
        if not name:
            messagebox.showwarning("提示", "請先選擇要切換的配置!", parent=self)
            return

        if name == self.current_profile:
            messagebox.showinfo("提示", "已經是當前配置了!", parent=self)
            return

        profile_data = self.config_manager.load_profile(name)
        if profile_data:
            self.config_manager.set_current_profile(name)
            self.current_profile = name
            self.current_label.configure(text=name)

            self.result = profile_data
            self.close()

    def _delete_profile(self):
        """刪除配置"""
        name = self._get_selected_name()
        if not name:
            messagebox.showwarning("提示", "請先選擇要刪除的配置!", parent=self)
            return

        if name == self.current_profile:
            messagebox.showerror("錯誤", "無法刪除當前正在使用的配置!", parent=self)
            return

        if messagebox.askyesno("確認刪除", f"確定要刪除配置 '{name}' 嗎？", parent=self):
            if self.config_manager.delete_profile(name):
                self._refresh_list()
