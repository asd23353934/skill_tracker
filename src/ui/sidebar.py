"""
固定式側邊欄導航元件
僅顯示 icon，hover 時以 tooltip 顯示文字
不展開，不擠壓其他元件
"""

import customtkinter as ctk
from src.ui.theme import AppTheme


class Sidebar(ctk.CTkFrame):
    """固定寬度側邊欄導航 — icon-only + tooltip"""

    # 頁面定義：(page_name, icon, label)
    PAGES = [
        ("skill", "🍁", "技能倒數"),
        ("monster", "👾", "怪物重生"),
    ]

    def __init__(self, parent, app, on_page_change):
        super().__init__(
            parent,
            width=AppTheme.SIDEBAR_COLLAPSED,
            fg_color=AppTheme.SIDEBAR_BG,
            corner_radius=0,
        )
        self.pack_propagate(False)
        self.app = app
        self.on_page_change = on_page_change
        self.current_page = "skill"

        # UI 元素追蹤
        self._items = {}       # {page_name: {frame, indicator, btn}}
        self.buttons = {}      # 向下相容

        # tooltip 元件
        self._tooltip_win = None
        self._tooltip_after_id = None
        self._tooltip_auto_hide_id = None
        self._tooltip_widget = None

        self._build_ui()

    def _build_ui(self):
        """建構側邊欄 UI"""
        # 頂部間距
        ctk.CTkFrame(self, fg_color="transparent", height=16).pack(fill="x")

        # 側邊欄分隔線（頂部裝飾）
        ctk.CTkFrame(
            self, fg_color=AppTheme.GOLD_MUTED, height=1
        ).pack(fill="x", padx=8, pady=(0, 8))

        for page_name, icon, label in self.PAGES:
            self._create_nav_item(page_name, icon, label)

        # 底部裝飾分隔線
        ctk.CTkFrame(
            self, fg_color=AppTheme.GOLD_MUTED, height=1
        ).pack(fill="x", padx=8, pady=(8, 0))

    def _create_nav_item(self, page_name, icon, label_text):
        """建立單個導航項目

        Args:
            page_name: 頁面識別名稱
            icon: 圖示 emoji
            label_text: tooltip 文字
        """
        is_active = page_name == self.current_page

        # 項目外框
        item_frame = ctk.CTkFrame(
            self,
            fg_color=AppTheme.SIDEBAR_HOVER_BG if is_active else "transparent",
            corner_radius=AppTheme.CORNER_MD,
            height=48,
        )
        item_frame.pack(fill="x", padx=6, pady=2)
        item_frame.pack_propagate(False)

        # 左側金色活動指示條
        indicator = ctk.CTkFrame(
            item_frame,
            width=3,
            fg_color=AppTheme.GOLD_PRIMARY if is_active else "transparent",
            corner_radius=2,
        )
        indicator.pack(side="left", fill="y", padx=(2, 0), pady=6)

        # 圖示按鈕
        btn = ctk.CTkButton(
            item_frame,
            text=icon,
            command=lambda p=page_name: self._on_click(p),
            width=44,
            height=44,
            corner_radius=AppTheme.CORNER_MD,
            fg_color="transparent",
            hover_color=AppTheme.SIDEBAR_HOVER_BG,
            font=AppTheme.FONT_SIDEBAR_ICON,
            text_color=(
                AppTheme.GOLD_LIGHT if is_active
                else AppTheme.SIDEBAR_ICON_INACTIVE
            ),
        )
        btn.pack(side="left")

        # 為按鈕綁定 tooltip 事件
        btn.bind("<Enter>", lambda e, t=label_text: self._show_tooltip(e, t))
        btn.bind("<Leave>", lambda e: self._hide_tooltip())

        # 為整個 item_frame 綁定點擊事件
        item_frame.bind(
            "<Button-1>", lambda e, p=page_name: self._on_click(p)
        )

        # 存儲引用
        self._items[page_name] = {
            "frame": item_frame,
            "indicator": indicator,
            "btn": btn,
            "label_text": label_text,
        }
        self.buttons[page_name] = btn

    # --------------------------------------------------
    # Tooltip
    # --------------------------------------------------
    def _show_tooltip(self, event, text):
        """顯示 tooltip（延遲 300ms 避免閃爍）"""
        self._hide_tooltip()
        self._tooltip_widget = event.widget
        self._tooltip_after_id = self.after(
            300, lambda: self._create_tooltip(event, text)
        )

    def _create_tooltip(self, event, text):
        """建立 tooltip 視窗"""
        if self._tooltip_win:
            return

        widget = event.widget
        try:
            # 確認 widget 還存在且滑鼠仍在上面
            if not widget.winfo_exists():
                return
        except Exception:
            return

        # 計算 tooltip 位置（按鈕右側）
        x = widget.winfo_rootx() + widget.winfo_width() + 4
        y = widget.winfo_rooty() + widget.winfo_height() // 2 - 14

        import tkinter as tk
        self._tooltip_win = tw = tk.Toplevel(self)
        tw.withdraw()
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.configure(bg=AppTheme.GOLD_DARK)

        label = ctk.CTkLabel(
            tw,
            text=text,
            font=AppTheme.FONT_BODY_MD_BOLD,
            text_color=AppTheme.TEXT_PRIMARY,
            fg_color=AppTheme.BG_SECONDARY,
            corner_radius=4,
            padx=10,
            pady=4,
        )
        label.pack(padx=1, pady=1)

        tw.update_idletasks()
        tw.geometry(f"+{x}+{y}")
        tw.deiconify()

        # 安全機制：2 秒後自動關閉，防止殘留
        self._tooltip_auto_hide_id = self.after(2000, self._hide_tooltip)

    def _hide_tooltip(self):
        """隱藏 tooltip"""
        if self._tooltip_after_id:
            try:
                self.after_cancel(self._tooltip_after_id)
            except Exception:
                pass
            self._tooltip_after_id = None

        if hasattr(self, "_tooltip_auto_hide_id") and self._tooltip_auto_hide_id:
            try:
                self.after_cancel(self._tooltip_auto_hide_id)
            except Exception:
                pass
            self._tooltip_auto_hide_id = None

        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass
            self._tooltip_win = None

    # --------------------------------------------------
    # 事件處理
    # --------------------------------------------------
    def _on_click(self, page_name):
        """點擊頁面按鈕"""
        # 切換頁面時強制關閉 tooltip
        self._hide_tooltip()

        if page_name == self.current_page:
            return

        self.current_page = page_name
        self._update_button_states()
        self.on_page_change(page_name)

    # --------------------------------------------------
    # 狀態更新
    # --------------------------------------------------
    def _update_button_states(self):
        """更新所有導航項目的 active / inactive 狀態"""
        for name, item_data in self._items.items():
            is_active = name == self.current_page

            # 外框背景
            item_data["frame"].configure(
                fg_color=(
                    AppTheme.SIDEBAR_HOVER_BG if is_active
                    else "transparent"
                )
            )

            # 金色指示條
            item_data["indicator"].configure(
                fg_color=(
                    AppTheme.GOLD_PRIMARY if is_active
                    else "transparent"
                )
            )

            # 圖示顏色
            item_data["btn"].configure(
                text_color=(
                    AppTheme.GOLD_LIGHT if is_active
                    else AppTheme.SIDEBAR_ICON_INACTIVE
                )
            )
