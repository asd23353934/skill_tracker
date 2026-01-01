"""
技能追蹤器
用於追蹤遊戲技能冷卻時間，支援網路房間同步
支援多種配置檔案，適應不同職業與 BOSS 場景
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from PIL import Image, ImageTk
import json
import os
import sys
import threading
import time
from pynput import keyboard
import winsound
import socket
import socketserver
import hashlib


# ==================== 工具函數 ====================

def resource_path(relative_path):
    """獲取資源文件路徑（支援 PyInstaller 打包）"""
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==================== 網路管理 ====================

class NetworkManager:
    """管理網路連線、房間創建與技能同步"""
    
    def __init__(self, skill_callback, members_callback):
        self.skill_callback = skill_callback
        self.members_callback = members_callback
        self.server = None
        self.client = None
        self.room_code = None
        self.is_host = False
        self.members = []
    
    def create_room(self):
        """創建新房間，返回房間代碼"""
        try:
            self.room_code = hashlib.md5(str(time.time()).encode()).hexdigest()[:6].upper()
            self.is_host = True
            self.members = []
            self.server = SkillServer(self.skill_callback, self._on_member_update)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            return self.room_code
        except:
            return None
    
    def join_room(self, room_code, player_name):
        """加入指定房間"""
        try:
            self.room_code = room_code
            self.is_host = False
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(('127.0.0.1', 9999))
            
            join_msg = json.dumps({'type': 'join', 'player': player_name})
            self.client.send(join_msg.encode())
            
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return True
        except:
            return False
    
    def leave_room(self):
        """離開當前房間"""
        if self.client:
            try:
                leave_msg = json.dumps({'type': 'leave'})
                self.client.send(leave_msg.encode())
                self.client.close()
            except:
                pass
        self.client = None
        self.room_code = None
        self.