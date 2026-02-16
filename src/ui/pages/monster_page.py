"""
怪物重生頁面
橫向滾動大卡牌，按鍵觸發浮動倒數視窗（從 0 數到設定時間）
卡片功能近似技能卡片：圖片、名稱、秒數、按鍵綁定、提前提示（可改秒數與聲音）
"""

import customtkinter as ctk
from tkinter import simpledialog
from PIL import Image
from src.ui.theme import AppTheme
from src.ui.helpers import resource_path


class MonsterCard(ctk.CTkFrame):
    """怪物重生大卡牌"""

    CARD_W = 280
    CARD_H = 400

    def __init__(self, parent, monster, app):
        super().__init__(
            parent,
            width=self.CARD_W,
            height=self.CARD_H,
            corner_radius=AppTheme.CORNER_MD,
            fg_color=AppTheme.BG_CARD,
            border_width=2,
            border_color=AppTheme.BORDER_GOLD_SUBTLE,
        )
        self.pack_propagate(False)
        self.monster = monster
        self.app = app
        self.monster_id = monster["id"]

        # 音效選項映射
        self._sound_label_map = {}
        self._build_sound_options()

        self._build_ui()

    def _build_sound_options(self):
        """建立音效下拉選項映射"""
        self._sound_label_map = {"全域設定": ""}
        if self.app.sound_manager:
            for filename in self.app.sound_manager.list_sounds():
                label = self.app.sound_manager.get_sound_label(filename)
                self._sound_label_map[label] = filename

    def _get_label_for_filename(self, filename):
        """根據檔名取得對應的下拉選項標籤"""
        if not filename:
            return "全域設定"
        for label, fname in self._sound_label_map.items():
            if fname == filename:
                return label
        return "全域設定"

    def _build_ui(self):
        """建構卡片 UI"""
        # === 圖示區域 ===
        icon_container = ctk.CTkFrame(
            self,
            fg_color=AppTheme.BG_DEEP,
            corner_radius=AppTheme.CORNER_SM,
            width=100,
            height=100,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        icon_container.pack(pady=(16, 8))
        icon_container.pack_propagate(False)

        # 載入圖片
        icon_file = self.monster.get("icon", "")
        if icon_file:
            try:
                img_path = resource_path(f"images/{icon_file}")
                img = Image.open(img_path)
                img_resized = img.resize((80, 80), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(
                    light_image=img_resized,
                    dark_image=img_resized,
                    size=(80, 80),
                )
                ctk.CTkLabel(icon_container, image=ctk_img, text="").place(
                    relx=0.5, rely=0.5, anchor="center"
                )
            except Exception:
                ctk.CTkLabel(
                    icon_container, text="👾",
                    font=(AppTheme.FONT_FAMILY, 36),
                    text_color=AppTheme.TEXT_MUTED,
                ).place(relx=0.5, rely=0.5, anchor="center")

        # === 名稱 ===
        ctk.CTkLabel(
            self,
            text=self.monster["name"],
            font=AppTheme.FONT_TITLE_MD,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(pady=(0, 4))

        # === 重生秒數顯示 ===
        respawn = self.monster.get("respawn_time", 0)
        ctk.CTkLabel(
            self,
            text=f"⏱ {respawn}秒",
            font=(AppTheme.FONT_FAMILY, 20, "bold"),
            text_color=AppTheme.TEXT_PRIMARY,
        ).pack(pady=(0, 6))

        # === 分隔線 ===
        ctk.CTkFrame(self, fg_color=AppTheme.GOLD_MUTED, height=1).pack(
            fill="x", padx=24, pady=4
        )

        # === 快捷鍵 ===
        hotkey_frame = ctk.CTkFrame(self, fg_color="transparent")
        hotkey_frame.pack(fill="x", padx=24, pady=(6, 3))

        ctk.CTkLabel(
            hotkey_frame,
            text="⌨ 快捷鍵",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_SECONDARY,
        ).pack(side="left")

        hotkey_text = self.monster.get("hotkey", "") or "未設定"
        has_hotkey = bool(self.monster.get("hotkey"))

        self.hotkey_btn = ctk.CTkButton(
            hotkey_frame,
            text=hotkey_text,
            command=self._begin_capture_hotkey,
            width=80,
            height=28,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=(
                AppTheme.ACCENT_YELLOW if has_hotkey else AppTheme.BG_TERTIARY
            ),
            hover_color=(
                "#e5a800" if has_hotkey else AppTheme.BG_SECONDARY
            ),
            text_color=(
                "#000000" if has_hotkey else AppTheme.TEXT_MUTED
            ),
            font=AppTheme.FONT_BODY_MD_BOLD,
        )
        self.hotkey_btn.pack(side="right")

        # === 提前提示秒數（可點擊修改）===
        alert_frame = ctk.CTkFrame(self, fg_color="transparent")
        alert_frame.pack(fill="x", padx=24, pady=(3, 3))

        ctk.CTkLabel(
            alert_frame,
            text="🔔 提前提示",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_SECONDARY,
        ).pack(side="left")

        alert_before = self.monster.get("alert_before", 10)
        self.alert_btn = ctk.CTkButton(
            alert_frame,
            text=f"{alert_before}s",
            command=self._edit_alert_seconds,
            width=60,
            height=28,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_ORANGE if alert_before > 0 else AppTheme.BG_TERTIARY,
            hover_color="#e07a2a" if alert_before > 0 else AppTheme.BG_SECONDARY,
            text_color="#ffffff" if alert_before > 0 else AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_BODY_MD_BOLD,
        )
        self.alert_btn.pack(side="right")

        # === 提示聲音（下拉）===
        sound_frame = ctk.CTkFrame(self, fg_color="transparent")
        sound_frame.pack(fill="x", padx=24, pady=(3, 3))

        ctk.CTkLabel(
            sound_frame,
            text="🔊 提示聲音",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_SECONDARY,
        ).pack(side="left")

        current_sound = self.monster.get("alert_sound", "")
        self.sound_menu = ctk.CTkOptionMenu(
            sound_frame,
            values=list(self._sound_label_map.keys()),
            command=self._on_sound_changed,
            width=120,
            height=28,
            corner_radius=AppTheme.CORNER_SM,
            font=AppTheme.FONT_BODY_SM,
            fg_color=AppTheme.BG_TERTIARY,
            button_color=AppTheme.GOLD_MUTED,
            button_hover_color=AppTheme.GOLD_PRIMARY,
            dropdown_font=AppTheme.FONT_BODY_SM,
        )
        self.sound_menu.set(self._get_label_for_filename(current_sound))
        self.sound_menu.pack(side="right")

        # === 試聽按鈕 ===
        preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        preview_frame.pack(fill="x", padx=24, pady=(2, 6))

        ctk.CTkButton(
            preview_frame,
            text="▶ 試聽",
            command=self._preview_sound,
            width=70,
            height=24,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="right")

        # Hover 效果
        self.bind("<Enter>", lambda e: self.configure(
            border_color=AppTheme.GOLD_PRIMARY
        ))
        self.bind("<Leave>", lambda e: self.configure(
            border_color=AppTheme.BORDER_GOLD_SUBTLE
        ))

    # --------------------------------------------------
    # 功能
    # --------------------------------------------------
    def _begin_capture_hotkey(self):
        """開始捕捉快捷鍵"""
        self.app.hotkey_manager.waiting_for = self.monster_id
        self.app.hotkey_manager.waiting_name = self.monster["name"]
        self.app.hotkey_manager.enabled = False
        self.app.hotkey_manager._monster_card = self
        self.app.header.show_hotkey_hint(
            f"⌨️ 請按下 '{self.monster['name']}' 的快捷鍵...",
            AppTheme.ACCENT_YELLOW,
        )

    def _edit_alert_seconds(self):
        """編輯提前提示秒數"""
        self.app.hotkey_manager.enabled = False
        current = self.monster.get("alert_before", 10)

        new_val = simpledialog.askinteger(
            "提前提示秒數",
            f"請輸入 '{self.monster['name']}' 提前幾秒提示:\n"
            f"(輸入 0 表示關閉提前提示)",
            initialvalue=current,
            minvalue=0,
            maxvalue=999,
            parent=self.app,
        )

        self.app.hotkey_manager.enabled = True

        if new_val is not None:
            self.monster["alert_before"] = new_val
            self.app.save_monsters()

            # 更新按鈕
            self.alert_btn.configure(
                text=f"{new_val}s",
                fg_color=AppTheme.ACCENT_ORANGE if new_val > 0 else AppTheme.BG_TERTIARY,
                hover_color="#e07a2a" if new_val > 0 else AppTheme.BG_SECONDARY,
                text_color="#ffffff" if new_val > 0 else AppTheme.TEXT_MUTED,
            )

    def _on_sound_changed(self, choice):
        """聲音下拉選單變更時儲存"""
        filename = self._sound_label_map.get(choice, "")
        self.monster["alert_sound"] = filename
        self.app.save_monsters()

    def _preview_sound(self):
        """試聽提示聲音"""
        label = self.sound_menu.get()
        filename = self._sound_label_map.get(label, "")
        if not filename:
            # 「全域設定」→ 取全域提前提示音
            filename = self.app.global_alert_sound
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def update_hotkey_display(self, key_str, has_hotkey):
        """更新快捷鍵顯示"""
        self.hotkey_btn.configure(
            text=key_str if has_hotkey else "未設定",
            fg_color=(
                AppTheme.ACCENT_YELLOW if has_hotkey else AppTheme.BG_TERTIARY
            ),
            hover_color=(
                "#e5a800" if has_hotkey else AppTheme.BG_SECONDARY
            ),
            text_color=(
                "#000000" if has_hotkey else AppTheme.TEXT_MUTED
            ),
        )


class MonsterPage(ctk.CTkFrame):
    """怪物重生頁面 — 填滿整個內容區域，橫向滾動，無滾動軸，卡牌水平垂直置中"""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.cards = {}

        self._build_ui()

    def _build_ui(self):
        """建構頁面 UI"""
        # 填滿整個頁面
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # === 標題區域（靠左上）===
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=(24, 0), pady=(20, 0))

        ctk.CTkLabel(
            title_frame,
            text="🍁 怪物重生",
            font=AppTheme.FONT_TITLE_LG,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="按下快捷鍵開始計時（從 0 數到設定時間）",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # === 卡牌容器（填滿剩餘空間）===
        card_area = ctk.CTkFrame(self, fg_color="transparent")
        card_area.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8, 16))
        card_area.rowconfigure(0, weight=1)
        card_area.columnconfigure(0, weight=1)

        # 使用 tkinter Canvas 實現無滾動軸的橫向滾動
        import tkinter as tk
        self._canvas = tk.Canvas(
            card_area,
            bg="#0a0e1a",
            highlightthickness=0,
            bd=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # 卡牌內部容器
        self._inner_frame = ctk.CTkFrame(self._canvas, fg_color="transparent")
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner_frame, anchor="nw"
        )

        # 綁定事件
        self._inner_frame.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # 綁定滾輪事件
        self._bind_mousewheel(self._canvas)
        self._bind_mousewheel(self._inner_frame)
        self._bind_mousewheel(self)
        self._bind_mousewheel(card_area)

        self._load_monsters()

    def _bind_mousewheel(self, widget):
        """綁定滾輪事件到指定元件及其子元件"""
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Enter>", lambda e: self._bind_children_mousewheel(widget), add="+")

    def _bind_children_mousewheel(self, widget):
        """遞迴綁定所有子元件的滾輪事件"""
        try:
            for child in widget.winfo_children():
                child.bind("<MouseWheel>", self._on_mousewheel, add="+")
                self._bind_children_mousewheel(child)
        except Exception:
            pass

    def _on_mousewheel(self, event):
        """滾輪事件處理 — 橫向滾動"""
        if self._canvas.winfo_exists():
            self._canvas.xview_scroll(int(-event.delta / 120) * 3, "units")

    def _on_inner_configure(self, event):
        """內部容器大小改變時更新滾動區域"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        # 重新計算置中
        self._center_content()

    def _on_canvas_configure(self, event):
        """Canvas 大小改變時讓卡牌垂直 + 水平置中"""
        self._center_content()

    def _center_content(self):
        """讓卡牌在 Canvas 中水平垂直置中"""
        try:
            canvas_w = self._canvas.winfo_width()
            canvas_h = self._canvas.winfo_height()
            inner_w = self._inner_frame.winfo_reqwidth()
            inner_h = self._inner_frame.winfo_reqheight()

            # 垂直置中
            y_offset = max(0, (canvas_h - inner_h) // 2)
            # 水平置中（如果內容比 canvas 窄才置中，否則靠左）
            x_offset = max(0, (canvas_w - inner_w) // 2)

            self._canvas.coords(self._canvas_window, x_offset, y_offset)
        except Exception:
            pass

    def _load_monsters(self):
        """從 config 載入怪物資料並建立卡牌"""
        monsters = self.app.config_manager.config.get("monsters", [])
        for monster in monsters:
            card = MonsterCard(self._inner_frame, monster, self.app)
            card.pack(side="left", padx=12, pady=10)
            self.cards[monster["id"]] = card
            # 綁定卡牌及子元件的滾輪
            self._bind_mousewheel(card)
            card.after(100, lambda c=card: self._bind_children_mousewheel(c))
