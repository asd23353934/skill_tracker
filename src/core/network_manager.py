"""
網路管理模組
處理房間創建、加入、技能同步等網路功能
"""

import json
import socket
import socketserver
import threading
import time
from src.core.ip_encoder import create_room_code, decode_room_code


class NetworkManager:
    """網路管理器"""
    
    def __init__(self, skill_callback, members_callback):
        """初始化網路管理器
        
        Args:
            skill_callback: 技能接收回調函數
            members_callback: 成員更新回調函數
        """
        self.skill_callback = skill_callback
        self.members_callback = members_callback
        self.server = None
        self.client = None
        self.room_code = None
        self.host_ip = None
        self.is_host = False
        self.members = []
    
    def create_room(self):
        """創建新房間
        
        Returns:
            成功返回房間代碼，失敗返回 None
        """
        try:
            # 創建房間代碼（包含本機 IP）
            room_info = create_room_code()
            self.room_code = room_info['code']
            self.host_ip = room_info['ip']
            self.is_host = True
            self.members = []
            
            # 啟動伺服器
            self.server = SkillServer(self.skill_callback, self._on_member_update)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            
            print(f"✅ 房間已創建")
            print(f"   房間代碼: {self.room_code}")
            print(f"   主機 IP: {self.host_ip}")
            
            return self.room_code
        except Exception as e:
            print(f"❌ 創建房間失敗: {e}")
            return None
    
    def join_room(self, room_code, player_name):
        """加入指定房間
        
        Args:
            room_code: 房間代碼
            player_name: 玩家名稱
        
        Returns:
            成功返回 True，失敗返回 False
        """
        try:
            self.room_code = room_code
            self.is_host = False
            
            # 從房間代碼解碼 IP
            self.host_ip = decode_room_code(room_code)
            
            if not self.host_ip:
                print(f"❌ 無法解碼房間代碼: {room_code}")
                return False
            
            print(f"🔗 嘗試連線到: {self.host_ip}:9999")
            
            # 連接到主機
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(5)  # 5 秒超時
            self.client.connect((self.host_ip, 9999))
            
            join_msg = json.dumps({'type': 'join', 'player': player_name})
            self.client.send(join_msg.encode())
            
            threading.Thread(target=self._receive_messages, daemon=True).start()
            
            print(f"✅ 成功加入房間: {room_code}")
            print(f"   主機 IP: {self.host_ip}")
            
            return True
        except Exception as e:
            print(f"❌ 加入房間失敗: {e}")
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
                self.client = None
            return False
            
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
        self.is_host = False
        self.members = []
    
    def broadcast_skill(self, skill_data):
        """廣播技能使用訊息
        
        Args:
            skill_data: 技能資料字典
        """
        if self.is_host and self.server:
            self.server.broadcast(json.dumps(skill_data))
        elif self.client:
            try:
                self.client.send(json.dumps(skill_data).encode())
            except:
                pass
    
    def _on_member_update(self, members):
        """成員更新內部回調"""
        self.members = members
        self.members_callback(members)
    
    def _receive_messages(self):
        """接收網路訊息（客戶端）"""
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break
                msg = json.loads(data)
                if msg.get('type') == 'members':
                    self.members = msg.get('members', [])
                    self.members_callback(self.members)
                elif msg.get('type') == 'skill':
                    self.skill_callback(msg)
            except:
                break


class SkillServer(socketserver.ThreadingTCPServer):
    """技能同步伺服器"""
    allow_reuse_address = True
    
    def __init__(self, callback, members_callback):
        self.callback = callback
        self.members_callback = members_callback
        self.clients = {}
        super().__init__(('0.0.0.0', 9999), SkillHandler)
        self.skill_handler_callback = callback
        self.skill_handler_members_callback = members_callback
    
    def broadcast(self, message):
        """廣播訊息給所有客戶端"""
        for client in list(self.clients.keys()):
            try:
                client.send(message.encode())
            except:
                if client in self.clients:
                    del self.clients[client]
    
    def update_members(self):
        """更新成員列表"""
        members = list(self.clients.values())
        members_msg = json.dumps({'type': 'members', 'members': members})
        self.broadcast(members_msg)
        self.skill_handler_members_callback(members)


class SkillHandler(socketserver.BaseRequestHandler):
    """處理單個客戶端連線"""
    
    def handle(self):
        player_name = None
        while True:
            try:
                data = self.request.recv(1024).decode()
                if not data:
                    break
                msg = json.loads(data)
                
                if msg.get('type') == 'join':
                    player_name = msg.get('player', 'Unknown')
                    self.server.clients[self.request] = player_name
                    self.server.update_members()
                elif msg.get('type') == 'leave':
                    break
                elif msg.get('type') == 'skill':
                    self.server.broadcast(data)
                    self.server.skill_handler_callback(msg)
            except:
                break
        
        # 清理斷線客戶端
        if self.request in self.server.clients:
            del self.server.clients[self.request]
            self.server.update_members()
