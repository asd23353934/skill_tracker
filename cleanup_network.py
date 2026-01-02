#!/usr/bin/env python3
"""
自動移除網路功能的腳本
"""

def remove_network_from_main_window():
    """移除 main_window.py 中的網路相關代碼"""
    
    with open('src/ui/main_window.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 要移除的方法名稱
    methods_to_remove = [
        '_create_room_column',
        '_create_room',
        '_join_room',
        '_leave_room',
        '_on_members_update',
        '_on_network_skill',
    ]
    
    new_lines = []
    skip_until_next_def = False
    indent_level = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 檢查是否是要移除的方法定義
        if '    def ' in line:
            method_name = line.strip().split('(')[0].replace('def ', '')
            if method_name in methods_to_remove:
                # 開始跳過這個方法
                skip_until_next_def = True
                indent_level = len(line) - len(line.lstrip())
                i += 1
                continue
            elif skip_until_next_def:
                # 檢查是否遇到下一個方法（同等或更少縮進）
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and line.strip():
                    skip_until_next_def = False
        
        if not skip_until_next_def:
            new_lines.append(line)
        
        i += 1
    
    # 特殊處理：移除導入
    final_lines = []
    for line in new_lines:
        # 跳過網路相關導入
        if 'NetworkManager' in line or 'JoinRoomDialog' in line:
            if 'import' in line or 'from' in line:
                continue
        # 跳過 sys, importlib 相關
        if line.strip().startswith('import sys') or line.strip().startswith('import importlib'):
            continue
        if 'importlib.reload' in line or 'sys.modules' in line:
            continue
            
        final_lines.append(line)
    
    with open('src/ui/main_window.py', 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    
    print("✅ main_window.py 已清理")

def remove_join_room_dialog():
    """從 dialogs.py 移除 JoinRoomDialog"""
    try:
        with open('src/ui/dialogs.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 從 __all__ 移除
        content = content.replace("'JoinRoomDialog', ", "")
        content = content.replace(", 'JoinRoomDialog'", "")
        
        # 找到並移除整個類
        lines = content.split('\n')
        new_lines = []
        skip = False
        class_indent = 0
        
        for line in lines:
            if 'class JoinRoomDialog' in line:
                skip = True
                class_indent = len(line) - len(line.lstrip())
                continue
            
            if skip:
                current_indent = len(line) - len(line.lstrip())
                # 如果遇到同等或更小縮進的非空行，停止跳過
                if line.strip() and current_indent <= class_indent:
                    skip = False
            
            if not skip:
                new_lines.append(line)
        
        with open('src/ui/dialogs.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ dialogs.py 已清理")
    except Exception as e:
        print(f"⚠️  dialogs.py 清理失敗: {e}")

def update_requirements():
    """從 requirements.txt 移除 miniupnpc"""
    try:
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()
        
        new_lines = [line for line in lines if 'miniupnpc' not in line.lower()]
        
        with open('requirements.txt', 'w') as f:
            f.writelines(new_lines)
        
        print("✅ requirements.txt 已更新")
    except Exception as e:
        print(f"⚠️  requirements.txt 更新失敗: {e}")

if __name__ == '__main__':
    print("🧹 開始清理網路功能...")
    print()
    
    remove_network_from_main_window()
    remove_join_room_dialog()
    update_requirements()
    
    print()
    print("✅ 清理完成！")
    print()
    print("下一步：")
    print("1. 運行 python diagnose.py 檢查")
    print("2. 運行 python main.py 測試")
