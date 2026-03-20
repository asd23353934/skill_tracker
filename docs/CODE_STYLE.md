# 程式碼風格規範

## 命名規範

| 類型 | 風格 | 範例 |
|------|------|------|
| 類別 | PascalCase | `SkillManager`, `SkillWindow` |
| 函數/方法 | snake_case | `load_skills()`, `get_skill()` |
| 私有方法 | `_` 前綴 | `_load_config()`, `_build_ui()` |
| 常量 | UPPER_SNAKE_CASE | `H_GAP`, `MAX_PER_ROW` |
| 主題常量 | 類別屬性 + UPPER_SNAKE_CASE | `AppTheme.BG_PRIMARY` |
| Qt override | camelCase + `# noqa: N802` | `paintEvent`, `mousePressEvent` |

## 語言

- **程式碼**: 英文變數名 + 中文 docstring / 註解
- **UI 文字**: 繁體中文
- **config.json 裡的名稱**: 繁體中文

## Docstring

- 每個模組開頭用三引號描述用途（中文）
- 函數 docstring 用中文說明，重要參數用 Args / Returns

```python
"""
工具函數模組
提供通用的輔助函數
"""

def darken_color(hex_color, factor=0.8):
    """將顏色變暗

    Args:
        hex_color: 十六進制顏色值 (#RRGGBB)
        factor: 變暗係數 (0-1)

    Returns:
        變暗後的顏色
    """
```

## Import 順序

```python
# 1. 標準庫
import sys, os, json, threading

# 2. 第三方套件
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PIL import Image

# 3. 本地模組
from src.ui.config_manager import ConfigManager
from src.ui.theme import AppTheme
```

## 主題與樣式

- 所有顏色、字型、圓角尺寸必須使用 `AppTheme` 常量，禁止硬編碼
- 新增顏色/字型時統一加到 `theme.py` 的 `AppTheme` 類別
- QSS 樣式透過 f-string + AppTheme 常量建構，勿用魔法顏色字串

## 資源路徑

- 所有**打包資源**路徑必須透過 `helpers.resource_path()` 處理，以支援 PyInstaller 打包
- **使用者資料**路徑（profiles、overlays、sounds）使用 `overlay_manager._user_path()` 模式（執行檔同層目錄）
