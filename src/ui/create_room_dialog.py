"""
支援外網 IP 的房間創建對話框
"""

import tkinter as tk
from tkinter import messagebox
from src.ui.components import Colors, Fonts, RoundedButton
from src.ui.dialogs import BaseDialog
from src.core.ip_encoder import RoomCodeGenerator
import requests


class CreateRoomDialog(BaseDialog):
    """創建房間對話框（支援外網 IP）"""
    
    def __init__(self, parent):
        super().__init__(parent, "創建房間", 450, 400)
        self.generator = RoomCodeGenerator()
        self.selected_ip = None
        self.room_code = None
        self._create_ui()
    
    def _create_ui(self):
        """創建 UI"""
        # 標題
        tk.Label(
            self.dialog, text="🏠 創建房間", 
            bg=Colors.BG_MEDIUM, fg=Colors.ACCENT_YELLOW,
            font=Fonts.TITLE_SMALL
        ).pack(pady=(20, 10))
        
        # 說明
        tk.Label(
            self.dialog, 
            text="請選擇要使用的 IP 地址\n同一區域網使用內網 IP，跨網路使用外網 IP", 
            bg=Colors.BG_MEDIUM, fg=Colors.TEXT_SECONDARY,
            font=('Microsoft JhengHei', 9), justify=tk.CENTER
        ).pack(pady=(0, 15))
        
        # IP 選項區域
        ip_frame = tk.Frame(self.dialog, bg=Colors.BG_MEDIUM)
        ip_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # 獲取 IP
        self.local_ip = self.generator.get_local_ip()
        self.public_ip = self._get_public_ip()
        
        # 內網 IP 選項
        self.ip_var = tk.StringVar(value="local")
        
        local_frame = tk.Frame(ip_frame, bg=Colors.BG_LIGHT, relief=tk.RIDGE, bd=1)
        local_frame.pack(fill=tk.X, pady=5)
        
        tk.Radiobutton(
            local_frame,
            text=f"內網 IP: {self.local_ip}",
            variable=self.ip_var,
            value="local",
            bg=Colors.BG_LIGHT,
            fg=Colors.TEXT_PRIMARY,
            font=Fonts.BODY_MEDIUM,
            selectcolor=Colors.BG_DARK,
            activebackground=Colors.BG_LIGHT
        ).pack(anchor=tk.W, padx=10, pady=10)
        
        tk.Label(
            local_frame,
            text="✅ 適用：同一 WiFi、區域網",
            bg=Colors.BG_LIGHT,
            fg=Colors.ACCENT_GREEN,
            font=('Microsoft JhengHei', 8)
        ).pack(anchor=tk.W, padx=30, pady=(0, 10))
        
        # 外網 IP 選項
        public_frame = tk.Frame(ip_frame, bg=Colors.BG_LIGHT, relief=tk.RIDGE, bd=1)
        public_frame.pack(fill=tk.X, pady=5)
        
        if self.public_ip:
            tk.Radiobutton(
                public_frame,
                text=f"外網 IP: {self.public_ip}",
                variable=self.ip_var,
                value="public",
                bg=Colors.BG_LIGHT,
                fg=Colors.TEXT_PRIMARY,
                font=Fonts.BODY_MEDIUM,
                selectcolor=Colors.BG_DARK,
                activebackground=Colors.BG_LIGHT
            ).pack(anchor=tk.W, padx=10, pady=10)
            
            tk.Label(
                public_frame,
                text="⚠️ 需要：端口轉發、防火牆設定",
                bg=Colors.BG_LIGHT,
                fg=Colors.ACCENT_YELLOW,
                font=('Microsoft JhengHei', 8)
            ).pack(anchor=tk.W, padx=30, pady=(0, 10))
        else:
            tk.Label(
                public_frame,
                text="❌ 無法獲取外網 IP",
                bg=Colors.BG_LIGHT,
                fg=Colors.TEXT_SECONDARY,
                font=Fonts.BODY_MEDIUM
            ).pack(anchor=tk.W, padx=10, pady=10)
        
        # 提示
        tk.Label(
            self.dialog,
            text="💡 不確定？選擇內網 IP 即可",
            bg=Colors.BG_MEDIUM,
            fg=Colors.TEXT_SECONDARY,
            font=('Microsoft JhengHei', 8)
        ).pack(pady=10)
        
        # 按鈕
        btn_frame = tk.Frame(self.dialog, bg=Colors.BG_MEDIUM)
        btn_frame.pack(pady=20)
        
        RoundedButton(
            btn_frame, "✓ 創建房間", self._create,
            Colors.ACCENT_BLUE, width=120, height=35
        ).pack(side=tk.LEFT, padx=5)
        
        RoundedButton(
            btn_frame, "✗ 取消", self.close,
            Colors.BG_LIGHT, width=120, height=35
        ).pack(side=tk.LEFT, padx=5)
    
    def _get_public_ip(self):
        """獲取外網 IP"""
        try:
            response = requests.get('https://api.ipify.org', timeout=3)
            return response.text
        except:
            return None
    
    def _create(self):
        """創建房間"""
        ip_type = self.ip_var.get()
        
        if ip_type == "local":
            ip = self.local_ip
        else:
            if not self.public_ip:
                messagebox.showerror("錯誤", "無法獲取外網 IP", parent=self.dialog)
                return
            ip = self.public_ip
        
        # 使用選擇的 IP 生成房間代碼
        code = self.generator.encode_ip_to_base32(ip)
        if not code:
            messagebox.showerror("錯誤", "IP 編碼失敗", parent=self.dialog)
            return
        
        # 生成完整的 UUID 風格代碼
        import time
        import uuid
        import hashlib
        
        timestamp = int(time.time())
        time_code = ''
        for _ in range(4):
            time_code = self.generator.BASE32_CHARS[timestamp % 32] + time_code
            timestamp //= 32
        
        uuid_str = str(uuid.uuid4()).replace('-', '')
        uuid_hash = hashlib.md5(uuid_str.encode()).hexdigest()
        uuid_code = ''
        for i in range(4):
            byte_val = int(uuid_hash[i*2:i*2+2], 16)
            uuid_code += self.generator.BASE32_CHARS[byte_val % 32]
        
        self.room_code = f"{code}-{time_code}-{uuid_code}"
        self.selected_ip = ip
        
        self.result = {
            'code': self.room_code,
            'ip': ip,
            'type': ip_type
        }
        
        self.close()


if __name__ == '__main__':
    # 測試
    root = tk.Tk()
    root.withdraw()
    
    dialog = CreateRoomDialog(root)
    result = dialog.show()
    
    if result:
        print(f"房間代碼: {result['code']}")
        print(f"IP 地址: {result['ip']}")
        print(f"類型: {result['type']}")
    else:
        print("取消創建")
    
    root.destroy()
