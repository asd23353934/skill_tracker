"""
網路管理模組
處理房間創建、加入、技能同步等網路功能
支援自動 UPnP 端口映射，實現跨網路連線
"""

import json
import socket
import socketserver
import threading
import time
from src.core.ip_encoder import create_room_code, decode_room_code, RoomCodeGenerator


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
        self.upnp_manager = None
        self.use_external_ip = False
        
        # 中繼模式
        self.relay_client = None
        self.use_relay = False
    
    def create_room(self, try_upnp=True):
        """創建新房間（強制使用外網 IP）
        
        Args:
            try_upnp: 是否嘗試 UPnP 端口映射
        
        Returns:
            成功返回房間代碼，失敗返回 None
        """
        try:
            generator = RoomCodeGenerator()
            local_ip = generator.get_local_ip()
            external_ip = None
            upnp_success = False
            
            print("\n" + "="*60)
            print("🌐 創建跨網路房間")
            print("="*60)
            
            # Step 1: 獲取外網 IP（必需）
            print("\n📡 Step 1: 獲取外網 IP")
            external_ip = self._get_external_ip_reliable()
            
            if not external_ip:
                print("\n❌ 無法獲取外網 IP，房間創建失敗")
                print("   請檢查網路連線")
                return None
            
            print(f"✅ 外網 IP: {external_ip}")
            print(f"   內網 IP: {local_ip}")
            
            # Step 2: 嘗試 UPnP 自動端口映射
            if try_upnp:
                print("\n🔧 Step 2: 嘗試 UPnP 自動端口映射")
                try:
                    from src.core.upnp_manager import UPnPManager
                    
                    self.upnp_manager = UPnPManager(port=9999)
                    upnp_success = self.upnp_manager.add_port_mapping()
                    
                    if upnp_success:
                        print("\n✅ UPnP 自動設定成功！")
                        print("   端口映射已自動配置")
                        self.use_external_ip = True
                    else:
                        print("\n⚠️ UPnP 自動設定失敗")
                        self.use_external_ip = False
                        self._show_manual_setup_guide(external_ip, local_ip)
                        
                except ImportError:
                    print("\n⚠️ UPnP 模組未安裝")
                    print("   安裝方式: pip install miniupnpc")
                    self.use_external_ip = False
                    self._show_manual_setup_guide(external_ip, local_ip)
                except Exception as e:
                    print(f"\n⚠️ UPnP 錯誤: {e}")
                    self.use_external_ip = False
                    self._show_manual_setup_guide(external_ip, local_ip)
            else:
                print("\n⚠️ 已跳過 UPnP 自動設定")
                self.use_external_ip = False
                self._show_manual_setup_guide(external_ip, local_ip)
            
            # Step 3: 使用外網 IP 生成房間代碼
            print("\n🔑 Step 3: 生成房間代碼")
            ip_code = generator.encode_ip_to_base32(external_ip)
            if not ip_code:
                print("❌ IP 編碼失敗")
                return None
            
            self.host_ip = external_ip
            
            # 生成完整房間代碼
            import hashlib
            import uuid
            
            timestamp = int(time.time())
            time_code = ''
            for _ in range(4):
                time_code = generator.BASE32_CHARS[timestamp % 32] + time_code
                timestamp //= 32
            
            uuid_str = str(uuid.uuid4()).replace('-', '')
            uuid_hash = hashlib.md5(uuid_str.encode()).hexdigest()
            uuid_code = ''
            for i in range(4):
                byte_val = int(uuid_hash[i*2:i*2+2], 16)
                uuid_code += generator.BASE32_CHARS[byte_val % 32]
            
            self.room_code = f"{ip_code}-{time_code}-{uuid_code}"
            self.is_host = True
            self.members = []
            
            # Step 4: 啟動伺服器
            print("\n🚀 Step 4: 啟動伺服器")
            self.server = SkillServer(self.skill_callback, self._on_member_update)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            
            print(f"✅ 伺服器已啟動在端口 9999")
            
            # 總結
            print("\n" + "="*60)
            print("📊 房間創建成功")
            print("="*60)
            print(f"房間代碼: {self.room_code}")
            print(f"外網 IP:  {self.host_ip}")
            print(f"內網 IP:  {local_ip}")
            print(f"端口:     9999")
            
            if upnp_success:
                print(f"\n✅ 狀態: 跨網路連線已啟用（UPnP 自動）")
                print(f"   任何網路的玩家都可以加入")
            else:
                print(f"\n⚠️ 狀態: 需要手動設定端口轉發")
                print(f"   請按照上方指示設定路由器")
                print(f"   或者只允許同網路玩家加入")
            
            print("="*60 + "\n")
            
            return self.room_code
            
        except Exception as e:
            print(f"\n❌ 創建房間失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_external_ip_reliable(self):
        """可靠地獲取外網 IP（多個備用源）"""
        sources = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ifconfig.me/ip',
            'https://ident.me',
            'https://api.my-ip.io/ip',
        ]
        
        import requests
        
        for source in sources:
            try:
                response = requests.get(source, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    # 驗證 IP 格式
                    parts = ip.split('.')
                    if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
                        return ip
            except:
                continue
        
        return None
    
    def _show_manual_setup_guide(self, external_ip, local_ip):
        """顯示手動設定指引"""
        print("\n" + "📖 手動設定指引".center(60, "="))
        print("\n由於 UPnP 自動設定失敗，請手動設定路由器端口轉發：")
        print("\n【步驟 1】登入路由器")
        print("   1. 瀏覽器打開: http://192.168.1.1")
        print("   2. 輸入管理員帳號密碼")
        print("\n【步驟 2】找到端口轉發設定")
        print("   名稱可能是：")
        print("   - 端口轉發 (Port Forwarding)")
        print("   - 虛擬伺服器 (Virtual Server)")
        print("   - NAT 設定")
        print("\n【步驟 3】新增轉發規則")
        print(f"   服務名稱: SkillTracker")
        print(f"   外部端口: 9999")
        print(f"   內部 IP:  {local_ip}")
        print(f"   內部端口: 9999")
        print(f"   協定:     TCP")
        print("\n【步驟 4】開放防火牆")
        print("   Windows: 控制台 → 防火牆 → 允許應用程式")
        print("   端口: 9999 (TCP)")
        print("\n【步驟 5】測試連線")
        print(f"   訪問: http://www.yougetsignal.com/tools/open-ports/")
        print(f"   輸入外網 IP 和端口 9999 檢查是否開放")
        print("\n" + "="*60)
        print("💡 詳細教學請參考: NETWORK_SETUP.md")
        print("="*60 + "\n")
    
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
            
            # 發送加入訊息
            join_msg = json.dumps({'type': 'join', 'player': player_name}) + '\n'
            self.client.send(join_msg.encode())
            
            # 啟動接收訊息的線程
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
    
    def leave_room(self):
        """離開當前房間"""
        if self.client:
            try:
                leave_msg = json.dumps({'type': 'leave'}) + '\n'
                self.client.send(leave_msg.encode())
                self.client.close()
            except Exception as e:
                print(f"❌ 離開房間錯誤: {e}")
        
        # 清理 UPnP 端口映射
        if self.is_host and self.upnp_manager:
            print("🧹 清理 UPnP 端口映射...")
            self.upnp_manager.remove_port_mapping()
            self.upnp_manager = None
        
        if self.server:
            try:
                self.server.shutdown()
            except:
                pass
            self.server = None
            
        self.client = None
        self.room_code = None
        self.is_host = False
        self.members = []
        self.use_external_ip = False
    
    def broadcast_skill(self, skill_data):
        """廣播技能使用訊息
        
        Args:
            skill_data: 技能資料字典
        """
        # 中繼模式
        if self.use_relay and self.relay_client:
            self.relay_client.send_skill(skill_data)
            return
        
        # P2P 模式
        message = json.dumps(skill_data)
        if not message.endswith('\n'):
            message += '\n'
            
        if self.is_host and self.server:
            self.server.broadcast(message)
        elif self.client:
            try:
                self.client.send(message.encode())
            except Exception as e:
                print(f"❌ 發送技能失敗: {e}")
    
    def _on_member_update(self, members):
        """成員更新內部回調"""
        self.members = members
        self.members_callback(members)
    
    def _receive_messages(self):
        """接收網路訊息（客戶端）"""
        print("📡 開始接收訊息...")
        buffer = ""
        
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    print("⚠️ 伺服器斷線")
                    break
                
                buffer += data
                
                # 使用換行符分隔多個 JSON 訊息
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        msg = json.loads(line)
                        msg_type = msg.get('type')
                        print(f"📨 收到訊息類型: {msg_type}")
                        
                        if msg_type == 'members':
                            members = msg.get('members', [])
                            print(f"👥 成員更新: {members}")
                            self.members = members
                            self.members_callback(self.members)
                            
                        elif msg_type == 'skill':
                            print(f"🎮 收到技能: {msg.get('skill_id')}")
                            self.skill_callback(msg)
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 解析錯誤: {e}, 內容: {line[:50]}")
                        
            except Exception as e:
                print(f"❌ 接收訊息錯誤: {e}")
                break
        
        print("📡 停止接收訊息")


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
        dead_clients = []
        print(f"📢 廣播訊息給 {len(self.clients)} 個客戶端")
        
        # 確保訊息以換行符結尾（用於分隔多個 JSON）
        if not message.endswith('\n'):
            message += '\n'
        
        for client in list(self.clients.keys()):
            try:
                client.send(message.encode())
                print(f"  ✅ 發送到: {self.clients[client]}")
            except Exception as e:
                print(f"  ❌ 發送失敗: {self.clients.get(client, 'Unknown')} - {e}")
                dead_clients.append(client)
        
        # 清理斷線客戶端
        for client in dead_clients:
            if client in self.clients:
                del self.clients[client]
        
        if dead_clients:
            print(f"🧹 清理 {len(dead_clients)} 個斷線客戶端")
            self.update_members()
    
    def update_members(self):
        """更新成員列表"""
        members = list(self.clients.values())
        print(f"👥 更新成員列表: {members}")
        
        members_msg = json.dumps({'type': 'members', 'members': members})
        self.broadcast(members_msg)
        
        # 通知主機的回調
        self.skill_handler_members_callback(members)


class SkillHandler(socketserver.BaseRequestHandler):
    """處理單個客戶端連線"""
    
    def handle(self):
        player_name = None
        client_addr = self.client_address
        buffer = ""
        print(f"🔗 新客戶端連線: {client_addr}")
        
        while True:
            try:
                data = self.request.recv(1024).decode()
                if not data:
                    print(f"📡 客戶端 {client_addr} 斷線（無數據）")
                    break
                
                buffer += data
                
                # 使用換行符分隔多個 JSON 訊息
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        msg = json.loads(line)
                        msg_type = msg.get('type')
                        print(f"📨 收到訊息: {msg_type} from {client_addr}")
                        
                        if msg_type == 'join':
                            player_name = msg.get('player', 'Unknown')
                            self.server.clients[self.request] = player_name
                            print(f"✅ 玩家加入: {player_name} ({client_addr})")
                            print(f"   當前成員: {list(self.server.clients.values())}")
                            self.server.update_members()
                            
                        elif msg_type == 'leave':
                            print(f"👋 玩家離開: {player_name} ({client_addr})")
                            break
                            
                        elif msg_type == 'skill':
                            print(f"🎮 技能廣播: {msg.get('skill_id')} from {player_name}")
                            # 廣播給其他客戶端
                            self.server.broadcast(line + '\n')
                            # 通知主機
                            self.server.skill_handler_callback(msg)
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 解析錯誤: {e}, 內容: {line[:50]}")
                        
            except Exception as e:
                print(f"❌ 處理訊息錯誤: {e}")
                break
        
        # 清理斷線客戶端
        if self.request in self.server.clients:
            del self.server.clients[self.request]
            print(f"🧹 清理客戶端: {client_addr}")
            self.server.update_members()


    def create_room_relay(self, player_name):
        """使用中繼伺服器創建房間（100% 免設定）"""
        try:
            print("\n" + "="*60)
            print("🌐 使用中繼伺服器模式（免設定）")
            print("="*60)
            
            import random
            import string
            
            self.room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.is_host = True
            self.use_relay = True
            
            print(f"\n🔑 房間代碼: {self.room_code}")
            print(f"🔗 連線到中繼伺服器...")
            
            from src.core.relay_client import RelayClient
            
            self.relay_client = RelayClient(
                self.room_code,
                player_name,
                self.skill_callback,
                self._on_members_update
            )
            
            if self.relay_client.connect():
                print(f"\n✅ 中繼房間創建成功")
                print(f"   房間代碼: {self.room_code}")
                print(f"   模式: 中繼伺服器（免設定）")
                print("="*60 + "\n")
                return self.room_code
            else:
                print(f"\n❌ 中繼伺服器連線失敗")
                return None
        except Exception as e:
            print(f"\n❌ 創建中繼房間失敗: {e}")
            return None
    
    def join_room_relay(self, room_code, player_name):
        """使用中繼伺服器加入房間"""
        try:
            print(f"\n🔗 透過中繼伺服器加入: {room_code}")
            
            self.room_code = room_code
            self.is_host = False
            self.use_relay = True
            
            from src.core.relay_client import RelayClient
            
            self.relay_client = RelayClient(
                room_code,
                player_name,
                self.skill_callback,
                self._on_members_update
            )
            
            return self.relay_client.connect()
        except Exception as e:
            print(f"❌ 加入中繼房間錯誤: {e}")
            return False
