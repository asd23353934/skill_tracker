"""
中繼伺服器
用於 NAT 穿透失敗時轉發訊息
可以部署在雲端伺服器（如 Heroku, Railway, Render）
"""

import socket
import socketserver
import json
import threading
import time


class RelayServer:
    """中繼伺服器"""
    
    def __init__(self, host='0.0.0.0', port=8888):
        """初始化中繼伺服器
        
        Args:
            host: 監聽地址
            port: 監聽端口
        """
        self.host = host
        self.port = port
        self.rooms = {}  # room_code -> {clients: [], host: socket}
        self.lock = threading.Lock()
        self.server = None
    
    def start(self):
        """啟動伺服器"""
        print("="*60)
        print("🌐 中繼伺服器啟動中...")
        print("="*60)
        print(f"監聽地址: {self.host}:{self.port}")
        print("="*60)
        
        self.server = socketserver.ThreadingTCPServer(
            (self.host, self.port),
            RelayHandler
        )
        
        # 傳遞 rooms 和 lock 給 handler
        self.server.relay_rooms = self.rooms
        self.server.relay_lock = self.lock
        
        print("✅ 伺服器已啟動，等待連線...")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️  伺服器停止")
            self.server.shutdown()


class RelayHandler(socketserver.BaseRequestHandler):
    """處理單個客戶端連線"""
    
    def handle(self):
        """處理客戶端"""
        client_addr = self.client_address
        buffer = ""
        room_code = None
        player_name = None
        
        print(f"🔗 新連線: {client_addr}")
        
        try:
            while True:
                data = self.request.recv(4096).decode()
                if not data:
                    break
                
                buffer += data
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        msg = json.loads(line)
                        msg_type = msg.get('type')
                        
                        if msg_type == 'init':
                            # 初始化連線
                            room_code = msg.get('room_code')
                            player_name = msg.get('player_name')
                            
                            is_host = self._join_room(room_code, player_name, self.request)
                            
                            # 發送回應
                            response = json.dumps({
                                'status': 'ok',
                                'is_host': is_host,
                                'room_code': room_code
                            }) + '\n'
                            
                            self.request.send(response.encode())
                            
                            print(f"✅ {player_name} 加入房間 {room_code} {'(主機)' if is_host else ''}")
                            
                        elif msg_type == 'skill':
                            # 廣播技能
                            if room_code:
                                self._broadcast_skill(room_code, msg.get('data'), self.request)
                                
                        elif msg_type == 'leave':
                            # 離開房間
                            break
                            
                        elif msg_type == 'pong':
                            # 心跳回應
                            pass
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 錯誤: {e}")
                        
        except Exception as e:
            print(f"❌ 處理錯誤: {e}")
        finally:
            # 清理
            if room_code:
                self._leave_room(room_code, self.request, player_name)
            
            print(f"👋 斷線: {client_addr}")
    
    def _join_room(self, room_code, player_name, client_socket):
        """加入房間
        
        Returns:
            bool: 是否為主機
        """
        with self.server.relay_lock:
            if room_code not in self.server.relay_rooms:
                # 創建新房間
                self.server.relay_rooms[room_code] = {
                    'host': client_socket,
                    'clients': {client_socket: player_name},
                    'members': [player_name]
                }
                return True
            else:
                # 加入現有房間
                room = self.server.relay_rooms[room_code]
                room['clients'][client_socket] = player_name
                room['members'].append(player_name)
                
                # 廣播成員更新
                self._broadcast_members(room_code)
                
                return False
    
    def _leave_room(self, room_code, client_socket, player_name):
        """離開房間"""
        with self.server.relay_lock:
            if room_code not in self.server.relay_rooms:
                return
            
            room = self.server.relay_rooms[room_code]
            
            # 移除客戶端
            if client_socket in room['clients']:
                del room['clients'][client_socket]
                if player_name in room['members']:
                    room['members'].remove(player_name)
            
            # 如果房間空了，刪除房間
            if not room['clients']:
                del self.server.relay_rooms[room_code]
                print(f"🗑️  房間 {room_code} 已關閉")
            else:
                # 廣播成員更新
                self._broadcast_members(room_code)
    
    def _broadcast_members(self, room_code):
        """廣播成員列表"""
        if room_code not in self.server.relay_rooms:
            return
        
        room = self.server.relay_rooms[room_code]
        members = room['members']
        
        msg = json.dumps({
            'type': 'members',
            'members': members
        }) + '\n'
        
        # 發送給所有客戶端
        for client in list(room['clients'].keys()):
            try:
                client.send(msg.encode())
            except:
                pass
    
    def _broadcast_skill(self, room_code, skill_data, sender):
        """廣播技能數據"""
        if room_code not in self.server.relay_rooms:
            return
        
        room = self.server.relay_rooms[room_code]
        
        msg = json.dumps({
            'type': 'skill',
            'data': skill_data
        }) + '\n'
        
        # 發送給除了發送者之外的所有客戶端
        for client in list(room['clients'].keys()):
            if client != sender:
                try:
                    client.send(msg.encode())
                except:
                    pass


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='技能追蹤器中繼伺服器')
    parser.add_argument('--host', default='0.0.0.0', help='監聽地址')
    parser.add_argument('--port', type=int, default=8888, help='監聽端口')
    
    args = parser.parse_args()
    
    server = RelayServer(host=args.host, port=args.port)
    server.start()


if __name__ == '__main__':
    main()
