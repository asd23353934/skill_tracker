#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
發布前檢查腳本
確保打包前的狀態正確
"""

import json
import os
import sys

def check_config_json():
    """檢查 config.json 是否處於初始狀態"""
    print("🔍 檢查 config.json...")
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        settings = config.get('settings', {})
        
        # 檢查項目
        checks = {
            'current_profile': settings.get('current_profile') == '預設配置',
            'skill_send 為空': settings.get('skill_send') == {},
            'skill_receive 為空': settings.get('skill_receive') == {},
            'skill_permanent 為空': settings.get('skill_permanent') == {},
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return False

def check_profiles_dir():
    """檢查 profiles 資料夾"""
    print("\n🔍 檢查 profiles/ 資料夾...")
    
    if not os.path.exists('profiles'):
        print("  ❌ profiles/ 資料夾不存在")
        return False
    
    files = os.listdir('profiles')
    json_files = [f for f in files if f.endswith('.json')]
    
    checks = {
        '只有一個配置文件': len(json_files) == 1,
        '是預設配置.json': '預設配置.json' in json_files,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    if len(json_files) > 1:
        print(f"  ⚠️  發現多個配置: {', '.join(json_files)}")
        print("  💡 提示: 打包前應該只保留預設配置.json")
        print("      請刪除其他配置檔案")
    
    # 檢查預設配置的內容
    if '預設配置.json' in json_files:
        try:
            with open('profiles/預設配置.json', 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            is_empty = (
                profile.get('hotkeys') == {} and
                profile.get('send') == {} and
                profile.get('receive') == {} and
                profile.get('permanent') == {} and
                profile.get('cooldown_overrides') == {}
            )
            
            if is_empty:
                print("  ✅ 預設配置內容為空（正確）")
            else:
                print("  ⚠️  預設配置包含設定（應該全部為空）")
                all_passed = False
        except:
            print("  ❌ 無法讀取預設配置.json")
            all_passed = False
    
    return all_passed

def check_images_dir():
    """檢查 images 資料夾"""
    print("\n🔍 檢查 images/ 資料夾...")
    
    if not os.path.exists('images'):
        print("  ❌ images/ 資料夾不存在")
        return False
    
    # 檢查是否有圖片
    files = os.listdir('images')
    png_files = [f for f in files if f.endswith('.png')]
    
    if len(png_files) > 0:
        print(f"  ✅ 找到 {len(png_files)} 個圖示文件")
        return True
    else:
        print("  ❌ 沒有找到任何圖示文件")
        return False

def check_overlays_dir():
    """檢查 overlays 資料夾（需存在，PyInstaller 才能打包）"""
    print("\n🔍 檢查 overlays/ 資料夾...")

    if not os.path.exists('overlays'):
        os.makedirs('overlays')
        print("  ✅ overlays/ 不存在，已自動建立空資料夾")
        return True

    files = [f for f in os.listdir('overlays')
             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'))]
    print(f"  ✅ overlays/ 存在，包含 {len(files)} 個圖片")
    return True


def check_icon_file():
    """檢查圖示文件"""
    print("\n🔍 檢查 icon.ico...")

    if os.path.exists('icon.ico'):
        size = os.path.getsize('icon.ico')
        print(f"  ✅ 圖示文件存在 ({size} bytes)")
        return True
    else:
        print("  ❌ 圖示文件不存在")
        return False


def check_ps1_bom():
    """檢查所有 .ps1 都帶 UTF-8 BOM

    PS 5.1 預設用系統 ANSI codepage 讀檔，含中文的 .ps1 缺 BOM 會 silent
    parse fail（[3/4] block 整段被跳過不報錯）。實機升級必踩雷。
    Edit 工具偶會 strip BOM，pre-flight 主動驗。
    """
    print("\n🔍 檢查 .ps1 file UTF-8 BOM...")
    targets = ['update_launcher.ps1']
    for sub in ('scripts', '.'):
        if os.path.isdir(sub):
            for name in os.listdir(sub):
                if name.endswith('.ps1'):
                    rel = name if sub == '.' else os.path.join(sub, name)
                    if rel not in targets:
                        targets.append(rel)
    all_passed = True
    for path in targets:
        if not os.path.exists(path):
            continue
        with open(path, 'rb') as f:
            head = f.read(3)
        if head == b'\xef\xbb\xbf':
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path} 缺 BOM（前 3 bytes: {head.hex()}）")
            all_passed = False
    return all_passed


def main():
    """主函數"""
    print("=" * 50)
    print("📦 技能追蹤器 - 發布前檢查")
    print("=" * 50)
    print()

    results = {
        'config.json': check_config_json(),
        'profiles/': check_profiles_dir(),
        'images/': check_images_dir(),
        'overlays/': check_overlays_dir(),
        'icon.ico': check_icon_file(),
        '.ps1 BOM': check_ps1_bom(),
    }
    
    print("\n" + "=" * 50)
    print("📊 檢查結果")
    print("=" * 50)
    
    all_passed = all(results.values())
    
    for item, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {item}")
    
    print()
    if all_passed:
        print("🎉 所有檢查通過！可以開始打包。")
        print("\n執行: pyinstaller skill_tracker.spec")
        return 0
    else:
        print("⚠️  有檢查項目未通過，請先修正。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
