"""
Toast 通知元件
左下角彈出式通知，支援成功/失敗顏色，可手動關閉，自動淡出
"""

import customtkinter as ctk
from src.ui.theme import AppTheme


class Toast(ctk.CTkFrame):
    """左下角浮動通知"""

    # 顏色對應
    COLORS = {
        "success": {"bg": "#0d3320", "border": "#10b981", "text": "#6ee7b7"},
        "error": {"bg": "#3b1111", "border": "#ef4444", "text": "#fca5a5"},
        "info": {"bg": "#1a2744", "border": "#3b82f6", "text": "#93bbfd"},
    }

    # 自動消失時間 (ms)
    AUTO_DISMISS_MS = 3000

    def __init__(self, parent, message, toast_type="success"):
        """建立 Toast 通知

        Args:
            parent: 父元件（主視窗）
            message: 通知文字
            toast_type: 類型 ("success" / "error" / "info")
        """
        colors = self.COLORS.get(toast_type, self.COLORS["info"])

        super().__init__(
            parent,
            fg_color=colors["bg"],
            corner_radius=8,
            border_width=1,
            border_color=colors["border"],
        )

        self._dismiss_id = None

        # 圖示對應
        icon_map = {"success": "✓", "error": "✕", "info": "ℹ"}
        icon = icon_map.get(toast_type, "ℹ")

        # 內容容器
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=8)

        # 圖示
        ctk.CTkLabel(
            content,
            text=icon,
            font=(AppTheme.FONT_FAMILY, 14, "bold"),
            text_color=colors["border"],
            width=20,
        ).pack(side="left", padx=(0, 8))

        # 訊息文字
        ctk.CTkLabel(
            content,
            text=message,
            font=AppTheme.FONT_BODY_MD,
            text_color=colors["text"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # 關閉按鈕
        ctk.CTkButton(
            content,
            text="✕",
            width=20,
            height=20,
            corner_radius=3,
            fg_color="transparent",
            hover_color=colors["border"],
            text_color=colors["text"],
            font=(AppTheme.FONT_FAMILY, 11),
            command=self.dismiss,
        ).pack(side="right", padx=(8, 0))

        # 自動消失
        self._dismiss_id = self.after(self.AUTO_DISMISS_MS, self.dismiss)

    def dismiss(self):
        """關閉通知"""
        if self._dismiss_id:
            self.after_cancel(self._dismiss_id)
            self._dismiss_id = None
        try:
            self.destroy()
        except Exception:
            pass


class ToastManager:
    """Toast 管理器 — 管理多個 Toast 的定位與堆疊"""

    MARGIN_BOTTOM = 16
    MARGIN_LEFT = 16
    GAP = 8

    def __init__(self, parent):
        """初始化

        Args:
            parent: 主視窗（CTk 或 CTkFrame）
        """
        self.parent = parent
        self._toasts = []

    def show(self, message, toast_type="success"):
        """顯示一個 Toast 通知

        Args:
            message: 文字內容
            toast_type: "success" / "error" / "info"
        """
        toast = Toast(self.parent, message, toast_type)

        # 覆寫 dismiss 以在銷毀時更新位置
        original_dismiss = toast.dismiss

        def _dismiss_and_reposition():
            if toast in self._toasts:
                self._toasts.remove(toast)
            original_dismiss()
            self._reposition()

        toast.dismiss = _dismiss_and_reposition

        self._toasts.append(toast)
        self._reposition()

    def _reposition(self):
        """重新計算所有 Toast 的位置（從下往上堆疊）"""
        y_offset = self.MARGIN_BOTTOM
        for toast in reversed(self._toasts):
            try:
                toast.place(
                    x=self.MARGIN_LEFT,
                    rely=1.0,
                    y=-y_offset,
                    anchor="sw",
                )
                toast.lift()
                toast.update_idletasks()
                y_offset += toast.winfo_reqheight() + self.GAP
            except Exception:
                pass
