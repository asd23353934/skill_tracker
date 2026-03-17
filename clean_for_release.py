#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
發布前清理腳本
自動清理配置，恢復初始狀態
"""

import json
import os
import shutil

def clean_config_json():
    """清理 config.json 到初始狀態"""
    print("🧹 清理 config.json...")
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 恢復 settings 到初始狀態
        config['settings'] = {
            "player_name": "玩家1",
            "skill_start_x": 400,
            "skill_start_y": 400,
            "enable_sound": True,
            "skill_send": {},
            "skill_receive": {},
            "skill_permanent": {},
            "current_profile": "預設配置"
        }

        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print("  ✅ config.json 已恢復初始狀態")
        return True
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return False

def clean_profiles_dir():
    """清理 profiles 資料夾，只保留預設配置"""
    print("\n🧹 清理 profiles/ 資料夾...")
    
    if not os.path.exists('profiles'):
        os.makedirs('profiles')
        print("  ✅ 創建 profiles/ 資料夾")
    
    # 獲取所有配置文件
    files = [f for f in os.listdir('profiles') if f.endswith('.json')]
    
    # 刪除非預設配置
    deleted = []
    for file in files:
        if file != '預設配置.json':
            os.remove(os.path.join('profiles', file))
            deleted.append(file)
    
    if deleted:
        print(f"  ✅ 已刪除 {len(deleted)} 個測試配置: {', '.join(deleted)}")
    else:
        print("  ✅ 沒有需要刪除的配置")
    
    # 確保預設配置存在且為空
    default_profile = {
        'hotkeys': {},
        'send': {},
        'receive': {},
        'permanent': {},
        'cooldown_overrides': {}
    }
    
    with open('profiles/預設配置.json', 'w', encoding='utf-8') as f:
        json.dump(default_profile, f, ensure_ascii=False, indent=2)
    
    print("  ✅ 預設配置已重置為空")
    return True

def remove_pycache():
    """刪除 __pycache__ 資料夾"""
    print("\n🧹 清理 __pycache__...")
    
    count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))
            count += 1
    
    if count > 0:
        print(f"  ✅ 已刪除 {count} 個 __pycache__ 資料夾")
    else:
        print("  ✅ 沒有 __pycache__ 需要刪除")
    
    return True

def remove_build_files():
    """刪除打包產生的檔案"""
    print("\n🧹 清理打包檔案...")
    
    dirs_to_remove = ['build', 'dist']
    removed = []
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            removed.append(dir_name)
    
    if removed:
        print(f"  ✅ 已刪除: {', '.join(removed)}")
    else:
        print("  ✅ 沒有打包檔案需要刪除")
    
    return True

def main():
    """主函數"""
    print("=" * 60)
    print("🧹 技能追蹤器 - 發布前清理")
    print("=" * 60)
    print()
    
    # 執行清理
    results = {
        'config.json': clean_config_json(),
        'profiles/': clean_profiles_dir(),
        '__pycache__': remove_pycache(),
        '打包檔案': remove_build_files(),
    }
    
    print("\n" + "=" * 60)
    print("📊 清理結果")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for item, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {item}")
    
    print()
    if all_passed:
        print("🎉 清理完成！現在可以運行檢查腳本。")
        print("\n執行: python check_release.py")
        return 0
    else:
        print("⚠️  某些清理失敗，請檢查錯誤訊息。")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
