"""
設定對話框
提供系統設定的 UI，包含位置、視窗大小、提前提示、音效選擇
RPG 金色邊框風格，音效使用下拉式選單 + 新增按鈕
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme


class SettingsDialog(BaseDialog):
    """設定對話框"""

    WINDOW_SIZE_OPTIONS = {
        "極小 (48px)": 48,
        "小 (64px) - 預設": 64,
        "中 (80px)": 80,
        "大 (96px)": 96,
        "極大 (128px)": 128,
    }

    NO_SOUND_LABEL = "無"

    def __init__(self, parent, current_settings):
        super().__init__(parent, "設定", 480, 780)
        self.current_settings = current_settings
        self.sound_manager = current_settings.get("sound_manager")

        # 音效選項映射 label → filename
        self._sound_label_map = {}
        self._build_sound_options()

        self._build_ui()

    def _build_sound_options(self):
        """建立音效下拉選項映射"""
        self._sound_label_map = {self.NO_SOUND_LABEL: ""}
        if self.sound_manager:
            for filename in self.sound_manager.list_sounds():
                label = self.sound_manager.get_sound_label(filename)
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
            text="⚙ 系統設定",
            font=AppTheme.FONT_TITLE_MD,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(pady=(16, 20))

        content = ctk.CTkScrollableFrame(
            container, fg_color="transparent", corner_radius=0
        )
        content.pack(fill="both", expand=True, padx=20)

        # ===== 位置設定 =====
        self._section_label(content, "📍 技能視窗起始位置")

        pos_frame = ctk.CTkFrame(content, fg_color="transparent")
        pos_frame.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(pos_frame, text="X:", font=AppTheme.FONT_BODY_LG,
                      text_color=AppTheme.TEXT_PRIMARY).pack(
            side="left", padx=(0, 4)
        )
        self.x_entry = ctk.CTkEntry(
            pos_frame, width=100, height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=("Arial", 11),
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            fg_color=AppTheme.BG_CARD,
        )
        self.x_entry.insert(0, str(self.current_settings.get("x", 960)))
        self.x_entry.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(pos_frame, text="Y:", font=AppTheme.FONT_BODY_LG,
                      text_color=AppTheme.TEXT_PRIMARY).pack(
            side="left", padx=(0, 4)
        )
        self.y_entry = ctk.CTkEntry(
            pos_frame, width=100, height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=("Arial", 11),
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            fg_color=AppTheme.BG_CARD,
        )
        self.y_entry.insert(0, str(self.current_settings.get("y", 540)))
        self.y_entry.pack(side="left")

        self._separator(content)

        # ===== 視窗大小 =====
        self._section_label(content, "📐 技能視窗大小")

        size_frame = ctk.CTkFrame(content, fg_color="transparent")
        size_frame.pack(fill="x", pady=(4, 4))

        ctk.CTkLabel(size_frame, text="大小:", font=AppTheme.FONT_BODY_LG,
                      text_color=AppTheme.TEXT_PRIMARY).pack(
            side="left", padx=(0, 8)
        )

        current_size = self.current_settings.get("window_size", 64)
        current_label = "小 (64px) - 預設"
        for label, size in self.WINDOW_SIZE_OPTIONS.items():
            if size == current_size:
                current_label = label
                break

        self.size_menu = ctk.CTkOptionMenu(
            size_frame,
            values=list(self.WINDOW_SIZE_OPTIONS.keys()),
            width=180,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=AppTheme.FONT_BODY_MD,
            fg_color=AppTheme.BG_CARD,
            button_color=AppTheme.GOLD_PRIMARY,
            button_hover_color=AppTheme.GOLD_LIGHT,
        )
        self.size_menu.set(current_label)
        self.size_menu.pack(side="left")

        ctk.CTkLabel(
            content,
            text="💡 推薦使用「小」或「中」大小",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 8))

        self._separator(content)

        # ===== 提前提示 =====
        self._section_label(content, "🔔 提前提示音設定")

        alert_frame = ctk.CTkFrame(content, fg_color="transparent")
        alert_frame.pack(fill="x", pady=(4, 4))

        ctk.CTkLabel(alert_frame, text="提前", font=AppTheme.FONT_BODY_LG,
                      text_color=AppTheme.TEXT_PRIMARY).pack(
            side="left", padx=(0, 4)
        )
        self.alert_entry = ctk.CTkEntry(
            alert_frame, width=80, height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=("Arial", 11),
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
            fg_color=AppTheme.BG_CARD,
        )
        self.alert_entry.insert(
            0, str(self.current_settings.get("alert_before_seconds", 0))
        )
        self.alert_entry.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(alert_frame, text="秒提示", font=AppTheme.FONT_BODY_LG,
                      text_color=AppTheme.TEXT_PRIMARY).pack(side="left")

        ctk.CTkLabel(
            content,
            text="💡 設為 0 表示結束時才提示",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 8))

        self._separator(content)

        # ===== 音效總開關 =====
        self._section_label(content, "🔊 音效設定")

        self.sound_var = ctk.BooleanVar(
            value=self.current_settings.get("sound", True)
        )
        ctk.CTkSwitch(
            content,
            text="啟用倒數完成音效提示",
            variable=self.sound_var,
            font=AppTheme.FONT_BODY_MD,
            progress_color=AppTheme.GOLD_PRIMARY,
            button_color=AppTheme.TEXT_PRIMARY,
            button_hover_color=AppTheme.GOLD_LIGHT,
        ).pack(anchor="w", pady=(4, 12))

        # ===== 全域完成音效（下拉式）=====
        self._section_label(content, "🎵 全域完成音效")

        sound_row = ctk.CTkFrame(content, fg_color="transparent")
        sound_row.pack(fill="x", pady=(4, 4))

        current_global_sound = self.current_settings.get("global_sound", "")
        self.global_sound_menu = ctk.CTkOptionMenu(
            sound_row,
            values=list(self._sound_label_map.keys()),
            width=240,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=AppTheme.FONT_BODY_MD,
            fg_color=AppTheme.BG_CARD,
            button_color=AppTheme.GOLD_PRIMARY,
            button_hover_color=AppTheme.GOLD_LIGHT,
        )
        self.global_sound_menu.set(
            self._get_label_for_filename(current_global_sound)
        )
        self.global_sound_menu.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            sound_row,
            text="▶ 試聽",
            command=lambda: self._preview_sound(self.global_sound_menu),
            width=60,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left")

        self._separator(content)

        # ===== 全域提前提示音效（下拉式）=====
        self._section_label(content, "🎵 全域提前提示音效")

        alert_sound_row = ctk.CTkFrame(content, fg_color="transparent")
        alert_sound_row.pack(fill="x", pady=(4, 4))

        current_global_alert_sound = self.current_settings.get("global_alert_sound", "")
        self.global_alert_sound_menu = ctk.CTkOptionMenu(
            alert_sound_row,
            values=list(self._sound_label_map.keys()),
            width=240,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            font=AppTheme.FONT_BODY_MD,
            fg_color=AppTheme.BG_CARD,
            button_color=AppTheme.GOLD_PRIMARY,
            button_hover_color=AppTheme.GOLD_LIGHT,
        )
        self.global_alert_sound_menu.set(
            self._get_label_for_filename(current_global_alert_sound)
        )
        self.global_alert_sound_menu.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            alert_sound_row,
            text="▶ 試聽",
            command=lambda: self._preview_sound(self.global_alert_sound_menu),
            width=60,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left")

        self._separator(content)

        # ===== 新增音效 =====
        self._section_label(content, "📂 新增自訂音效")

        ctk.CTkButton(
            content,
            text="＋ 匯入音效檔案 (.wav / .mp3)",
            command=self._import_sound,
            width=280,
            height=36,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_MD,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        ).pack(anchor="w", pady=(4, 4))

        ctk.CTkLabel(
            content,
            text="💡 匯入後可在上方下拉選單中選擇",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 8))

        self._separator(content)

        # 提示
        hints = ctk.CTkFrame(content, fg_color="transparent")
        hints.pack(fill="x", pady=(8, 4))

        for text in [
            "💡 視窗尺寸會自動適應技能圖片大小",
            "💡 提示視窗可在畫面上拖曳調整位置",
        ]:
            ctk.CTkLabel(
                hints, text=text,
                font=AppTheme.FONT_BODY_SM,
                text_color=AppTheme.TEXT_MUTED,
            ).pack(anchor="w", pady=1)

        # 儲存按鈕
        ctk.CTkButton(
            container,
            text="✓ 儲存設定",
            command=self._save,
            width=160,
            height=42,
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
    def _preview_sound(self, menu):
        """試聽指定下拉選單目前選擇的音效"""
        label = menu.get()
        filename = self._sound_label_map.get(label, "")
        if filename and self.sound_manager:
            self.sound_manager.play(filename)

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

        if not self.sound_manager:
            return

        new_name = self.sound_manager.import_sound(filepath)
        if new_name:
            # 重新建立選項映射
            self._build_sound_options()
            new_values = list(self._sound_label_map.keys())

            # 更新兩個下拉選單
            self.global_sound_menu.configure(values=new_values)
            self.global_alert_sound_menu.configure(values=new_values)

            # 自動選擇新匯入的音效
            new_label = self.sound_manager.get_sound_label(new_name)
            self.global_sound_menu.set(new_label)

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
            x_val = int(self.x_entry.get())
            y_val = int(self.y_entry.get())
            alert_before = int(self.alert_entry.get())

            selected_label = self.size_menu.get()
            window_size = self.WINDOW_SIZE_OPTIONS.get(selected_label, 64)

            if x_val < 0 or y_val < 0:
                messagebox.showerror("錯誤", "座標值不能為負數！", parent=self)
                return

            if alert_before < 0:
                messagebox.showerror("錯誤", "提前秒數不能為負數！", parent=self)
                return

            # 從下拉選單取得檔名
            global_sound_label = self.global_sound_menu.get()
            global_sound = self._sound_label_map.get(global_sound_label, "")

            alert_sound_label = self.global_alert_sound_menu.get()
            global_alert_sound = self._sound_label_map.get(alert_sound_label, "")

            self.result = {
                "x": x_val,
                "y": y_val,
                "sound": self.sound_var.get(),
                "alert_before_seconds": alert_before,
                "window_size": window_size,
                "global_sound": global_sound,
                "global_alert_sound": global_alert_sound,
            }
            self.close()

        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的數字！", parent=self)
