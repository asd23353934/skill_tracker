"""
房間代碼生成器
使用 UUID 風格的嚴謹代碼（16碼以上）
包含 IP 信息和唯一性保證
"""

import socket
import uuid
import hashlib
import time


class RoomCodeGenerator:
    """房間代碼生成器（UUID 風格）"""
    
    # 編碼字符集（Base32，排除易混淆字符）
    BASE32_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    
    def get_local_ip(self):
        """獲取本機 IP 地址
        
        Returns:
            str: IP 地址
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                if ip != '127.0.0.1':
                    return ip
            except:
                pass
            return '127.0.0.1'
    
    def encode_ip_to_base32(self, ip):
        """將 IP 編碼為 Base32 字符串
        
        Args:
            ip: IP 地址 (例如: "192.168.1.100")
        
        Returns:
            str: Base32 編碼的 IP（8碼）
        """
        try:
            # IP 轉為 4 字節
            parts = [int(p) for p in ip.split('.')]
            if len(parts) != 4:
                return None
            
            # 打包為 32 位整數
            ip_int = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
            
            # 轉為 Base32（7 個字符足夠表示 32 位）
            code = ''
            for _ in range(7):
                code = self.BASE32_CHARS[ip_int % 32] + code
                ip_int //= 32
            
            # 添加校驗位（第8位）
            checksum = sum(parts) % 32
            code += self.BASE32_CHARS[checksum]
            
            return code
        except Exception as e:
            print(f"IP編碼錯誤: {e}")
            return None
    
    def decode_base32_to_ip(self, code):
        """將 Base32 代碼解碼為 IP
        
        Args:
            code: 8 位 Base32 代碼
        
        Returns:
            str: IP 地址，失敗返回 None
        """
        try:
            if len(code) != 8:
                return None
            
            # 驗證字符
            for char in code:
                if char not in self.BASE32_CHARS:
                    return None
            
            # 解碼前 7 位
            ip_int = 0
            for char in code[:7]:
                ip_int = ip_int * 32 + self.BASE32_CHARS.index(char)
            
            # 提取 IP 各段
            parts = [
                (ip_int >> 24) & 0xFF,
                (ip_int >> 16) & 0xFF,
                (ip_int >> 8) & 0xFF,
                ip_int & 0xFF
            ]
            
            # 驗證校驗位
            expected_checksum = sum(parts) % 32
            actual_checksum = self.BASE32_CHARS.index(code[7])
            
            if expected_checksum != actual_checksum:
                print(f"校驗碼錯誤: 期望 {expected_checksum}, 實際 {actual_checksum}")
                return None
            
            return '.'.join(map(str, parts))
        except Exception as e:
            print(f"IP解碼錯誤: {e}")
            return None
    
    def generate_uuid_style_code(self):
        """生成 UUID 風格的房間代碼
        
        格式: XXXXXXXX-XXXX-XXXX
        - 前8位: IP 編碼
        - 中4位: 時間戳
        - 後4位: 隨機UUID
        
        Returns:
            dict: {'code': 房間代碼, 'ip': IP地址}
        """
        ip = self.get_local_ip()
        
        # Part 1: IP 編碼（8位）
        ip_code = self.encode_ip_to_base32(ip)
        if not ip_code:
            # 備用方案：隨機生成
            ip_code = self._generate_random_code(8)
        
        # Part 2: 時間戳（4位）
        timestamp = int(time.time())
        time_code = ''
        for _ in range(4):
            time_code = self.BASE32_CHARS[timestamp % 32] + time_code
            timestamp //= 32
        
        # Part 3: UUID 片段（4位）
        uuid_str = str(uuid.uuid4()).replace('-', '')
        uuid_hash = hashlib.md5(uuid_str.encode()).hexdigest()
        uuid_code = ''
        for i in range(4):
            byte_val = int(uuid_hash[i*2:i*2+2], 16)
            uuid_code += self.BASE32_CHARS[byte_val % 32]
        
        # 組合: XXXXXXXX-XXXX-XXXX (總共16碼 + 2個分隔符)
        code = f"{ip_code}-{time_code}-{uuid_code}"
        
        return {
            'code': code,
            'ip': ip,
            'ip_part': ip_code,
            'time_part': time_code,
            'uuid_part': uuid_code
        }
    
    def _generate_random_code(self, length):
        """生成隨機代碼
        
        Args:
            length: 代碼長度
        
        Returns:
            str: 隨機代碼
        """
        import random
        return ''.join(random.choice(self.BASE32_CHARS) for _ in range(length))
    
    def extract_ip_from_code(self, code):
        """從房間代碼提取 IP
        
        Args:
            code: 房間代碼 (格式: XXXXXXXX-XXXX-XXXX)
        
        Returns:
            str: IP 地址，失敗返回 None
        """
        try:
            # 移除分隔符
            parts = code.split('-')
            if len(parts) != 3:
                # 容錯：如果用戶沒輸入分隔符，取前8位
                if len(code) >= 8:
                    ip_code = code[:8]
                else:
                    return None
            else:
                ip_code = parts[0]
            
            # 解碼 IP 部分
            return self.decode_base32_to_ip(ip_code)
        except Exception as e:
            print(f"提取IP錯誤: {e}")
            return None


# 全局實例
_generator = RoomCodeGenerator()


def create_room_code():
    """創建房間代碼（便捷函數）
    
    Returns:
        dict: {'code': 房間代碼, 'ip': IP地址}
    """
    return _generator.generate_uuid_style_code()


def decode_room_code(code):
    """解碼房間代碼為 IP（便捷函數）
    
    Args:
        code: 房間代碼
    
    Returns:
        str: IP 地址，失敗返回 None
    """
    return _generator.extract_ip_from_code(code)


def get_local_ip():
    """獲取本機 IP（便捷函數）
    
    Returns:
        str: IP 地址
    """
    return _generator.get_local_ip()


if __name__ == '__main__':
    # 測試
    generator = RoomCodeGenerator()
    
    print("=" * 60)
    print("UUID 風格房間代碼測試")
    print("=" * 60)
    
    # 測試 1: 本機 IP
    ip = generator.get_local_ip()
    print(f"\n本機 IP: {ip}")
    
    # 測試 2: IP 編碼/解碼
    test_ips = [
        '192.168.1.100',
        '10.0.0.1',
        '172.16.0.50',
        '127.0.0.1',
        '8.8.8.8'
    ]
    
    print("\nIP 編碼/解碼測試:")
    print("-" * 60)
    for test_ip in test_ips:
        code = generator.encode_ip_to_base32(test_ip)
        if code:
            decoded = generator.decode_base32_to_ip(code)
            status = "✅" if decoded == test_ip else "❌"
            print(f"{status} IP: {test_ip:15} → {code:8} → {decoded}")
        else:
            print(f"❌ IP: {test_ip:15} → 編碼失敗")

    
    # 測試 3: UUID 風格代碼生成
    print("\nUUID 風格代碼生成測試:")
    print("-" * 60)
    for i in range(3):
        room_info = generator.generate_uuid_style_code()
        print(f"\n房間 {i+1}:")
        print(f"  完整代碼: {room_info['code']}")
        print(f"  IP 地址:  {room_info['ip']}")
        print(f"  IP 部分:  {room_info['ip_part']}")
        print(f"  時間部分: {room_info['time_part']}")
        print(f"  UUID部分: {room_info['uuid_part']}")
        
        # 驗證解碼
        decoded_ip = generator.extract_ip_from_code(room_info['code'])
        status = "✅" if decoded_ip == room_info['ip'] else "❌"
        print(f"  解碼驗證: {status} {decoded_ip}")
    
    # 測試 4: 不同格式輸入
    print("\n輸入格式容錯測試:")
    print("-" * 60)
    room_info = generator.generate_uuid_style_code()
    test_inputs = [
        room_info['code'],                          # 完整格式
        room_info['code'].replace('-', ''),         # 無分隔符
        room_info['ip_part'],                       # 只有IP部分
    ]
    
    for test_input in test_inputs:
        decoded = generator.extract_ip_from_code(test_input)
        status = "✅" if decoded == room_info['ip'] else "❌"
        print(f"{status} 輸入: {test_input:20} → {decoded}")
    
    print("\n" + "=" * 60)
