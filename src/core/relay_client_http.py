"""
中繼伺服器客戶端 - HTTP 版本
使用 HTTP 輪詢代替 WebSocket，適用於所有平台
"""

import json
import threading
import time
import requests


class RelayClientHTTP:
    """中繼伺服器客戶端（HTTP 輪詢）"""
    
    # 中繼伺服器列表
    RELAY_SERVERS = [
        # Render.com 伺服器
        'https://skill-tracker-mqpk.onrender.com',
        
        # 本地測試
        'http://127.0.0.1:8888',
    ]
    
    def __init__(self, room_code, player_name, skill_callback, members_callback):
        """初始化中繼客戶端
        
        Args:
            room_code: 房間代碼
            player_name: 玩家名稱
            skill_callback: 技能回調
            members_callback: 成員回調
        """
        self.room_code = room_code
        self.player_name = player_name
        self.skill_callback = skill_callback
        self.members_callback = members_callback
        self.server_url = None
        self.connected = False
        self.is_host = False
        self.last_message_index = 0
        self.poll_thread = None
    
    def connect(self):
        """連線到中繼伺服器"""
        for server_url in self.RELAY_SERVERS:
            try:
                print(f"🔗 嘗試連線到中繼伺服器: {server_url}")
                
                # 測試伺服器是否可用
                response = requests.get(f"{server_url}/status", timeout=5)
                if response.status_code != 200:
                    print(f"⚠️ 伺服器回應錯誤: {response.status_code}")
                    continue
                
                # 初始化房間
                init_data = {
                    'type': 'init',
                    'room_code': self.room_code,
                    'player_name': self.player_name
                }
                
                response = requests.post(
                    f"{server_url}/relay",
                    json=init_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    resp_data = response.json()
                    
                    if resp_data.get('status') == 'ok':
                        self.server_url = server_url
                        self.connected = True
                        self.is_host = resp_data.get('is_host', False)
                        
                        print(f"✅ 已連線到中繼伺服器")
                        print(f"   房間: {self.room_code}")
                        print(f"   角色: {'主機' if self.is_host else '成員'}")
                        
                        # 啟動輪詢線程
                        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
                        self.poll_thread.start()
                        
                        return True
                    else:
                        print(f"❌ 伺服器拒絕: {resp_data.get('message')}")
                else:
                    print(f"❌ HTTP 錯誤: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"❌ 連線超時")
            except requests.exceptions.ConnectionError:
                print(f"❌ 無法連線")
            except Exception as e:
                print(f"❌ 連線失敗: {e}")
                continue
        
        return False
    
    def send_skill(self, skill_data):
        """發送技能數據"""
        if not self.connected or not self.server_url:
            return False
        
        try:
            message_data = {
                'type': 'send',
                'room_code': self.room_code,
                'message': {
                    'type': 'skill',
                    'data': skill_data
                }
            }
            
            response = requests.post(
                f"{self.server_url}/relay",
                json=message_data,
                timeout=3
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 發送技能失敗: {e}")
            return False
    
    def _poll_loop(self):
        """輪詢新訊息"""
        while self.connected:
            try:
                # 輪詢新訊息
                poll_data = {
                    'type': 'poll',
                    'room_code': self.room_code,
                    'last_index': self.last_message_index
                }
                
                response = requests.post(
                    f"{self.server_url}/relay",
                    json=poll_data,
                    timeout=3
                )
                
                if response.status_code == 200:
                    resp_data = response.json()
                    messages = resp_data.get('messages', [])
                    
                    # 處理新訊息
                    for msg in messages:
                        self._handle_message(msg)
                    
                    # 更新索引
                    self.last_message_index = resp_data.get('index', self.last_message_index)
                
                # 輪詢間隔（1 秒）
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ 輪詢錯誤: {e}")
                time.sleep(2)  # 錯誤時等待更久
    
    def _handle_message(self, msg):
        """處理接收到的訊息"""
        msg_type = msg.get('type')
        
        if msg_type == 'members':
            # 成員列表更新
            members = msg.get('members', [])
            self.members_callback(members)
            
        elif msg_type == 'skill':
            # 技能數據
            skill_data = msg.get('data', {})
            self.skill_callback(skill_data)
        
        elif msg_type == 'room_disbanded':
            # 房間解散
            print("⚠️ 房主已離開，房間已解散")
            self.connected = False
            # 這裡可以通知 UI 房間已解散
    
    def disconnect(self):
        """斷線"""
        if self.connected and self.server_url:
            try:
                # 發送離開通知
                leave_data = {
                    'type': 'leave',
                    'room_code': self.room_code,
                    'player_name': self.player_name
                }
                requests.post(f"{self.server_url}/relay", json=leave_data, timeout=2)
                print(f"👋 已離開房間 {self.room_code}")
            except Exception as e:
                print(f"⚠️ 發送離開通知失敗: {e}")
        
        self.connected = False
        # 等待輪詢線程結束
        if self.poll_thread:
            self.poll_thread.join(timeout=2)


def test_relay_http():
    """測試 HTTP 中繼客戶端"""
    def skill_cb(data):
        print(f"收到技能: {data}")
    
    def members_cb(members):
        print(f"成員更新: {members}")
    
    client = RelayClientHTTP("TEST123", "玩家1", skill_cb, members_cb)
    
    if client.connect():
        print("\n連線成功，等待 5 秒...")
        time.sleep(5)
        
        print("\n發送測試技能...")
        client.send_skill({
            'type': 'skill',
            'skill_id': 'test',
            'player': '玩家1'
        })
        
        print("\n等待 5 秒...")
        time.sleep(5)
        
        client.disconnect()
        print("\n測試完成")
    else:
        print("\n連線失敗")


if __name__ == '__main__':
    test_relay_http()
