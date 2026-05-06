"""
工具函數模組
提供通用的輔助函數
"""

import json
import os
import sys
import tempfile


def atomic_write_json(path: str, data) -> None:
    """原子寫 JSON：tempfile + os.replace，避免寫到一半留半截檔。

    失敗時 raise（含 tmp 已清理）；呼叫端負責 log 與回傳 bool。
    """
    parent = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def resource_path(relative_path):
    """獲取資源文件路徑（支援 PyInstaller 打包）"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def user_data_path(relative_path):
    """取得使用者可寫入的資料路徑（支援 PyInstaller 打包）

    打包模式使用 exe 所在目錄；開發模式使用專案根目錄。
    適用於執行時寫入的使用者資料（快取、配置等），不適用於打包資源。

    Args:
        relative_path: 相對路徑

    Returns:
        絕對路徑字串
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)


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


def lighten_color(hex_color, factor=1.2):
    """將顏色變亮

    Args:
        hex_color: 十六進制顏色值 (#RRGGBB)
        factor: 變亮係數 (>1 變亮)

    Returns:
        變亮後的顏色
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return f'#{r:02x}{g:02x}{b:02x}'
