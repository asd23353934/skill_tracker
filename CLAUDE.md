# CLAUDE.md - 技能追蹤器 開發規範

## 專案概要

**技能追蹤器 (Skill Tracker)** — Artale 楓之谷技能冷卻追蹤工具。
Python 3 + PySide6 GUI 桌面應用，支援 PyInstaller 打包為 exe。

## 技術棧

- **GUI**: PySide6 (QMainWindow, QWidget, QSS 樣式)
- **圖片**: Pillow (PIL)
- **快捷鍵**: pynput (全域鍵盤監聽)
- **HTTP**: requests (更新檢查)
- **音效**: winsound + Windows MCI (支援 MP3/WAV)
- **打包**: PyInstaller (`skill_tracker.spec`)

## 專案結構

```
main.py                  # 入口點
version.py               # 版本號 (VERSION = "x.y.z")
config.json              # 技能資料 + 使用者設定
profiles/                # 使用者配置檔 (JSON)
images/                  # 技能圖示
sounds/                  # 音效檔案
src/ui/
  app.py                 # 主應用程式 (App / QMainWindow, 統一協調)
  config_manager.py      # 設定檔讀寫、配置管理
  skill_manager.py       # 技能資料載入、圖片快取
  hotkey_manager.py      # 鍵盤監聽、快捷鍵綁定
  window_manager.py      # 浮動技能視窗生命週期
  overlay_manager.py     # 浮動圖片視窗管理
  skill_window.py        # 單一技能倒數視窗 (QWidget frameless)
  overlay_window.py      # 浮動圖片視窗 (QWidget frameless, 透明)
  skill_column.py        # 技能列表欄位元件
  skill_card.py          # 單一技能卡片元件
  skill_item.py          # 單一技能列元件（技能頁用）
  sidebar.py             # 左側導覽列 (頁面切換)
  header.py              # 頂部控制列 (無框拖曳、視窗控制)
  status_bar.py          # 底部狀態列 (配置名稱 + 版本號 + SizeGrip)
  theme.py               # 主題常量 (AppTheme)
  helpers.py             # 工具函數 (resource_path 等)
  sound_manager.py       # 音效播放管理
  toast.py               # Toast 通知系統
  updater.py             # 版本更新檢查
  pages/
    skill_page.py        # 技能倒數頁面
    monster_page.py      # 怪物重生頁面
    overlay_page.py      # 浮動圖片頁面
  dialogs/               # 對話框
    base_dialog.py       # BaseDialog 基底類別
    profile_dialog.py    # 配置管理對話框
    settings_dialog.py   # 設定對話框
    skill_detail_dialog.py # 技能細節設定對話框
    update_dialog.py     # 更新通知對話框
```

## 命名規範

| 類型 | 風格 | 範例 |
|------|------|------|
| 類別 | PascalCase | `SkillManager`, `SkillWindow` |
| 函數/方法 | snake_case | `load_skills()`, `get_skill()` |
| 私有方法 | `_` 前綴 | `_load_config()`, `_build_ui()` |
| 常量 | UPPER_SNAKE_CASE | `H_GAP`, `MAX_PER_ROW` |
| 主題常量 | 類別屬性 + UPPER_SNAKE_CASE | `AppTheme.BG_PRIMARY` |
| Qt override | camelCase + `# noqa: N802` | `paintEvent`, `mousePressEvent` |

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
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PIL import Image

# 3. 本地模組
from src.ui.config_manager import ConfigManager
from src.ui.theme import AppTheme
```

### 主題與樣式
- 所有顏色、字型、圓角尺寸必須使用 `AppTheme` 常量，禁止硬編碼
- 新增顏色/字型時統一加到 `theme.py` 的 `AppTheme` 類別
- QSS 樣式透過 f-string + AppTheme 常量建構，勿用魔法顏色字串

### 資源路徑
- 所有**打包資源**路徑必須透過 `helpers.resource_path()` 處理，以支援 PyInstaller 打包
- **使用者資料**路徑（profiles、overlays、sounds）使用 `overlay_manager._user_path()` 模式（執行檔同層目錄）

## 架構規則

### 職責分離
- **App (app.py)**: 只做協調，初始化各 Manager，串接事件，包含 `_Dispatcher` 執行緒安全排程
- **Manager 類別**: 各自負責單一領域 (config / skill / hotkey / window / overlay / sound)
- **UI 元件**: 接收 callback，不直接操作其他元件的狀態
- **Pages**: 繼承 QWidget，透過 `self.app` 存取應用狀態，放在 `pages/` 目錄
- **dialog/**: 所有對話框繼承 `BaseDialog`

### 狀態管理
- 技能狀態 (`permanent`, `loop`, `alert_enabled`) 集中在 App 實例
- UI 狀態透過 Qt 訊號/槽雙向同步
- 狀態變更後呼叫 `config_manager.save_profile()` 持久化

### 事件模式
- 使用 callback 函數或 Qt 訊號傳遞事件
- 鍵盤事件走 pynput daemon thread → `_Dispatcher.schedule()` 排回主執行緒
- 倒數計時走 `QTimer` 輪詢 (100ms)

### 執行緒安全
- pynput listener 為 daemon thread，**不可直接操作 UI**
- UI 更新必須在主執行緒，跨執行緒呼叫使用 `app.after(ms, func)`：
  - `ms=0`：透過 `_Dispatcher` Signal/Slot (QueuedConnection) 立即排隊
  - `ms>0`：`_Dispatcher` 先排回主執行緒，再用 `QTimer.singleShot` 延遲
- 網路請求 (更新檢查) 用 `QTimer.singleShot` 延遲啟動，不阻塞 UI

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
- `version.py` 也提供 `get_version()`、`get_changelog()` 等工具函數
- Changelog 格式: emoji 標記 (🎉 新版 / ✨ 功能 / 🐛 修復 / ✅ 任務)
- 使用 `bump_version.py` 自動遞增版本

## 常用指令

```bash
# 執行
python main.py

# 安裝依賴
pip install -r requirements.txt

# 版本遞增（互動式）
python bump_version.py

# 發布前清理
python clean_for_release.py

# 發布前檢查
python check_release.py

# 打包
pyinstaller skill_tracker.spec

# 壓縮為 ZIP 發布檔
python zip_release.py
```

## 注意事項

- 浮動視窗使用 `QWidget` + `Qt.FramelessWindowHint` + `Qt.WindowStaysOnTopHint`
- 透明背景：`setAttribute(Qt.WA_TranslucentBackground)` + 圓角 QSS
- PySide6 Qt override 方法（如 `paintEvent`）需加 `# noqa: N802` 抑制 PEP 8 警告
- 圖片快取: SkillManager 在啟動時載入所有技能圖片，同時產生 `QPixmap`（技能視窗）和 `QPixmap card`（卡片）兩種尺寸
- 新增技能只需在 `config.json` 加入資料 + 放入對應圖片檔到 `images/`
- 新增頁面請在 `pages/` 建立並於 `pages/__init__.py` 匯出
- 新增對話框請繼承 `dialogs/base_dialog.py`
- 音效檔放在 `sounds/`，使用者可自訂（exe 同層目錄）
