"""
連線模式選擇對話框
讓用戶選擇使用哪種連線方式
"""

import tkinter as tk
from tkinter import messagebox
from src.ui.components import Colors, Fonts, RoundedButton
from src.ui.dialogs import BaseDialog


class ConnectionModeDialog(BaseDialog):
    """連線模式選擇對話框"""
    
    def __init__(self, parent):
        """初始化對話框
        
        Args:
            parent: 父視窗
        """
        self.selected_mode = None
        super().__init__(parent, "選擇連線模式", 600, 450)
        self._create_ui()
    
    def _create_ui(self):
        """創建 UI"""
        # 標題
        title_frame = tk.Frame(self.dialog, bg=Colors.BG_MEDIUM)
        title_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(
            title_frame,
            text="🌐 選擇連線模式",
            bg=Colors.BG_MEDIUM,
            fg=Colors.TEXT_PRIMARY,
            font=Fonts.TITLE_SMALL
        ).pack()
        
        # 選項區域
        options_frame = tk.Frame(self.dialog, bg=Colors.BG_MEDIUM)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 選項 1: 中繼伺服器（推薦）
        self._create_option(
            options_frame,
            "🌟 中繼伺服器（推薦）",
            "✅ 100% 免設定\n✅ 任何網路都可用\n⚠️ 延遲約 1 秒",
            Colors.ACCENT_GREEN,
            "relay",
            0
        )
        
        # 選項 2: UPnP 自動端口映射
        self._create_option(
            options_frame,
            "🔧 UPnP 自動端口映射",
            "✅ 自動設定\n✅ P2P 直連，延遲低\n⚠️ 成功率約 70%",
            Colors.ACCENT_BLUE,
            "upnp",
            1
        )
        
        # 選項 3: 同網路（區域網）
        self._create_option(
            options_frame,
            "🏠 同網路（區域網）",
            "✅ 最簡單\n✅ 延遲最低\n❌ 只能同 WiFi",
            Colors.ACCENT_PURPLE,
            "local",
            2
        )
        
        # 按鈕區域
        btn_frame = tk.Frame(self.dialog, bg=Colors.BG_MEDIUM)
        btn_frame.pack(pady=15)
        
        RoundedButton(
            btn_frame,
            "取消",
            self.close,
            Colors.TEXT_SECONDARY,
            width=120,
            height=35
        ).pack()
    
    def _create_option(self, parent, title, description, color, mode, row):
        """創建選項按鈕"""
        option_frame = tk.Frame(parent, bg=Colors.BG_DARK, relief=tk.RIDGE, borderwidth=2)
        option_frame.grid(row=row, column=0, sticky='ew', pady=8)
        parent.grid_columnconfigure(0, weight=1)
        
        # 內容區域
        content_frame = tk.Frame(option_frame, bg=Colors.BG_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)
        
        # 標題
        tk.Label(
            content_frame,
            text=title,
            bg=Colors.BG_DARK,
            fg=color,
            font=Fonts.SUBTITLE,
            anchor='w'
        ).pack(fill=tk.X)
        
        # 說明
        tk.Label(
            content_frame,
            text=description,
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_SECONDARY,
            font=Fonts.BODY_SMALL,
            anchor='w',
            justify=tk.LEFT
        ).pack(fill=tk.X, pady=(5, 0))
        
        # 選擇按鈕
        btn = RoundedButton(
            content_frame,
            "選擇此模式",
            lambda: self._select_mode(mode),
            color,
            width=120,
            height=32
        )
        btn.pack(anchor='e', pady=(8, 0))
    
    def _select_mode(self, mode):
        """選擇模式"""
        self.selected_mode = mode
        self.result = mode
        self.close()
    
    def show(self):
        """顯示對話框並返回選擇的模式"""
        self.dialog.wait_window()
        return self.selected_mode


if __name__ == '__main__':
    # 測試
    root = tk.Tk()
    root.withdraw()
    
    dialog = ConnectionModeDialog(root)
    mode = dialog.show()
    
    print(f"選擇的模式: {mode}")
    
    root.destroy()
