"""
工具函數模組
提供通用的輔助函數
"""

import os
import sys


def resource_path(relative_path):
    """獲取資源文件路徑（支援 PyInstaller 打包）"""
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def darken_color(hex_color, factor=0.8):
    """將顏色變暗
    
    Args:
        hex_color: 十六進制顏色值 (#RRGGBB)
        factor: 變暗係數 (0-1)
    
    Returns:
        變暗後的顏色
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = max(0, int(r * factor))
    g = max(0, int(g * factor))
    b = max(0, int(b * factor))
    return f'#{r:02x}{g:02x}{b:02x}'
