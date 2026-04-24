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
main.py                  # 入口（薄 wrapper — 佔 single instance 鎖後委派給 main_v2）
main_v2.py               # V2 入口（紫色漸層 dashboard，正式 UI）
version.py               # 版本號 (VERSION = "x.y.z")
config.json              # 靜態：skills / items 元資料（tracked）
config_user.json         # 可變：settings / monsters / overlays（gitignored，ConfigManager 自建）
profiles/                # 使用者配置檔 JSON（gitignored）
images/                  # 技能 / 怪物圖示
sounds/                  # 音效檔案
icon.ico / icon.png      # app icon（.ico 給 exe；.png 給 V2 sidebar logo）
scripts/
  strip_config_for_release.py  # release 前清 config.json 內可變區（--restore 還原）
src/infrastructure/      # 外部邊界（檔案 I/O、OS、第三方）
  config_manager.py      # 靜態 config.json + 可變 config_user.json 分檔讀寫
  skill_loader.py        # 技能元資料載入
  repositories.py        # SkillRepository / 其他資料存取
  sound_manager.py       # 音效播放 / 清單 / 匯入
  helpers.py             # resource_path / user_data_path / lucide_pixmap 等
  updater.py             # 版本更新檢查
  mapleworld_scanner.py  # MapleWorld 資源掃描（Unity / Web，背景執行緒 + callback）
src/domain/              # 純 Python 領域層（零 Qt 依賴）
  models.py              # 領域資料模型
  services.py            # SkillService / MonsterService
  potion_service.py      # 藥水費用計算 / autosave / 紀錄序列化
src/ui/                  # V1/V2 共用控制層（V1 已下架；保留共用基礎）
  app_core.py            # AppCoreMixin — 提供 V2AppContext 的 domain backing
                         #   技能 / 怪物互動 + profile CRUD + apply_settings + switch_profile + delegates
  dispatcher.py          # Dispatcher — 跨執行緒安全的回呼排程
  skill_pixmap_cache.py  # 技能 QPixmap 多尺寸預載快取
  hotkey_manager.py      # pynput 鍵盤監聽 / 快捷鍵綁定
  window_manager.py      # 浮動技能視窗生命週期
  overlay_manager.py     # 浮動圖片視窗管理
  skill_window.py        # 單一技能倒數視窗（QWidget frameless）
  overlay_window.py      # 浮動圖片視窗（QWidget frameless, 透明）
  theme.py               # 共用主題常量 AppTheme（浮動視窗 / hotkey manager 等使用）
src/ui_v2/               # V2 UI（正式 UI）
  theme_v2.py            # V2 主題常量 V2Theme
  header_v2.py           # V2 頁首（精簡為視窗控制 + 拖曳區）
  sidebar_v2.py          # V2 左側導覽（齒輪→SettingsDialogV2）
  status_bar_v2.py       # V2 底部狀態列
  components.py          # V2 共用元件（ArrowComboBox / IconBadge / StatusChip 等）
  toast_v2.py            # V2 Toast 浮層（右下角、fade-out、PlainText 防注入）
  lucide.py / icons/     # Lucide SVG 圖示載入 + 來源
  pages/
    skill_page_v2.py / skill_column_v2.py / skill_card_v2.py
    monster_page_v2.py / overlay_page_v2.py /
    potion_page_v2.py / mapleworld_page_v2.py
    mapleworld_widgets_v2.py  # 資源中心卡片 / chip / 縮圖 LRU / 分類 cache
  dialogs/
    base_dialog_v2.py
    skill_detail_dialog_v2.py
    settings_dialog_v2.py          # 全域設定（音量 / 視窗位置 / 全域聲音…）
    profile_manager_dialog_v2.py   # 配置管理（切換 / 新增 / 複製 / 重命名 / 刪除）
    potion_save_dialog_v2.py / potion_load_dialog_v2.py
docs/DESIGN_V2.md        # V2 設計規範（顏色、間距、元件契約）
```

## 注意事項

- 浮動視窗使用 `QWidget` + `Qt.FramelessWindowHint` + `Qt.WindowStaysOnTopHint`
- 透明背景：`setAttribute(Qt.WA_TranslucentBackground)` + 圓角 QSS
- PySide6 Qt override 方法（如 `paintEvent`）需加 `# noqa: N802` 抑制 PEP 8 警告
- 圖片快取：`SkillPixmapCache` 啟動時載入所有技能圖片，預生多種尺寸（技能視窗用大、卡片用小、V2 用中）
- 新增技能只需在 `config.json` 加入資料 + 放入對應圖片檔到 `images/`
- 新增頁面請在 `src/ui_v2/pages/` 建立
- 新增對話框請繼承 `src/ui_v2/dialogs/base_dialog_v2.py`
- 音效檔放在 `sounds/`，使用者可自訂（exe 同層目錄）
- 升級時 ZIP 不覆蓋 `config_user.json` / `profiles/`；既有 user 資料保留
