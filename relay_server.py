"""
中繼伺服器 - HTTP 版本
支援 Render.com 部署
"""

import json
import threading
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class RelayServer:
    """中繼伺服器（HTTP API）"""
    
    def __init__(self, host='0.0.0.0', port=None):
        self.host = host
        self.port = port or int(os.environ.get('PORT', 8888))
        self.rooms = {}  # room_code -> {players: [], messages: []}
        self.lock = threading.Lock()
        self.http_server = None
    
    def start(self):
        """啟動伺服器"""
        print("="*60)
        print("🌐 中繼伺服器啟動中...")
        print("="*60)
        print(f"監聽地址: {self.host}:{self.port}")
        print("="*60)
        
        self.http_server = HTTPServer(
            (self.host, self.port),
            lambda *args: RelayHTTPHandler(self.rooms, self.lock, *args)
        )
        
        print("✅ HTTP 伺服器已啟動")
        print("="*60)
        
        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️  伺服器停止")


class RelayHTTPHandler(BaseHTTPRequestHandler):
    """HTTP 請求處理器"""
    
    def __init__(self, rooms, lock, *args):
        self.relay_rooms = rooms
        self.relay_lock = lock
        super().__init__(*args)
    
    def do_GET(self):
        """處理 GET 請求"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>技能追蹤器中繼伺服器</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .status {{ color: #28a745; font-size: 24px; }}
                    .info {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    h1 {{ color: #333; }}
                </style>
            </head>
            <body>
                <h1>🌐 技能追蹤器中繼伺服器</h1>
                <p class="status">✅ 伺服器運行中</p>
                
                <div class="info">
                    <h2>📊 狀態</h2>
                    <p>活躍房間: <strong>{rooms}</strong></p>
                    <p>連線數: <strong>{connections}</strong></p>
                </div>
            </body>
            </html>
            """.format(
                rooms=len(self.relay_rooms),
                connections=sum(len(room.get('players', [])) for room in self.relay_rooms.values())
            )
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                'status': 'ok',
                'rooms': len(self.relay_rooms),
                'connections': sum(len(room.get('players', [])) for room in self.relay_rooms.values())
            }
            
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """處理 POST 請求"""
        if self.path == '/relay':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                msg_type = data.get('type')
                
                if msg_type == 'init':
                    room_code = data.get('room_code')
                    player_name = data.get('player_name')
                    
                    with self.relay_lock:
                        if room_code not in self.relay_rooms:
                            self.relay_rooms[room_code] = {
                                'players': [player_name],
                                'messages': []
                            }
                            is_host = True
                        else:
                            self.relay_rooms[room_code]['players'].append(player_name)
                            is_host = False
                    
                    print(f"✅ {player_name} 加入房間 {room_code} {'(房主)' if is_host else ''}")
                    
                    response = {
                        'status': 'ok',
                        'is_host': is_host,
                        'room_code': room_code
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    
                elif msg_type == 'poll':
                    room_code = data.get('room_code')
                    last_index = data.get('last_index', 0)
                    
                    messages = []
                    with self.relay_lock:
                        if room_code in self.relay_rooms:
                            room = self.relay_rooms[room_code]
                            messages = room['messages'][last_index:]
                    
                    response = {
                        'status': 'ok',
                        'messages': messages,
                        'index': last_index + len(messages)
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    
                elif msg_type == 'send':
                    room_code = data.get('room_code')
                    message = data.get('message')
                    
                    with self.relay_lock:
                        if room_code in self.relay_rooms:
                            self.relay_rooms[room_code]['messages'].append(message)
                            print(f"📨 房間 {room_code} 收到訊息")
                    
                    response = {'status': 'ok'}
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                
                elif msg_type == 'leave':
                    room_code = data.get('room_code')
                    player_name = data.get('player_name')
                    
                    with self.relay_lock:
                        if room_code in self.relay_rooms:
                            room = self.relay_rooms[room_code]
                            players = room.get('players', [])
                            
                            # 檢查是否為房主（第一個玩家）
                            is_host = players and players[0] == player_name
                            
                            if is_host:
                                # 房主離開，解散房間
                                room['messages'].append({
                                    'type': 'room_disbanded',
                                    'message': '房主已離開，房間解散'
                                })
                                print(f"👑 房主 {player_name} 離開，房間 {room_code} 解散")
                                del self.relay_rooms[room_code]
                            else:
                                # 普通成員離開
                                if player_name in players:
                                    players.remove(player_name)
                                print(f"👋 {player_name} 離開房間 {room_code}")
                                
                                if len(players) == 0:
                                    del self.relay_rooms[room_code]
                                    print(f"🗑️ 房間 {room_code} 已清空")
                    
                    response = {'status': 'ok'}
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    
            except Exception as e:
                print(f"❌ 錯誤: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        """減少日誌輸出"""
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=None)
    args = parser.parse_args()
    
    server = RelayServer(host=args.host, port=args.port)
    server.start()


if __name__ == '__main__':
    main()