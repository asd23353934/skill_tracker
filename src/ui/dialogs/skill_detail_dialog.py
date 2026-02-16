"""
技能細部設定對話框
提供提前秒數、完成音效 / 提前提示音效選擇（下拉式）、自動套用設定等選項
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class SkillDetailDialog(BaseDialog):
    """技能細部設定對話框"""

    NO_SOUND_LABEL = "使用全域設定"

    def __init__(self, parent, skill_id, app):
        self.skill_id = skill_id
        self.app = app
        self.skill = app.skill_manager.get_skill(skill_id)
        skill_name = self.skill["name"] if self.skill else skill_id

        # 音效選項映射
        self._sound_label_map = {}
        self._build_sound_options()

        super().__init__(parent, f"細部設定 — {skill_name}", 440, 620)
        self._build_ui()

    def _build_sound_options(self):
        """建立音效下拉選項映射"""
        self._sound_label_map = {self.NO_SOUND_LABEL: ""}
        if self.app.sound_manager:
            for filename in self.app.sound_manager.list_sounds():
                label = self.app.sound_manager.get_sound_label(filename)
                self._sound_label_map[label] = filename

    def _get_label_for_filename(self, filename):
        """根據檔名取得對應的下拉選項標籤"""
        if not filename:
            return self.NO_SOUND_LABEL
        for label, fname in self._sound_label_map.items():
            if fname == filename:
                return label
        return self.NO_SOUND_LABEL

    def _build_ui(self):
        """建構 UI"""
        container = self.inner

        # 標題
        ctk.CTkLabel(
            container,
            text=f"⚙ {self.skill['name']}",
            font=AppTheme.FONT_TITLE_MD,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(pady=(16, 16))

        content = ctk.CTkScrollableFrame(
            container, fg_color="transparent", corner_radius=0
        )
        content.pack(fill="both", expand=True, padx=20)

        # ===== 提前提示秒數 =====
        self._section_label(content, "🔔 提前提示秒數")

        alert_frame = ctk.CTkFrame(content, fg_color="transparent")
        alert_frame.pack(fill="x", pady=(4, 4))

        current_override = self.app.skill_alert_seconds_overrides.get(
            self.skill_id, None
        )
        current_val = (
            current_override if current_override is not None
            else self.app.alert_before_seconds
        )

        ctk.CTkLabel(
            alert_frame, text="提前", font=AppTheme.FONT_BODY_LG,
            text_color=AppTheme.TEXT_PRIMARY,
        ).pack(side="left", padx=(0, 4))

        self.alert_entry = ctk.CTkEntry(
            alert_frame, width=80, height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=("Arial", 11),
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            fg_color=AppTheme.BG_CARD,
        )
        self.alert_entry.insert(0, str(current_val))
        self.alert_entry.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            alert_frame, text="秒提示", font=AppTheme.FONT_BODY_LG,
            text_color=AppTheme.TEXT_PRIMARY,
        ).pack(side="left")

        # 使用全域設定 checkbox
        self.use_global_alert = ctk.BooleanVar(
            value=(current_override is None)
        )
        ctk.CTkCheckBox(
            content,
            text=f"使用全域設定（目前: {self.app.alert_before_seconds}秒）",
            variable=self.use_global_alert,
            command=self._on_toggle_global_alert,
            width=300,
            height=24,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            fg_color=AppTheme.GOLD_PRIMARY,
            hover_color=AppTheme.GOLD_LIGHT,
            text_color=AppTheme.TEXT_SECONDARY,
            font=AppTheme.FONT_BODY_SM,
        ).pack(anchor="w", pady=(2, 8))

        self._separator(content)

        # ===== 完成音效選擇 =====
        self._section_label(content, "🎵 完成音效")

        sound_row = ctk.CTkFrame(content, fg_color="transparent")
        sound_row.pack(fill="x", pady=(4, 4))

        current_sound = self.app.skill_sound_overrides.get(self.skill_id, "")
        self.sound_menu = ctk.CTkOptionMenu(
            sound_row,
            values=list(self._sound_label_map.keys()),
            width=220,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=AppTheme.FONT_BODY_MD,
            fg_color=AppTheme.BG_CARD,
            button_color=AppTheme.GOLD_PRIMARY,
            button_hover_color=AppTheme.GOLD_LIGHT,
        )
        self.sound_menu.set(self._get_label_for_filename(current_sound))
        self.sound_menu.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            sound_row,
            text="▶",
            command=self._preview_completion_sound,
            width=36,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left")

        self._separator(content)

        # ===== 提前提示音效選擇 =====
        self._section_label(content, "🔔 提前提示音效")

        alert_sound_row = ctk.CTkFrame(content, fg_color="transparent")
        alert_sound_row.pack(fill="x", pady=(4, 4))

        current_alert_sound = self.app.skill_alert_sound_overrides.get(
            self.skill_id, ""
        )
        self.alert_sound_menu = ctk.CTkOptionMenu(
            alert_sound_row,
            values=list(self._sound_label_map.keys()),
            width=220,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=AppTheme.FONT_BODY_MD,
            fg_color=AppTheme.BG_CARD,
            button_color=AppTheme.GOLD_PRIMARY,
            button_hover_color=AppTheme.GOLD_LIGHT,
        )
        self.alert_sound_menu.set(
            self._get_label_for_filename(current_alert_sound)
        )
        self.alert_sound_menu.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            alert_sound_row,
            text="▶",
            command=self._preview_alert_sound,
            width=36,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left")

        # 匯入音效按鈕
        ctk.CTkButton(
            content,
            text="＋ 匯入音效檔案",
            command=self._import_sound,
            width=160,
            height=30,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        ).pack(anchor="w", pady=(4, 8))

        self._separator(content)

        # ===== 自動設定 =====
        self._section_label(content, "⚡ 自動設定")

        ctk.CTkLabel(
            content,
            text="未手動設定時自動套用的參數：",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(4, 4))

        auto_frame = ctk.CTkFrame(content, fg_color="transparent")
        auto_frame.pack(fill="x", pady=(0, 4))

        # 自動常駐
        self.auto_permanent = ctk.BooleanVar(
            value=self.app.skill_permanent.get(self.skill_id, False)
        )
        ctk.CTkCheckBox(
            auto_frame,
            text="常駐",
            variable=self.auto_permanent,
            width=80,
            height=24,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_YELLOW,
            hover_color="#e5a800",
            text_color=AppTheme.ACCENT_YELLOW,
            font=AppTheme.FONT_BODY_MD,
        ).pack(side="left", padx=(0, 12))

        # 自動循環
        self.auto_loop = ctk.BooleanVar(
            value=self.app.skill_loop.get(self.skill_id, False)
        )
        ctk.CTkCheckBox(
            auto_frame,
            text="循環",
            variable=self.auto_loop,
            width=80,
            height=24,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_GREEN,
            hover_color="#0d9668",
            text_color=AppTheme.ACCENT_GREEN,
            font=AppTheme.FONT_BODY_MD,
        ).pack(side="left", padx=(0, 12))

        # 自動提示
        self.auto_alert = ctk.BooleanVar(
            value=self.app.skill_alert_enabled.get(self.skill_id, False)
        )
        ctk.CTkCheckBox(
            auto_frame,
            text="提前提示",
            variable=self.auto_alert,
            width=100,
            height=24,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_ORANGE,
            hover_color="#e07a2a",
            text_color=AppTheme.ACCENT_ORANGE,
            font=AppTheme.FONT_BODY_MD,
        ).pack(side="left")

        self._separator(content)

        # 儲存按鈕
        ctk.CTkButton(
            container,
            text="✓ 儲存",
            command=self._save,
            width=140,
            height=40,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.GOLD_PRIMARY,
            hover_color=AppTheme.GOLD_LIGHT,
            text_color=AppTheme.BG_DEEP,
            font=AppTheme.FONT_BTN,
            border_width=1,
            border_color=AppTheme.GOLD_DARK,
        ).pack(pady=(8, 16))

    # --------------------------------------------------
    # 音效功能
    # --------------------------------------------------
    def _get_effective_filename(self, menu, global_fallback):
        """取得選單實際對應的檔名（含全域 fallback）

        Args:
            menu: CTkOptionMenu 元件
            global_fallback: 全域設定的檔名

        Returns:
            實際要播放的檔名
        """
        label = menu.get()
        filename = self._sound_label_map.get(label, "")
        if not filename:
            # 「使用全域設定」→ 取全域值
            return global_fallback
        return filename

    def _preview_completion_sound(self):
        """試聽完成音效（含全域 fallback）"""
        filename = self._get_effective_filename(
            self.sound_menu, self.app.global_sound
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _preview_alert_sound(self):
        """試聽提前提示音效（含全域 fallback）"""
        filename = self._get_effective_filename(
            self.alert_sound_menu, self.app.global_alert_sound
        )
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def _import_sound(self):
        """開啟檔案選擇器匯入音效"""
        filepath = filedialog.askopenfilename(
            title="選擇音效檔案",
            filetypes=[
                ("音效檔案", "*.wav *.mp3"),
                ("WAV 檔案", "*.wav"),
                ("MP3 檔案", "*.mp3"),
            ],
            parent=self,
        )

        if not filepath:
            return

        if not self.app.sound_manager:
            return

        new_name = self.app.sound_manager.import_sound(filepath)
        if new_name:
            self._build_sound_options()
            new_values = list(self._sound_label_map.keys())
            self.sound_menu.configure(values=new_values)
            self.alert_sound_menu.configure(values=new_values)

            new_label = self.app.sound_manager.get_sound_label(new_name)
            self.sound_menu.set(new_label)

            messagebox.showinfo(
                "匯入成功",
                f"已成功匯入音效: {new_name}",
                parent=self,
            )
        else:
            messagebox.showerror(
                "匯入失敗",
                "無法匯入音效檔案，請確認檔案格式為 .wav 或 .mp3",
                parent=self,
            )

    def _on_toggle_global_alert(self):
        """切換全域提示設定時更新 entry 狀態"""
        if self.use_global_alert.get():
            self.alert_entry.delete(0, "end")
            self.alert_entry.insert(0, str(self.app.alert_before_seconds))

    # --------------------------------------------------
    # UI 工具
    # --------------------------------------------------
    def _section_label(self, parent, text):
        """建立區段標題"""
        ctk.CTkLabel(
            parent,
            text=text,
            font=AppTheme.FONT_BODY_LG_BOLD,
            text_color=AppTheme.GOLD_PRIMARY,
            anchor="w",
        ).pack(anchor="w", pady=(8, 2))

    def _separator(self, parent):
        """建立分隔線"""
        ctk.CTkFrame(parent, fg_color=AppTheme.GOLD_MUTED, height=1).pack(
            fill="x", pady=8
        )

    def _save(self):
        """儲存設定"""
        try:
            # 提前秒數
            if self.use_global_alert.get():
                self.app.skill_alert_seconds_overrides.pop(self.skill_id, None)
            else:
                alert_val = int(self.alert_entry.get())
                if alert_val < 0:
                    alert_val = 0
                self.app.skill_alert_seconds_overrides[self.skill_id] = alert_val

            # 更新提前秒數按鈕
            btn = self.app.alert_seconds_buttons.get(self.skill_id)
            if btn:
                actual_val = self.app.get_alert_seconds(self.skill_id)
                is_override = self.skill_id in self.app.skill_alert_seconds_overrides
                btn.configure(
                    text=f"{actual_val}s",
                    fg_color=(
                        AppTheme.ACCENT_ORANGE if is_override
                        else AppTheme.BG_TERTIARY
                    ),
                )

            # 完成音效（從下拉選單取得）
            sound_label = self.sound_menu.get()
            sound = self._sound_label_map.get(sound_label, "")
            if sound:
                self.app.skill_sound_overrides[self.skill_id] = sound
            else:
                self.app.skill_sound_overrides.pop(self.skill_id, None)

            # 提前提示音效（從下拉選單取得）
            alert_sound_label = self.alert_sound_menu.get()
            alert_sound = self._sound_label_map.get(alert_sound_label, "")
            if alert_sound:
                self.app.skill_alert_sound_overrides[self.skill_id] = alert_sound
            else:
                self.app.skill_alert_sound_overrides.pop(self.skill_id, None)

            # 自動設定（常駐/循環/提示）
            new_permanent = self.auto_permanent.get()
            new_loop = self.auto_loop.get()
            new_alert = self.auto_alert.get()

            # 互斥處理：常駐和循環不能同時啟用
            if new_permanent and new_loop:
                new_loop = False

            # 更新狀態
            old_permanent = self.app.skill_permanent.get(self.skill_id, False)
            old_loop = self.app.skill_loop.get(self.skill_id, False)

            self.app.skill_permanent[self.skill_id] = new_permanent
            self.app.skill_loop[self.skill_id] = new_loop
            self.app.skill_alert_enabled[self.skill_id] = new_alert

            # 更新 UI vars
            if self.skill_id in self.app.permanent_vars:
                self.app.permanent_vars[self.skill_id].set(new_permanent)
            if self.skill_id in self.app.loop_vars:
                self.app.loop_vars[self.skill_id].set(new_loop)
            if self.skill_id in self.app.alert_enabled_vars:
                self.app.alert_enabled_vars[self.skill_id].set(new_alert)

            # 處理視窗變更
            if new_permanent and not old_permanent:
                if self.skill_id not in self.app.window_manager.active_windows:
                    self.app.window_manager.create_permanent_window(self.skill_id)
            elif not new_permanent and old_permanent:
                if self.skill_id in self.app.window_manager.active_windows:
                    self.app.window_manager.active_windows[self.skill_id].close()

            if not new_loop and old_loop:
                if self.skill_id in self.app.window_manager.active_windows:
                    self.app.window_manager.active_windows[self.skill_id].close()

            # 更新活躍視窗
            if self.skill_id in self.app.window_manager.active_windows:
                win = self.app.window_manager.active_windows[self.skill_id]
                win.alert_enabled = new_alert
                win.alert_before_seconds = self.app.get_alert_seconds(self.skill_id)

            self.app.auto_save_current_profile()

            self.result = True
            self.close()

        except ValueError:
            pass
