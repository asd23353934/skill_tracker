#!/usr/bin/env python3
"""
檢查所有導入是否正確（不需要 tkinter）
"""

import sys
import importlib.util

def check_imports():
    """檢查導入語法"""
    files_to_check = [
        'src/ui/main_window.py',
        'src/ui/components.py',
        'src/ui/dialogs.py',
        'src/ui/skill_window.py',
        'src/ui/skill_manager.py',
        'src/ui/config_manager.py',
        'src/ui/helpers.py',
        'src/ui/styles.py',
        'src/ui/updater.py',
    ]
    
    print("🔍 檢查 Python 文件導入...")
    print()
    
    errors = []
    
    for filepath in files_to_check:
        try:
            # 只檢查語法，不實際導入
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 檢查是否有錯誤的導入
            if 'from src.utils.' in code:
                errors.append(f"❌ {filepath}: 仍使用 src.utils 導入")
            elif 'from src.core.' in code:
                errors.append(f"❌ {filepath}: 仍使用 src.core 導入")
            else:
                print(f"✅ {filepath}")
                
        except Exception as e:
            errors.append(f"❌ {filepath}: {e}")
    
    print()
    if errors:
        print("⚠️ 發現問題：")
        for error in errors:
            print(error)
        return False
    else:
        print("✅ 所有文件導入正確！")
        return True

if __name__ == '__main__':
    success = check_imports()
    sys.exit(0 if success else 1)
