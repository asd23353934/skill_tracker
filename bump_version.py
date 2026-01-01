#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本更新腳本
自動更新所有相關文件的版本號
"""

import re
import sys
from datetime import datetime


def update_version_file(new_version, changelog_entry=None):
    """更新 version.py"""
    print(f"📝 更新 version.py 到 {new_version}...")
    
    with open('version.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新版本號
    content = re.sub(
        r'VERSION = "[^"]+"',
        f'VERSION = "{new_version}"',
        content
    )
    
    # 如果有更新日誌，添加到最前面
    if changelog_entry:
        date_str = datetime.now().strftime("%Y-%m-%d")
        new_entry = f"""v{new_version} ({date_str})
-------------------
{changelog_entry}

"""
        content = re.sub(
            r'(CHANGELOG = """)\n',
            f'\\1\n{new_entry}',
            content
        )
    
    with open('version.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ version.py 已更新")


def update_spec_file(new_version):
    """更新 skill_tracker.spec 的文件名"""
    print(f"📝 檢查 skill_tracker.spec...")
    
    try:
        with open('skill_tracker.spec', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # spec 文件通常不需要改版本號，但可以添加註釋
        print("  ℹ️  spec 文件不需要更新版本號")
    except:
        print("  ⚠️  找不到 spec 文件")


def update_readme(new_version):
    """更新 README 中的版本號"""
    print(f"📝 更新 README_USER.md...")
    
    try:
        with open('README_USER.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新標題中的版本
        content = re.sub(
            r'# 🎮 技能追蹤器 v[0-9.]+',
            f'# 🎮 技能追蹤器 v{new_version}',
            content
        )
        
        # 更新下載連結中的版本
        content = re.sub(
            r'技能追蹤器_v[0-9.]+',
            f'技能追蹤器_v{new_version}',
            content
        )
        
        with open('README_USER.md', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ README_USER.md 已更新")
    except Exception as e:
        print(f"  ⚠️  更新失敗: {e}")


def show_current_version():
    """顯示當前版本"""
    try:
        with open('version.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        match = re.search(r'VERSION = "([^"]+)"', content)
        if match:
            return match.group(1)
    except:
        pass
    return "未知"


def parse_version(version_str):
    """解析版本號"""
    try:
        parts = version_str.split('.')
        return tuple(int(p) for p in parts)
    except:
        return (0, 0, 0)


def bump_version(current, bump_type='patch'):
    """自動增加版本號
    
    Args:
        current: 當前版本 (e.g., "1.0.1")
        bump_type: 'major', 'minor', 'patch'
    
    Returns:
        新版本號
    """
    major, minor, patch = parse_version(current)
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def main():
    """主函數"""
    print("=" * 60)
    print("📦 技能追蹤器 - 版本更新")
    print("=" * 60)
    print()
    
    current = show_current_version()
    print(f"當前版本: {current}")
    print()
    
    # 選擇更新類型
    print("請選擇更新類型:")
    print("  1. Patch (修復bug): x.x.X")
    print("  2. Minor (新功能): x.X.0")
    print("  3. Major (重大更新): X.0.0")
    print("  4. 自訂版本號")
    print("  0. 取消")
    print()
    
    choice = input("選擇 [1-4, 0]: ").strip()
    
    if choice == '0':
        print("取消更新")
        return 0
    
    # 決定新版本號
    if choice == '1':
        new_version = bump_version(current, 'patch')
    elif choice == '2':
        new_version = bump_version(current, 'minor')
    elif choice == '3':
        new_version = bump_version(current, 'major')
    elif choice == '4':
        new_version = input("請輸入新版本號 (例如 1.2.0): ").strip()
    else:
        print("❌ 無效的選擇")
        return 1
    
    print()
    print(f"新版本: {new_version}")
    print()
    
    # 輸入更新日誌
    print("請輸入更新內容（每行一項，空行結束）:")
    changelog_lines = []
    while True:
        line = input()
        if not line:
            break
        changelog_lines.append(f"- {line}")
    
    changelog = "\n".join(changelog_lines) if changelog_lines else None
    
    print()
    print("-" * 60)
    print("即將進行以下更新:")
    print(f"  版本: {current} → {new_version}")
    if changelog:
        print(f"  更新內容:\n{changelog}")
    print("-" * 60)
    print()
    
    confirm = input("確認更新？[y/N]: ").strip().lower()
    if confirm != 'y':
        print("取消更新")
        return 0
    
    # 執行更新
    print()
    update_version_file(new_version, changelog)
    update_readme(new_version)
    
    print()
    print("=" * 60)
    print("✅ 版本更新完成！")
    print("=" * 60)
    print()
    print("📋 接下來的步驟:")
    print("  1. 運行: python clean_for_release.py")
    print("  2. 運行: python check_release.py")
    print("  3. 打包: pyinstaller skill_tracker.spec")
    print("  4. 測試打包結果")
    print(f"  5. 創建 Git tag: git tag v{new_version}")
    print(f"  6. 推送: git push origin v{new_version}")
    print(f"  7. 在 GitHub 創建 Release v{new_version}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
