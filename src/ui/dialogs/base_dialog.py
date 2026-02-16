"""
基礎對話框
CTkToplevel 基礎類別 — RPG 金色邊框風格
"""

import customtkinter as ctk
from src.ui.theme import AppTheme
from src.ui.helpers import resource_path


class BaseDialog(ctk.CTkToplevel):
    """基礎對話框 — RPG 金色邊框"""

    def __init__(self, parent, title, width=400, height=300):
        super().__init__(parent)
        self.title(title)
        self.attributes("-topmost", True)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(fg_color=AppTheme.GOLD_DARK)

        # 設定對話框圖示
        try:
            import os
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.after(200, lambda: self.iconbitmap(icon_path))
        except Exception:
            pass

        # 置中
        self.update_idletasks()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.grab_set()
        self.focus_force()

        self.result = None

        # ===== RPG 金色邊框效果 =====
        # 外層作為金色邊框（CTkToplevel 的 fg_color = GOLD_DARK）
        # 內層為實際內容區域
        self.inner = ctk.CTkFrame(
            self,
            fg_color=AppTheme.BG_DEEP,
            corner_radius=AppTheme.CORNER_MD,
            border_width=1,
            border_color=AppTheme.GOLD_MUTED,
        )
        self.inner.pack(fill="both", expand=True, padx=3, pady=3)

        # 關閉事件
        self.protocol("WM_DELETE_WINDOW", self.close)

    def show(self):
        """顯示對話框並等待關閉"""
        self.wait_window()
        return self.result

    def close(self):
        """關閉對話框"""
        self.grab_release()
        self.destroy()
