#!/usr/bin/env python3
"""
一鍵修復所有導入路徑問題
"""

import os
import re

def fix_imports_in_file(filepath):
    """修復單個文件的導入"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 替換 src.utils 為 src.ui
        content = re.sub(r'from src\.utils\.', 'from src.ui.', content)
        
        # 替換 src.core 為 src.ui
        content = re.sub(r'from src\.core\.', 'from src.ui.', content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ 錯誤處理 {filepath}: {e}")
        return False

def main():
    print("🔧 自動修復導入路徑...")
    print()
    
    fixed_count = 0
    
    # 遍歷所有 Python 文件
    for root, dirs, files in os.walk('src'):
        # 跳過 __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_imports_in_file(filepath):
                    print(f"✅ 已修復: {filepath}")
                    fixed_count += 1
    
    print()
    if fixed_count > 0:
        print(f"✅ 共修復 {fixed_count} 個文件")
    else:
        print("✅ 所有文件已是最新")
    print()
    print("現在可以運行: python main.py")

if __name__ == '__main__':
    main()
