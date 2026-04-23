# 技能追蹤器 — 專案概要

## 簡介

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
main.py                  # 入口點（`python main.py --v2` 進 V2 預覽 shell）
main_v2.py               # V2 預覽入口（紫色漸層 dashboard，逐頁接線中）
version.py               # 版本號 (VERSION = "x.y.z")
config.json              # 技能資料 + 使用者設定
profiles/                # 使用者配置檔 (JSON)
images/                  # 技能圖示
sounds/                  # 音效檔案
src/ui/
  app.py                 # 主應用程式 (App / QMainWindow, 統一協調；繼承 AppCoreMixin)
  app_core.py            # AppCoreMixin — V1 App 與 V2AppContext 共用 domain backing（含 12 技能 + 8 怪物 + switch_profile + 4 sound/monster delegate 方法）
  dispatcher.py          # Dispatcher — 跨執行緒安全的回呼排程器（V1/V2 共用）
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
    potion_cost_page.py  # 藥水費用計算頁面
    mapleworld_page.py   # MapleStory Worlds 本機資源瀏覽頁面
  dialogs/               # 對話框
    base_dialog.py       # BaseDialog 基底類別
    profile_dialog.py    # 配置管理對話框
    settings_dialog.py   # 設定對話框
    skill_detail_dialog.py # 技能細節設定對話框
    potion_save_dialog.py  # 藥水紀錄儲存/載入對話框
    update_dialog.py     # 更新通知對話框
src/domain/              # 純 Python 領域層（零 Qt 依賴，V1/V2 共用）
  models.py              # 領域資料模型
  services.py            # SkillService / MonsterService
  potion_service.py      # 藥水費用計算、autosave、紀錄序列化
src/ui_v2/               # V2 預覽 shell（紫色漸層 dashboard）
  theme_v2.py            # V2 主題常量 (V2Theme)
  header_v2.py           # V2 頁首（精簡為視窗控制 + 拖曳區；profile dropdown 已搬至 skill_page_v2）
  sidebar_v2.py          # V2 左側導覽
  status_bar_v2.py       # V2 底部狀態列
  components.py          # V2 共用元件
  lucide.py              # Lucide SVG 圖示載入器
  icons/                 # Lucide SVG 來源
  pages/                 # V2 頁面（overlay/mapleworld/potion 已接線；skill/monster 為最小接線）
    potion_page_v2.py    # 練功水錢 V2 頁面（透過 PotionService 接線；與 V1 共用 potion_autosave.json）
  dialogs/               # V2 對話框
    potion_save_dialog_v2.py  # V2 練功紀錄儲存對話框
    potion_load_dialog_v2.py  # V2 練功紀錄載入對話框
docs/DESIGN_V2.md        # V2 設計規範（顏色、間距、元件契約）
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
