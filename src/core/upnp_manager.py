"""
UPnP 端口映射模組
自動設定路由器端口轉發，實現跨網路連線
"""

import socket
import struct
import time
import requests


class UPnPManager:
    """UPnP 管理器 - 自動端口映射"""
    
    def __init__(self, port=9999):
        """初始化 UPnP 管理器
        
        Args:
            port: 要映射的端口
        """
        self.port = port
        self.gateway_url = None
        self.control_url = None
        self.external_ip = None
        self.local_ip = None
    
    def get_local_ip(self):
        """獲取本機內網 IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def get_external_ip(self):
        """獲取外網 IP（多個備用源）"""
        sources = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ifconfig.me/ip',
            'https://ident.me',
        ]
        
        for source in sources:
            try:
                response = requests.get(source, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    print(f"✅ 從 {source} 獲取外網 IP: {ip}")
                    return ip
            except Exception as e:
                print(f"⚠️ {source} 失敗: {e}")
                continue
        
        print("❌ 無法獲取外網 IP")
        return None
    
    def discover_gateway(self):
        """發現路由器（UPnP SSDP）"""
        print("🔍 搜尋支援 UPnP 的路由器...")
        
        # SSDP 多播訊息
        ssdp_request = (
            'M-SEARCH * HTTP/1.1\r\n'
            'HOST: 239.255.255.250:1900\r\n'
            'MAN: "ssdp:discover"\r\n'
            'MX: 3\r\n'
            'ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n'
            '\r\n'
        ).encode()
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(5)
        
        try:
            sock.sendto(ssdp_request, ('239.255.255.250', 1900))
            
            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = data.decode('utf-8', errors='ignore')
                    
                    # 解析 LOCATION
                    for line in response.split('\r\n'):
                        if line.upper().startswith('LOCATION:'):
                            location = line.split(':', 1)[1].strip()
                            print(f"✅ 找到路由器: {location}")
                            self.gateway_url = location
                            return True
                            
                except socket.timeout:
                    break
                    
        except Exception as e:
            print(f"❌ UPnP 搜尋失敗: {e}")
        finally:
            sock.close()
        
        return False
    
    def add_port_mapping(self):
        """使用 miniupnpc 添加端口映射（更可靠）"""
        try:
            import miniupnpc
            
            print("🔧 使用 miniupnpc 設定端口映射...")
            
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            
            # 搜尋設備
            print("   搜尋 UPnP 設備...")
            devices = upnp.discover()
            print(f"   找到 {devices} 個設備")
            
            if devices == 0:
                print("❌ 未找到 UPnP 設備")
                return False
            
            # 選擇有效的 IGD
            try:
                upnp.selectigd()
            except Exception as e:
                print(f"❌ 選擇 IGD 失敗: {e}")
                return False
            
            # 獲取外網 IP
            try:
                self.external_ip = upnp.externalipaddress()
                print(f"   外網 IP: {self.external_ip}")
            except:
                print("⚠️ 無法從路由器獲取外網 IP，使用備用方法")
                self.external_ip = self.get_external_ip()
            
            # 獲取本機 IP
            self.local_ip = self.get_local_ip()
            print(f"   內網 IP: {self.local_ip}")
            
            # 刪除舊的映射（如果存在）
            try:
                upnp.deleteportmapping(self.port, 'TCP')
                print(f"   清理舊映射")
            except:
                pass
            
            # 添加端口映射
            # 參數順序：external_port, protocol, internal_host, internal_port, description, remote_host
            try:
                result = upnp.addportmapping(
                    self.port,              # 外部端口
                    'TCP',                  # 協定
                    self.local_ip,          # 內網 IP
                    self.port,              # 內部端口
                    'SkillTracker',         # 描述
                    ''                      # 遠程主機（空=任何）
                )
            except TypeError:
                # 某些版本的 miniupnpc 參數順序不同
                print("   嘗試備用參數格式...")
                result = upnp.addportmapping(
                    self.port,              # 外部端口
                    'TCP',                  # 協定
                    self.local_ip,          # 內網 IP
                    self.port,              # 內部端口
                    'SkillTracker',         # 描述
                    '',                     # 遠程主機
                    0                       # 租約時間（0=永久）
                )
            
            if result:
                print(f"✅ 端口映射成功！")
                print(f"   外部端口: {self.port}")
                print(f"   內部地址: {self.local_ip}:{self.port}")
                
                # 驗證映射
                try:
                    mappings = upnp.getgenericportmapping(0)
                    print(f"   驗證: {mappings}")
                except:
                    pass
                
                return True
            else:
                print("❌ 端口映射返回失敗")
                return False
                
        except ImportError:
            print("❌ 未安裝 miniupnpc")
            print("   請執行: pip install miniupnpc")
            return False
        except Exception as e:
            print(f"❌ miniupnpc 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_port_mapping(self):
        """移除端口映射"""
        try:
            import miniupnpc
            
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            upnp.discover()
            upnp.selectigd()
            
            upnp.deleteportmapping(self.port, 'TCP')
            print(f"✅ 已移除端口映射: {self.port}")
            return True
        except:
            return False
    
    def setup_automatic(self):
        """自動設定完整流程
        
        Returns:
            dict: {'success': bool, 'external_ip': str, 'local_ip': str}
        """
        print("=" * 60)
        print("🚀 自動設定跨網路連線")
        print("=" * 60)
        
        # Step 1: 獲取外網 IP
        print("\n📡 Step 1: 獲取外網 IP")
        self.external_ip = self.get_external_ip()
        
        if not self.external_ip:
            print("⚠️ 無法獲取外網 IP，將使用內網模式")
            self.external_ip = self.get_local_ip()
        
        # Step 2: 嘗試 UPnP 端口映射
        print("\n🔧 Step 2: 設定 UPnP 端口映射")
        upnp_success = self.add_port_mapping()
        
        if not upnp_success:
            print("\n⚠️ UPnP 自動設定失敗，可能原因：")
            print("   1. 路由器不支援 UPnP")
            print("   2. UPnP 功能被關閉")
            print("   3. 未安裝 miniupnpc 套件")
            print("\n💡 解決方案：")
            print("   - 安裝: pip install miniupnpc")
            print("   - 或手動設定端口轉發（參考 NETWORK_SETUP.md）")
            print("   - 或使用同一網路連線（最簡單）")
        
        # Step 3: 總結
        print("\n" + "=" * 60)
        print("📊 設定結果")
        print("=" * 60)
        
        result = {
            'success': upnp_success,
            'external_ip': self.external_ip,
            'local_ip': self.get_local_ip(),
            'port': self.port,
            'upnp_available': upnp_success
        }
        
        if upnp_success:
            print(f"✅ 跨網路連線已啟用")
            print(f"   外網 IP: {result['external_ip']}")
            print(f"   內網 IP: {result['local_ip']}")
            print(f"   端口: {result['port']}")
            print(f"\n💡 其他玩家可以從任何網路連線到你的房間")
        else:
            print(f"⚠️ 目前僅支援同網路連線")
            print(f"   內網 IP: {result['local_ip']}")
            print(f"   端口: {result['port']}")
            print(f"\n💡 只有同一 WiFi 的玩家可以加入")
        
        return result


def test_upnp():
    """測試 UPnP 功能"""
    manager = UPnPManager(port=9999)
    result = manager.setup_automatic()
    
    if result['success']:
        print("\n⏸️  按 Enter 移除端口映射...")
        input()
        manager.remove_port_mapping()
    
    return result


if __name__ == '__main__':
    test_upnp()
