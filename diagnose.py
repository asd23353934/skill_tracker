"""
診斷腳本 - 檢查 NetworkManager 是否正確
"""

import sys
import os

print("=" * 60)
print("技能追蹤器診斷工具")
print("=" * 60)
print()

# 1. 檢查文件是否存在
print("[1] 檢查文件...")
files_to_check = [
    'src/core/network_manager.py',
    'src/core/relay_client_http.py',
    'src/ui/main_window.py'
]

for file in files_to_check:
    exists = os.path.exists(file)
    status = "✓" if exists else "✗"
    print(f"   {status} {file}")
    if exists:
        size = os.path.getsize(file)
        print(f"      大小: {size:,} bytes")

print()

# 2. 檢查是否能導入
print("[2] 檢查導入...")
try:
    from src.core.network_manager import NetworkManager
    print("   ✓ NetworkManager 導入成功")
except Exception as e:
    print(f"   ✗ NetworkManager 導入失敗: {e}")
    sys.exit(1)

print()

# 3. 檢查方法是否存在
print("[3] 檢查方法...")
nm = NetworkManager(None, None)
methods_to_check = [
    'create_room',
    'create_room_relay',
    'join_room',
    'join_room_relay',
    'broadcast_skill'
]

for method in methods_to_check:
    has_method = hasattr(nm, method)
    status = "✓" if has_method else "✗"
    print(f"   {status} {method}")

print()

# 4. 檢查 relay_client_http
print("[4] 檢查中繼客戶端...")
try:
    from src.core.relay_client_http import RelayClientHTTP
    print("   ✓ RelayClientHTTP 導入成功")
    
    # 檢查伺服器配置
    print(f"   伺服器列表: {RelayClientHTTP.RELAY_SERVERS}")
except Exception as e:
    print(f"   ✗ RelayClientHTTP 導入失敗: {e}")

print()

# 5. 測試創建實例
print("[5] 測試創建實例...")
try:
    def dummy_callback(*args, **kwargs):
        pass
    
    nm = NetworkManager(dummy_callback, dummy_callback)
    print("   ✓ NetworkManager 實例創建成功")
    
    # 嘗試訪問方法
    if hasattr(nm, 'create_room_relay'):
        print("   ✓ create_room_relay 方法可訪問")
    else:
        print("   ✗ create_room_relay 方法不存在！")
        print("   → 這就是問題所在！")
except Exception as e:
    print(f"   ✗ 創建實例失敗: {e}")

print()
print("=" * 60)
print("診斷完成")
print("=" * 60)
print()
print("如果看到 ✗ 標記，請:")
print("1. 完全刪除 __pycache__ 資料夾")
print("2. 刪除所有 .pyc 文件")
print("3. 重新解壓 SkillTracker_Relay_Only_Final.tar.gz")
print("4. 重新運行此診斷腳本")
print()
