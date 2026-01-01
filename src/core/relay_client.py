"""
中繼伺服器客戶端
用於 NAT 穿透失敗時的備用方案
"""

import socket
import json
import threading
import time


class RelayClient:
    """中繼伺服器客戶端"""
    
    # 公開中繼伺服器列表（可以自架或使用免費服務）
    RELAY_SERVERS = [
        # 主要伺服器（需要自己架設）
        # ('relay.yourdomain.com', 8888),
        
        # 備用：使用 ngrok 等服務
        # ('0.tcp.ngrok.io', 12345),
        
        # 測試用（本地）
        ('127.0.0.1', 8888),
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
        self.socket = None
        self.connected = False
        self.is_host = False
    
    def connect(self):
        """連線到中繼伺服器"""
        for host, port in self.RELAY_SERVERS:
            try:
                print(f"🔗 嘗試連線到中繼伺服器: {host}:{port}")
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5)
                self.socket.connect((host, port))
                
                # 發送房間信息
                init_msg = json.dumps({
                    'type': 'init',
                    'room_code': self.room_code,
                    'player_name': self.player_name
                }) + '\n'
                
                self.socket.send(init_msg.encode())
                
                # 接收回應
                response = self.socket.recv(1024).decode().strip()
                resp_data = json.loads(response)
                
                if resp_data.get('status') == 'ok':
                    self.connected = True
                    self.is_host = resp_data.get('is_host', False)
                    
                    print(f"✅ 已連線到中繼伺服器")
                    print(f"   房間: {self.room_code}")
                    print(f"   角色: {'主機' if self.is_host else '成員'}")
                    
                    # 啟動接收線程
                    threading.Thread(target=self._receive_loop, daemon=True).start()
                    
                    return True
                else:
                    print(f"❌ 中繼伺服器拒絕: {resp_data.get('message')}")
                    self.socket.close()
                    
            except Exception as e:
                print(f"❌ 連線失敗: {e}")
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                continue
        
        return False
    
    def send_skill(self, skill_data):
        """發送技能數據"""
        if not self.connected:
            return False
        
        try:
            msg = json.dumps({
                'type': 'skill',
                'room_code': self.room_code,
                'data': skill_data
            }) + '\n'
            
            self.socket.send(msg.encode())
            return True
        except Exception as e:
            print(f"❌ 發送技能失敗: {e}")
            self.connected = False
            return False
    
    def _receive_loop(self):
        """接收訊息循環"""
        buffer = ""
        
        while self.connected:
            try:
                data = self.socket.recv(4096).decode()
                if not data:
                    print("⚠️ 中繼伺服器斷線")
                    self.connected = False
                    break
                
                buffer += data
                
                # 處理多個訊息
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        msg = json.loads(line)
                        self._handle_message(msg)
                    except json.JSONDecodeError:
                        print(f"⚠️ JSON 解析失敗: {line[:50]}")
                        
            except Exception as e:
                print(f"❌ 接收錯誤: {e}")
                self.connected = False
                break
    
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
            
        elif msg_type == 'ping':
            # 心跳回應
            pong_msg = json.dumps({'type': 'pong'}) + '\n'
            self.socket.send(pong_msg.encode())
    
    def disconnect(self):
        """斷線"""
        self.connected = False
        if self.socket:
            try:
                leave_msg = json.dumps({
                    'type': 'leave',
                    'room_code': self.room_code
                }) + '\n'
                self.socket.send(leave_msg.encode())
                self.socket.close()
            except:
                pass


def test_relay():
    """測試中繼客戶端"""
    def skill_cb(data):
        print(f"收到技能: {data}")
    
    def members_cb(members):
        print(f"成員更新: {members}")
    
    client = RelayClient("TEST123", "玩家1", skill_cb, members_cb)
    
    if client.connect():
        print("連線成功，按 Enter 發送測試技能...")
        input()
        
        client.send_skill({
            'type': 'skill',
            'skill_id': 'test',
            'player': '玩家1'
        })
        
        print("等待 5 秒...")
        time.sleep(5)
        
        client.disconnect()
    else:
        print("連線失敗")


if __name__ == '__main__':
    test_relay()
