"""
中繼伺服器 - WebSocket 版本
支援在 Render、Railway、Heroku 等平台部署
同時支援原始 TCP 和 WebSocket 連線
"""

import socket
import socketserver
import json
import threading
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class RelayServer:
    """中繼伺服器（WebSocket + TCP）"""
    
    def __init__(self, host='0.0.0.0', port=None):
        """初始化中繼伺服器
        
        Args:
            host: 監聽地址
            port: 監聽端口（None 則從環境變數讀取）
        """
        self.host = host
        self.port = port or int(os.environ.get('PORT', 8888))
        self.rooms = {}  # room_code -> {clients: [], host: socket}
        self.lock = threading.Lock()
        self.tcp_server = None
        self.http_server = None
    
    def start(self):
        """啟動伺服器"""
        print("="*60)
        print("🌐 中繼伺服器啟動中...")
        print("="*60)
        print(f"監聽地址: {self.host}:{self.port}")
        print(f"環境: {'Production' if os.environ.get('PORT') else 'Development'}")
        print("="*60)
        
        # 啟動 HTTP 伺服器（用於健康檢查和 WebSocket）
        self.http_server = HTTPServer(
            (self.host, self.port),
            lambda *args: RelayHTTPHandler(self.rooms, self.lock, *args)
        )
        
        print("✅ HTTP 伺服器已啟動")
        print(f"   訪問: http://localhost:{self.port}")
        print("   支援: HTTP API + WebSocket")
        print("="*60)
        
        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️  伺服器停止")
            self.http_server.shutdown()


class RelayHTTPHandler(BaseHTTPRequestHandler):
    """HTTP 請求處理器"""
    
    def __init__(self, rooms, lock, *args):
        self.relay_rooms = rooms
        self.relay_lock = lock
        super().__init__(*args)
    
    def do_GET(self):
        """處理 GET 請求（健康檢查）"""
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
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #f5f5f5;
                    }
                    .status { color: #28a745; }
                    .info { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
                    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
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
                
                <div class="info">
                    <h2>🔧 客戶端配置</h2>
                    <p>在 <code>src/core/relay_client.py</code> 中設定:</p>
                    <pre style="background: #f0f0f0; padding: 15px; border-radius: 5px;">
RELAY_SERVERS = [
    ('{host}', {port}),
]</pre>
                </div>
                
                <div class="info">
                    <h2>📡 API 端點</h2>
                    <ul>
                        <li><code>GET /</code> - 健康檢查（本頁面）</li>
                        <li><code>GET /status</code> - JSON 狀態</li>
                        <li><code>POST /relay</code> - 中繼 API</li>
                    </ul>
                </div>
            </body>
            </html>
            """.format(
                rooms=len(self.relay_rooms),
                connections=sum(len(room.get('clients', {})) for room in self.relay_rooms.values()),
                host=self.server.server_address[0],
                port=self.server.server_address[1]
            )
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                'status': 'ok',
                'rooms': len(self.relay_rooms),
                'connections': sum(len(room.get('clients', {})) for room in self.relay_rooms.values()),
                'uptime': time.time()
            }
            
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """處理 POST 請求（中繼 API）"""
        if self.path == '/relay':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                msg_type = data.get('type')
                
                if msg_type == 'init':
                    # 創建/加入房間
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
                    # 輪詢新訊息
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
                    # 發送訊息
                    room_code = data.get('room_code')
                    message = data.get('message')
                    
                    with self.relay_lock:
                        if room_code in self.relay_rooms:
                            self.relay_rooms[room_code]['messages'].append(message)
                    
                    response = {'status': 'ok'}
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        """禁用訪問日誌（減少輸出）"""
        pass


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='技能追蹤器中繼伺服器')
    parser.add_argument('--host', default='0.0.0.0', help='監聽地址')
    parser.add_argument('--port', type=int, default=None, help='監聽端口')
    
    args = parser.parse_args()
    
    server = RelayServer(host=args.host, port=args.port)
    server.start()


if __name__ == '__main__':
    main()
