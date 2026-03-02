"""
怪物重生頁面
橫向滾動大卡牌，按鍵觸發浮動計時視窗（從 0 數到設定時間）
卡片功能：重生時間修改、快捷鍵（含重置）、提前提示、聲音、循環、常駐
名稱標籤顯示於卡片圖示下方（卡片內）
"""

import tkinter as tk

import customtkinter as ctk
from tkinter import simpledialog
from PIL import Image

from src.ui.theme import AppTheme
from src.ui.helpers import resource_path


class MonsterCard(ctk.CTkFrame):
    """怪物重生大卡牌（名稱在圖示下方、卡片內）"""

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

        # 音效選項映射（label → filename）及反查快取（filename → label）
        self._sound_label_map: dict[str, str] = {}
        self._sound_filename_map: dict[str, str] = {}  # O(1) 反查
        self._build_sound_options()

        self._build_ui()

    # --------------------------------------------------
    # 音效對應
    # --------------------------------------------------
    def _build_sound_options(self):
        """建立音效下拉選項映射及 O(1) 反查快取"""
        self._sound_label_map = {"全域設定": ""}
        if self.app.sound_manager:
            for filename in self.app.sound_manager.list_sounds():
                label = self.app.sound_manager.get_sound_label(filename)
                self._sound_label_map[label] = filename
        # 反查快取：filename → label（排除空字串「全域設定」以免誤匹配）
        self._sound_filename_map = {v: k for k, v in self._sound_label_map.items() if v}

    def _get_label_for_filename(self, filename: str) -> str:
        """根據檔名 O(1) 取得對應的下拉選項標籤"""
        if not filename:
            return "全域設定"
        return self._sound_filename_map.get(filename, "全域設定")

    # --------------------------------------------------
    # UI 建構
    # --------------------------------------------------
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

        # === 名稱（圖示下方，卡片內）===
        ctk.CTkLabel(
            self,
            text=self.monster["name"],
            font=AppTheme.FONT_TITLE_MD,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(pady=(4, 0))

        # 載入圖示圖片
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
                    icon_container,
                    text="👾",
                    font=(AppTheme.FONT_FAMILY, 36),
                    text_color=AppTheme.TEXT_MUTED,
                ).place(relx=0.5, rely=0.5, anchor="center")

        # === 分隔線 ===
        ctk.CTkFrame(self, fg_color=AppTheme.GOLD_MUTED, height=1).pack(
            fill="x", padx=24, pady=(0, 6)
        )

        # === 重生時間（可點擊修改 + 重置）===
        respawn_frame = ctk.CTkFrame(self, fg_color="transparent")
        respawn_frame.pack(fill="x", padx=24, pady=(0, 3))

        ctk.CTkLabel(
            respawn_frame,
            text="⏱ 重生時間",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_SECONDARY,
        ).pack(side="left")

        ctk.CTkButton(
            respawn_frame,
            text="↺",
            command=lambda: self.app.reset_respawn_time(self.monster_id),
            width=26,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.BG_SECONDARY,
            text_color=AppTheme.TEXT_SECONDARY,
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="right", padx=(2, 0))

        respawn = self.monster.get("respawn_time", 0)
        original_respawn = self.app.config_manager.get_original_respawn_time(self.monster_id)
        is_modified = original_respawn is not None and respawn != original_respawn

        self.respawn_btn = ctk.CTkButton(
            respawn_frame,
            text=f"{respawn}秒",
            command=lambda: self.app.edit_respawn_time(self.monster_id),
            width=70,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_TERTIARY,
            hover_color=AppTheme.ACCENT_BLUE if is_modified else AppTheme.BG_SECONDARY,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_MD_BOLD,
        )
        self.respawn_btn.pack(side="right")
        self.app.monster_respawn_buttons[self.monster_id] = self.respawn_btn

        # === 快捷鍵（含重置）===
        hotkey_frame = ctk.CTkFrame(self, fg_color="transparent")
        hotkey_frame.pack(fill="x", padx=24, pady=(3, 3))

        ctk.CTkLabel(
            hotkey_frame,
            text="⌨ 快捷鍵",
            font=AppTheme.FONT_BODY_MD,
            text_color=AppTheme.TEXT_SECONDARY,
        ).pack(side="left")

        ctk.CTkButton(
            hotkey_frame,
            text="↺",
            command=self._reset_hotkey,
            width=26,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.BG_SECONDARY,
            text_color=AppTheme.TEXT_SECONDARY,
            font=AppTheme.FONT_BTN_SM,
        ).pack(side="right", padx=(2, 0))

        hotkey_text = self.monster.get("hotkey", "") or "未設定"
        has_hotkey = bool(self.monster.get("hotkey"))

        self.hotkey_btn = ctk.CTkButton(
            hotkey_frame,
            text=hotkey_text,
            command=self._begin_capture_hotkey,
            width=80,
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_YELLOW if has_hotkey else AppTheme.BG_TERTIARY,
            hover_color=AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
            text_color="#000000" if has_hotkey else AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_BODY_MD_BOLD,
        )
        self.hotkey_btn.pack(side="right")

        # === 提前提示秒數 ===
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
            height=26,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.ACCENT_ORANGE if alert_before > 0 else AppTheme.BG_TERTIARY,
            hover_color=AppTheme.ACCENT_ORANGE_HOVER if alert_before > 0 else AppTheme.BG_SECONDARY,
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
            height=26,
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
        preview_frame.pack(fill="x", padx=24, pady=(2, 4))

        ctk.CTkButton(
            preview_frame,
            text="▶ 試聽",
            command=self._preview_sound,
            width=70,
            height=22,
            corner_radius=AppTheme.CORNER_SM,
            fg_color=AppTheme.BG_TERTIARY,
            hover_color=AppTheme.GOLD_MUTED,
            text_color=AppTheme.TEXT_PRIMARY,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="right")

        # === 分隔線 ===
        ctk.CTkFrame(self, fg_color=AppTheme.GOLD_MUTED, height=1).pack(
            fill="x", padx=24, pady=(2, 6)
        )

        # === 底部：循環（預設開啟）+ 常駐 ===
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=24, pady=(0, 8))

        self.loop_var = ctk.BooleanVar(value=self.monster.get("loop", True))
        ctk.CTkCheckBox(
            bottom_frame,
            text="循環",
            variable=self.loop_var,
            command=self._on_loop_changed,
            width=65,
            height=24,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_GREEN,
            hover_color=AppTheme.ACCENT_GREEN_HOVER,
            text_color=AppTheme.ACCENT_GREEN,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left", padx=(0, 8))

        self.permanent_var = ctk.BooleanVar(value=self.monster.get("permanent", False))
        ctk.CTkCheckBox(
            bottom_frame,
            text="常駐",
            variable=self.permanent_var,
            command=self._on_permanent_changed,
            width=65,
            height=24,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=3,
            fg_color=AppTheme.ACCENT_YELLOW,
            hover_color=AppTheme.ACCENT_YELLOW_HOVER,
            text_color=AppTheme.ACCENT_YELLOW,
            font=AppTheme.FONT_BODY_SM,
        ).pack(side="left")

        # Hover 邊框效果
        self.bind("<Enter>", lambda e: self.configure(border_color=AppTheme.GOLD_PRIMARY))
        self.bind("<Leave>", lambda e: self.configure(border_color=AppTheme.BORDER_GOLD_SUBTLE))

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

    def _reset_hotkey(self):
        """重置快捷鍵"""
        if not self.monster.get("hotkey"):
            return
        self.monster["hotkey"] = ""
        self.app.save_monsters()
        self.update_hotkey_display("未設定", False)

    def _edit_alert_seconds(self):
        """編輯提前提示秒數"""
        self.app.hotkey_manager.enabled = False
        current = self.monster.get("alert_before", 10)

        new_val = simpledialog.askinteger(
            "提前提示秒數",
            f"請輸入 '{self.monster['name']}' 提前幾秒提示:\n(輸入 0 表示關閉提前提示)",
            initialvalue=current,
            minvalue=0,
            maxvalue=999,
            parent=self.app,
        )

        self.app.hotkey_manager.enabled = True

        if new_val is not None:
            self.monster["alert_before"] = new_val
            self.app.save_monsters()
            self.alert_btn.configure(
                text=f"{new_val}s",
                fg_color=AppTheme.ACCENT_ORANGE if new_val > 0 else AppTheme.BG_TERTIARY,
                hover_color=AppTheme.ACCENT_ORANGE_HOVER if new_val > 0 else AppTheme.BG_SECONDARY,
                text_color="#ffffff" if new_val > 0 else AppTheme.TEXT_MUTED,
            )

    def _on_loop_changed(self):
        """循環切換"""
        self.app.update_monster_loop(self.monster_id, self.loop_var.get())

    def _on_permanent_changed(self):
        """常駐切換"""
        self.app.update_monster_permanent(self.monster_id, self.permanent_var.get())

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
            filename = self.app.global_alert_sound
        if filename and self.app.sound_manager:
            self.app.sound_manager.play(filename)

    def update_hotkey_display(self, key_str: str, has_hotkey: bool):
        """更新快捷鍵顯示

        Args:
            key_str: 顯示的按鍵字串
            has_hotkey: 是否已設定快捷鍵
        """
        self.hotkey_btn.configure(
            text=key_str if has_hotkey else "未設定",
            fg_color=AppTheme.ACCENT_YELLOW if has_hotkey else AppTheme.BG_TERTIARY,
            hover_color=AppTheme.ACCENT_YELLOW_HOVER if has_hotkey else AppTheme.BG_SECONDARY,
            text_color="#000000" if has_hotkey else AppTheme.TEXT_MUTED,
        )


class MonsterPage(ctk.CTkFrame):
    """怪物重生頁面 — 填滿整個內容區域，橫向滾動，卡牌水平垂直置中"""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.cards: dict = {}
        # 防止滾輪事件重複綁定同一元件（避免單次滾動觸發多次回呼）
        self._bound_mousewheel_widgets: set = set()

        self._build_ui()

    def _build_ui(self):
        """建構頁面 UI（標題與卡片同容器，整體垂直置中）"""
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            self,
            bg="#0a0e1a",
            highlightthickness=0,
            bd=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # 整體容器（標題 + 卡片一起置中）
        self._inner_frame = ctk.CTkFrame(self._canvas, fg_color="transparent")
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner_frame, anchor="nw"
        )

        # === 標題（與卡片同容器，自然緊鄰卡片上方）===
        title_frame = ctk.CTkFrame(self._inner_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            title_frame,
            text="🍁 怪物重生",
            font=AppTheme.FONT_TITLE_LG,
            text_color=AppTheme.TEXT_GOLD,
        ).pack(anchor="center")

        ctk.CTkLabel(
            title_frame,
            text="按下快捷鍵開始計時（從 0 數到設定時間）",
            font=AppTheme.FONT_BODY_SM,
            text_color=AppTheme.TEXT_MUTED,
        ).pack(anchor="center", pady=(2, 0))

        # === 卡片橫向容器 ===
        self._cards_frame = ctk.CTkFrame(self._inner_frame, fg_color="transparent")
        self._cards_frame.pack()

        self._inner_frame.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # 綁定基礎容器的滾輪（一次性，使用 dedup 集合保護）
        self._bind_mousewheel(self._canvas)
        self._bind_mousewheel(self._inner_frame)
        self._bind_mousewheel(self._cards_frame)
        self._bind_mousewheel(self)

        self._load_monsters()

    def _bind_mousewheel(self, widget):
        """綁定滾輪事件（含防重複綁定保護）

        tkinter 的 <MouseWheel> 不會向上傳遞，必須對每個可能懸停的子元件都綁定。
        使用 _bound_mousewheel_widgets 集合確保同一元件只綁定一次。
        """
        if widget in self._bound_mousewheel_widgets:
            return
        self._bound_mousewheel_widgets.add(widget)
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")

    def _bind_children_mousewheel(self, widget):
        """遞迴綁定所有子元件的滾輪事件（每個元件只綁定一次）"""
        try:
            for child in widget.winfo_children():
                self._bind_mousewheel(child)  # dedup 保護在此
                self._bind_children_mousewheel(child)
        except Exception:
            pass

    def _on_mousewheel(self, event):
        """滾輪事件 — 橫向滾動"""
        if self._canvas.winfo_exists():
            self._canvas.xview_scroll(int(-event.delta / 120) * 3, "units")

    def _on_inner_configure(self, event):
        """內部容器大小改變時更新滾動區域並重新置中"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._center_content()

    def _on_canvas_configure(self, event):
        """Canvas 大小改變時重新置中"""
        self._center_content()

    def _center_content(self):
        """讓標題＋卡牌整體在 Canvas 中水平垂直置中"""
        try:
            canvas_w = self._canvas.winfo_width()
            canvas_h = self._canvas.winfo_height()
            inner_w = self._inner_frame.winfo_reqwidth()
            inner_h = self._inner_frame.winfo_reqheight()

            x_offset = max(0, (canvas_w - inner_w) // 2)
            y_offset = max(0, (canvas_h - inner_h) // 2)

            self._canvas.coords(self._canvas_window, x_offset, y_offset)
        except Exception:
            pass

    def _load_monsters(self):
        """從 config 載入怪物資料並建立卡牌"""
        monsters = self.app.config_manager.config.get("monsters", [])
        for monster in monsters:
            card = MonsterCard(self._cards_frame, monster, self.app)
            card.pack(side="left", padx=12, pady=10)
            self.cards[monster["id"]] = card
            self._bind_mousewheel(card)
            # 100ms 後才能取到完整子元件樹，一次性遞迴綁定
            card.after(100, lambda c=card: self._bind_children_mousewheel(c))
