## 1. 功能1 — 提示音禁音（全域 + 每技能）

- [x] 1.1 config_manager 的 DEFAULT_USER_SETTINGS 新增 enable_end_sound / enable_alert_sound（預設 True），並在 app_core 載入設定時實作「全域聲音拆成兩個獨立開關並遷移 enable_sound」（無新欄位但有舊 enable_sound 時兩者取舊值），保留舊鍵相容
- [x] 1.2 settings_dialog_v2 把單一「啟用聲音」改為兩個勾選框「完成提示音」「提前提示音」，_build_result 回傳新欄位、apply_settings 串接寫回（spec: Completion and alert sounds are independently mutable）
- [x] 1.3 skill_window 完成音 gate 改讀 enable_end_sound、提前音 gate 改讀 enable_alert_sound（_on_finish 與 _trigger_alert 兩處）
- [x] 1.4 定義靜音 sentinel 常數，skill_detail_dialog_v2 兩個音效下拉（冷卻完成 / 提前提示）新增「靜音（不播放）」純文字選項並於儲存時寫入 sentinel — 即「每技能靜音以 sentinel 值表達三態」（spec: Individual skills can mute their sounds）
- [x] 1.5 services.py 的 get_sound_for_skill / get_alert_sound_for_skill 套用「全域與每技能的優先順序（全域關 = 總靜音）」：全域關→靜、sentinel→靜、檔名→該檔、空→全域

## 2. 功能3 — 快捷鍵限定前景視窗

- [x] 2.1 新增 src/infrastructure/window_enum.py（Qt-free，ctypes），實作 list_windows 與 get_foreground_exe，即「視窗列舉與縮圖獨立為 infrastructure 模組」
- [x] 2.2 在 window_enum 實作 capture_window_thumbnail，採「視窗縮圖用 PrintWindow 而非截螢幕」（PW_RENDERFULLCONTENT），回傳 RGBA bytes，最小化視窗回退為 None 由 UI 顯示程式圖示
- [x] 2.3 config_manager 的 DEFAULT_USER_SETTINGS 新增 hotkey_app_filter_enabled / hotkey_app_target_exe / hotkey_app_target_label，app_core 載入與 apply_settings 串接這三個欄位
- [x] 2.4 新增 src/ui_v2/dialogs/window_picker_dialog_v2.py（繼承 BaseDialogV2）為「視窗挑選器為獨立對話框（縮圖卡片網格）」：縮圖卡片網格、bytes→QPixmap、點選高亮 / 雙擊確認、重新整理鈕、最小化回退圖示（spec: Target window selection via thumbnail picker）
- [x] 2.5 settings_dialog_v2 於音量列後新增「只在指定視窗觸發快捷鍵」勾選框 + 目標視窗顯示（小縮圖 + 標題）+「選擇視窗…」按鈕開啟挑選器
- [x] 2.6 hotkey_manager._on_key_press 實作「前景視窗比對只在快捷鍵命中後執行，以 exe 名稱比對」：比對到技能/怪物快捷鍵後、觸發前呼叫 get_foreground_exe 比對目標，不符則忽略；捕捉模式不受限（spec: Window-scoped hotkey triggering）

## 3. 測試、文件與收尾

- [x] 3.1 新增 pytest（純邏輯層）：services 音效優先序四情境（全域關 / sentinel / 指定檔 / 空）+ enable_sound 遷移
- [x] 3.2 實機驗證並更新文件：實際啟動程式測「全域 / 單技能禁音」「挑選器縮圖顯示與選定」「快捷鍵僅在目標視窗前景時觸發」；同步更新 docs/DATA_FORMAT.md（新 settings 欄位 + 靜音 sentinel）與 docs/PROJECT.md（window_enum / window_picker_dialog_v2）
- [x] 3.3 收尾：python -m pytest tests/ 全綠 → /simplify + /security-review（或 /spectra:audit）→ version.py bump（minor）+ CHANGELOG 補記 → commit（信箱 asd23353934@gmail.com、不加 Claude 標註）
