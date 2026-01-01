"""
IP 編碼模組
將 IP 地址編碼為房間代碼，並支援解碼
不需要中央伺服器，完全 P2P
"""

import socket
import hashlib


class IPEncoder:
    """IP 編碼器（可逆）"""
    
    # 自訂編碼表（排除易混淆字符: 0,O,1,I,L）
    ENCODE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    
    # 簡單的異或密鑰（混淆用）
    XOR_KEY = 0xA5  # 10100101
    
    def get_local_ip(self):
        """獲取本機 IP 地址
        
        Returns:
            str: IP 地址，如果獲取失敗返回 '127.0.0.1'
        """
        try:
            # 創建一個 UDP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 連接到外部地址（不會真的發送數據）
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            # 如果無法獲取，嘗試其他方法
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                # 避免返回 127.0.0.1
                if ip != '127.0.0.1':
                    return ip
            except:
                pass
            return '127.0.0.1'
    
    def encode_ip(self, ip):
        """將 IP 地址編碼為 8 位房間代碼
        
        Args:
            ip: IP 地址字符串 (例如: "192.168.1.100")
        
        Returns:
            str: 8 位房間代碼 (例如: "AB7K9M2X")
        """
        try:
            # 將 IP 轉為 4 個數字
            parts = ip.split('.')
            if len(parts) != 4:
                return None
            
            # 轉為整數並異或加密
            bytes_data = []
            for part in parts:
                num = int(part)
                encrypted = num ^ self.XOR_KEY
                bytes_data.append(encrypted)
            
            # 添加校驗碼（簡單的和校驗）
            checksum = sum(bytes_data) % 256
            bytes_data.append(checksum)
            
            # 轉為 base32 編碼（5 bytes → 8 chars）
            code = self._bytes_to_code(bytes_data)
            
            return code
        except Exception as e:
            print(f"編碼錯誤: {e}")
            return None
    
    def decode_code(self, room_code):
        """將房間代碼解碼為 IP 地址
        
        Args:
            room_code: 8 位房間代碼
        
        Returns:
            str: IP 地址，失敗返回 None
        """
        try:
            # 驗證長度
            if len(room_code) != 8:
                return None
            
            # 解碼為字節
            bytes_data = self._code_to_bytes(room_code)
            if not bytes_data or len(bytes_data) != 5:
                return None
            
            # 驗證校驗碼
            checksum = sum(bytes_data[:4]) % 256
            if checksum != bytes_data[4]:
                print("校驗碼錯誤")
                return None
            
            # 異或解密並組成 IP
            ip_parts = []
            for encrypted in bytes_data[:4]:
                num = encrypted ^ self.XOR_KEY
                if num > 255:
                    return None
                ip_parts.append(str(num))
            
            return '.'.join(ip_parts)
        except Exception as e:
            print(f"解碼錯誤: {e}")
            return None
    
    def _bytes_to_code(self, bytes_data):
        """將字節數組轉為代碼
        
        Args:
            bytes_data: 字節數組 (5 bytes)
        
        Returns:
            str: 8 位代碼
        """
        # 將 5 個字節轉為一個大整數
        value = 0
        for byte in bytes_data:
            value = (value << 8) | byte
        
        # 轉為 base-32 編碼
        code = ''
        base = len(self.ENCODE_CHARS)
        for _ in range(8):
            code = self.ENCODE_CHARS[value % base] + code
            value //= base
        
        return code
    
    def _code_to_bytes(self, code):
        """將代碼轉為字節數組
        
        Args:
            code: 8 位代碼
        
        Returns:
            list: 字節數組 (5 bytes)
        """
        # 驗證字符合法性
        for char in code:
            if char not in self.ENCODE_CHARS:
                print(f"非法字符: {char}")
                return None
        
        # base-32 解碼為整數
        value = 0
        base = len(self.ENCODE_CHARS)
        for char in code:
            value = value * base + self.ENCODE_CHARS.index(char)
        
        # 轉為 5 個字節
        bytes_data = []
        for _ in range(5):
            bytes_data.insert(0, value & 0xFF)
            value >>= 8
        
        return bytes_data
    
    def create_room_code(self):
        """創建房間代碼（包含本機 IP）
        
        Returns:
            dict: {'code': 房間代碼, 'ip': IP地址}
        """
        ip = self.get_local_ip()
        code = self.encode_ip(ip)
        
        if not code:
            # 編碼失敗，使用備用方案
            import time
            code = hashlib.md5(f"{ip}{time.time()}".encode()).hexdigest()[:8].upper()
        
        return {
            'code': code,
            'ip': ip
        }


# 全局實例
_encoder = IPEncoder()


def create_room_code():
    """創建房間代碼（便捷函數）
    
    Returns:
        dict: {'code': 房間代碼, 'ip': IP地址}
    """
    return _encoder.create_room_code()


def decode_room_code(code):
    """解碼房間代碼為 IP（便捷函數）
    
    Args:
        code: 房間代碼
    
    Returns:
        str: IP 地址，失敗返回 None
    """
    return _encoder.decode_code(code)


def get_local_ip():
    """獲取本機 IP（便捷函數）
    
    Returns:
        str: IP 地址
    """
    return _encoder.get_local_ip()


if __name__ == '__main__':
    # 測試
    encoder = IPEncoder()
    
    # 測試 1: 本機 IP
    ip = encoder.get_local_ip()
    print(f"本機 IP: {ip}")
    
    # 測試 2: 編碼/解碼
    test_ips = [
        '192.168.1.100',
        '10.0.0.1',
        '172.16.0.50',
        '127.0.0.1'
    ]
    
    print("\n編碼/解碼測試:")
    for test_ip in test_ips:
        code = encoder.encode_ip(test_ip)
        decoded = encoder.decode_code(code)
        status = "✅" if decoded == test_ip else "❌"
        print(f"{status} IP: {test_ip} → 代碼: {code} → 解碼: {decoded}")
    
    # 測試 3: 創建房間
    print("\n創建房間測試:")
    room_info = create_room_code()
    print(f"房間代碼: {room_info['code']}")
    print(f"IP 地址: {room_info['ip']}")
    
    decoded_ip = decode_room_code(room_info['code'])
    print(f"解碼驗證: {decoded_ip}")
    print(f"結果: {'✅ 成功' if decoded_ip == room_info['ip'] else '❌ 失敗'}")
