#!/usr/bin/env python3
"""
刪除發送/接收功能，只保留常駐
"""

def remove_send_receive_from_main_window():
    """從 main_window.py 刪除發送/接收功能"""
    
    with open('src/ui/main_window.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip_line = False
    
    for i, line in enumerate(lines):
        # 跳過包含 send 或 receive 的行（但保留 permanent）
        if any(keyword in line for keyword in ['skill_send', 'skill_receive', 'send_vars', 'receive_vars']):
            # 檢查是否在初始化區域
            if '= {}' in line or 'setdefault' in line or '.copy()' in line:
                continue
        
        # 跳過發送/接收按鈕
        if '\"發送\"' in line or '\"接收\"' in line:
            # 跳過整個按鈕定義（包括後續幾行）
            skip_line = True
            continue
        
        if skip_line:
            if ').pack' in line:
                skip_line = False
            continue
        
        # 跳過 checkbox 中的發送/接收
        if "('send'" in line or "('receive'" in line:
            continue
        
        # 修改 _toggle_all 中的 settings_map
        if 'settings_map = {' in line:
            new_lines.append(line)
            # 跳過 send 和 receive 行
            i += 1
            while i < len(lines) and '}' not in lines[i]:
                if 'permanent' in lines[i]:
                    new_lines.append(lines[i])
                i += 1
            if i < len(lines):
                new_lines.append(lines[i])  # 加上結束的 }
            continue
        
        # 修改 checkboxes 列表
        if 'checkboxes = [' in line:
            new_lines.append('        checkboxes = [\n')
            new_lines.append("            ('permanent', '常駐', Colors.ACCENT_YELLOW, self.skill_permanent, self.permanent_vars)\n")
            new_lines.append('        ]\n')
            # 跳過原來的列表內容
            i += 1
            while i < len(lines) and ']' not in lines[i]:
                i += 1
            continue
        
        # 修改配置保存
        if "'send': self.skill_send" in line or "'receive': self.skill_receive" in line:
            continue
        
        new_lines.append(line)
    
    with open('src/ui/main_window.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ 已從 main_window.py 刪除發送/接收功能")

if __name__ == '__main__':
    print("🧹 開始刪除發送/接收功能...")
    remove_send_receive_from_main_window()
    print("✅ 完成！")
