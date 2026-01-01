#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
網路功能測試
測試房間創建、加入、成員更新、技能廣播
"""

import sys
import time
sys.path.insert(0, '/home/claude/SkillTracker')

from src.core.network_manager import NetworkManager


def test_server():
    """測試伺服器端"""
    print("=" * 60)
    print("伺服器端測試")
    print("=" * 60)
    
    received_skills = []
    members_list = []
    
    def skill_callback(skill_data):
        print(f"✅ 伺服器收到技能: {skill_data}")
        received_skills.append(skill_data)
    
    def members_callback(members):
        print(f"👥 成員更新: {members}")
        members_list.clear()
        members_list.extend(members)
    
    # 創建房間
    network = NetworkManager(skill_callback, members_callback)
    room_code = network.create_room()
    
    if room_code:
        print(f"\n✅ 房間創建成功")
        print(f"   房間代碼: {room_code}")
        print(f"   等待客戶端連線...")
        
        # 保持運行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  停止伺服器")
    else:
        print("❌ 房間創建失敗")


def test_client(room_code):
    """測試客戶端"""
    print("=" * 60)
    print("客戶端測試")
    print("=" * 60)
    
    received_skills = []
    members_list = []
    
    def skill_callback(skill_data):
        print(f"✅ 客戶端收到技能: {skill_data}")
        received_skills.append(skill_data)
    
    def members_callback(members):
        print(f"👥 成員更新: {members}")
        members_list.clear()
        members_list.extend(members)
    
    # 加入房間
    network = NetworkManager(skill_callback, members_callback)
    
    print(f"\n嘗試加入房間: {room_code}")
    success = network.join_room(room_code, "測試玩家")
    
    if success:
        print(f"\n✅ 成功加入房間")
        print(f"   等待 5 秒...")
        time.sleep(5)
        
        print(f"\n當前成員列表: {members_list}")
        
        # 測試技能廣播
        print("\n🎮 測試技能廣播...")
        network.broadcast_skill({
            'type': 'skill',
            'skill_id': 'test_skill',
            'player': '測試玩家',
            'timestamp': time.time()
        })
        
        print("等待 3 秒...")
        time.sleep(3)
        
        print(f"\n收到的技能: {received_skills}")
        
    else:
        print("❌ 加入房間失敗")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='網路功能測試')
    parser.add_argument('mode', choices=['server', 'client'], help='運行模式')
    parser.add_argument('--code', help='房間代碼（客戶端模式）')
    
    args = parser.parse_args()
    
    if args.mode == 'server':
        test_server()
    else:
        if not args.code:
            print("錯誤: 客戶端模式需要房間代碼")
            print("使用方式: python test_network.py client --code XXXXXXXX-XXXX-XXXX")
            sys.exit(1)
        test_client(args.code)
