# CLAUDE.md - 技能追蹤器 開發規範

## 專案概要

**技能追蹤器 (Skill Tracker)** — Artale 楓之谷技能冷卻追蹤工具。
Python 3 + customtkinter GUI 桌面應用，支援 PyInstaller 打包為 exe。

## 技術棧

- **GUI**: customtkinter (dark mode)
- **圖片**: Pillow (PIL)
- **快捷鍵**: pynput (全域鍵盤監聽)
- **HTTP**: requests (更新檢查)
- **打包**: PyInstaller (`skill_tracker.spec`)

## 專案結構

```
main.py                  # 入口點
version.py               # 版本號 (VERSION = "x.y.z")
config.json              # 技能資料 + 使用者設定
profiles/                # 使用者配置檔 (JSON)
images/                  # 技能圖示
src/ui/
  app.py                 # 主應用程式 (App 類別, 統一協調)
  config_manager.py      # 設定檔讀寫、配置管理
  skill_manager.py       # 技能資料載入、圖片快取
  hotkey_manager.py      # 鍵盤監聽、快捷鍵綁定
  window_manager.py      # 浮動視窗生命週期、定位
  skill_window.py        # 單一技能倒數視窗 (tkinter.Toplevel)
  skill_column.py        # 三欄技能列表
  skill_item.py          # 單一技能列元件
  header.py              # 頂部控制列
  theme.py               # 主題常量 (AppTheme)
  helpers.py             # 工具函數 (resource_path 等)
  updater.py             # 版本更新檢查
  dialogs/               # 對話框 (base_dialog, profile_dialog, settings_dialog)
```

## 命名規範

| 類型 | 風格 | 範例 |
|------|------|------|
| 類別 | PascalCase | `SkillManager`, `SkillWindow` |
| 函數/方法 | snake_case | `load_skills()`, `get_skill()` |
| 私有方法 | `_` 前綴 | `_load_config()`, `_build_ui()` |
| 常量 | UPPER_SNAKE_CASE | `H_GAP`, `MAX_PER_ROW` |
| 主題常量 | 類別屬性 + UPPER_SNAKE_CASE | `AppTheme.BG_PRIMARY` |

## 程式碼風格

### 語言
- **程式碼**: 英文變數名 + 中文 docstring / 註解
- **UI 文字**: 繁體中文
- **config.json 裡的名稱**: 繁體中文

### Docstring
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

### Import 順序
```python
# 1. 標準庫
import sys, os, json, threading

# 2. 第三方套件
import customtkinter as ctk
from PIL import Image, ImageTk
from pynput import keyboard

# 3. 本地模組
from src.ui.config_manager import ConfigManager
from src.ui.theme import AppTheme
```

### 主題與樣式
- 所有顏色、字型、圓角尺寸必須使用 `AppTheme` 常量，禁止硬編碼
- 新增顏色/字型時統一加到 `theme.py` 的 `AppTheme` 類別

### 資源路徑
- 所有檔案路徑必須透過 `helpers.resource_path()` 處理，以支援 PyInstaller 打包

## 架構規則

### 職責分離
- **App (app.py)**: 只做協調，初始化各 Manager，串接事件
- **Manager 類別**: 各自負責單一領域 (config / skill / hotkey / window)
- **UI 元件**: 接收 callback，不直接操作其他元件的狀態
- **dialog/**: 所有對話框繼承 `BaseDialog`

### 狀態管理
- 技能狀態 (`permanent`, `loop`, `alert_enabled`) 集中在 App 實例
- UI 狀態透過 `ctk.BooleanVar` 雙向綁定
- 狀態變更後呼叫 `config_manager.save_profile()` 持久化

### 事件模式
- 使用 callback 函數傳遞事件 (`on_close`, `on_drag_start` 等)
- 鍵盤事件走 pynput daemon thread
- 倒數計時走 `tkinter.after()` 輪詢 (100ms)

### 執行緒安全
- pynput listener 為 daemon thread
- UI 更新必須在主執行緒 (用 `after()` 排程)
- 網路請求 (更新檢查) 用 `after()` 延遲啟動，不阻塞 UI

## 資料格式

### config.json
```json
{
  "skills": [{ "id": "", "name": "", "icon": "", "cooldown": 0, "hotkey": "", "category": "", "subcategory": "" }],
  "items": [{ "id": "", "name": "", "icon": "", "cooldown": 0, "category": "item", "subcategory": "" }],
  "settings": { "player_name": "", "skill_start_x": 0, "skill_start_y": 0, ... }
}
```
- `skills` / `items` 為唯讀資料來源，不可被程式覆寫
- `settings` 為可變設定

### profiles/{name}.json
```json
{
  "hotkeys": {},
  "permanent": {},
  "loop": {},
  "alert_enabled": {},
  "cooldown_overrides": {}
}
```

## 版本管理

- 版本號唯一定義在 `version.py` 的 `VERSION` 變數
- Changelog 格式: emoji 標記 (🎉 新版 / ✨ 功能 / 🐛 修復 / ✅ 任務)
- 使用 `bump_version.py` 自動遞增版本

## 常用指令

```bash
# 執行
python main.py

# 安裝依賴
pip install -r requirements.txt

# 打包
pyinstaller skill_tracker.spec

# 版本遞增
python bump_version.py
```

## 注意事項

- 浮動視窗使用 `tkinter.Toplevel`（非 customtkinter），因為需要透明背景
- Windows 限定: `-transparentcolor` 用 `#010101` 實現透明
- 圖片快取: SkillManager 在啟動時載入所有技能圖片，同時產生 `PhotoImage` 和 `CTkImage` 兩種格式
- 新增技能只需在 `config.json` 加入資料 + 放入對應圖片檔到 `images/`
- 新增對話框請繼承 `dialogs/base_dialog.py`
