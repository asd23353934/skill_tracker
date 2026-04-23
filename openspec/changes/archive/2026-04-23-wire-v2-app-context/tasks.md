## 1. 準備與前置驗證

- [x] 1.1 盤點 V1 App 現行方法：在 `src/ui/app.py` 列出 13 個共通 App 互動方法（edit_cooldown / reset_cooldown / reset_hotkey / update_skill_setting_exclusive / update_alert_setting / edit_alert_seconds / toggle_all / update_hotkey_display / get_alert_seconds / get_original_cooldown / auto_save_current_profile / show_skill_detail / on_skill_triggered）的起訖行號，記入本地筆記以便後續搬移
- [x] 1.2 盤點 App 狀態 dict：確認 `skill_hotkeys` / `skill_permanent` / `skill_loop` / `skill_alert_enabled` / `skill_cooldown_overrides` / `skill_alert_seconds_overrides` / `skill_sound_overrides` / `skill_alert_sound_overrides` / `cooldown_buttons` / `hotkey_buttons` / `alert_seconds_buttons` / `permanent_vars` / `loop_vars` / `alert_enabled_vars` / `skill_card_widgets` 目前在 App `__init__` 的初始化位置
- [x] 1.3 驗證前置：執行 `python verify_skill_page_v2.py`，必須印出 "All checks passed."；未過不進入 Step 2

## 2. 建立 AppCoreMixin（不影響 V1 App）

- [x] 2.1 新建 `src/ui/app_core.py`，定義 `AppCoreMixin` 類骨架（無任何方法），僅加 docstring 說明「AppCoreMixin SHALL provide shared domain backing for App and V2AppContext」；落實「Mixin 而非組合：AppCoreMixin 直接注入方法到 App / V2AppContext」決策
- [x] 2.2 在 `AppCoreMixin` 實作「`_init_domain_backing(config_manager)`：單一進入點重建 Manager 鏈」，依序建立 SkillManager / HotkeyManager / WindowManager / SoundManager / OverlayManager；同時初始化所有 15 個 dict（AppCoreMixin SHALL initialize the App-level state registries）
- [x] 2.3 驗證「AppCoreMixin SHALL NOT introduce circular imports or regressions」：`python -c "from src.ui.app_core import AppCoreMixin"` 必須成功；同時 `python verify_skill_page_v2.py` 繼續通過

## 3. 搬移 13 個共通方法到 Mixin

- [x] 3.1 先把 edit_cooldown / reset_cooldown / reset_hotkey 從 App 搬到 AppCoreMixin（同簽名、同行為），App 改為不定義這些方法；符合 AppCoreMixin SHALL expose the 13 shared App interaction methods
- [x] 3.2 驗證 3.1：`python -c "from src.ui.app import App; assert App.edit_cooldown.__qualname__.startswith('AppCoreMixin.')"`；執行 `python verify_skill_page_v2.py` 通過
- [x] 3.3 搬移 update_skill_setting_exclusive / update_alert_setting / edit_alert_seconds
- [x] 3.4 驗證 3.3：重跑 2 項驗證（qualname 斷言 + verify_skill_page_v2）
- [x] 3.5 搬移 toggle_all / update_hotkey_display / get_alert_seconds / get_original_cooldown
- [x] 3.6 驗證 3.5：`toggle_all` 的 3 次呼叫順序測試 + verify_skill_page_v2 通過
- [x] 3.7 搬移 auto_save_current_profile / show_skill_detail / on_skill_triggered
- [x] 3.8 驗證 3.7：手動啟動 `python main.py`，點擊任一技能的齒輪 icon → SkillDetailDialog 正常出現；關閉程式確認 profile 自動存檔到 profiles/*.json

## 4. V1 App 套用 Mixin

- [x] 4.1 修改 `src/ui/app.py`：`class App(QMainWindow, AppCoreMixin)`，在 `__init__` 中呼叫 `self._init_domain_backing(self.config_manager)` 取代原本手寫的 Manager 建構 + dict 初始化區塊
- [x] 4.2 驗證：執行 `python main.py`，手動回歸原本的技能頁（V1）— 冷卻設定、熱鍵綁定、常駐/循環 checkbox、Detail dialog 全部互動維持現狀，無 regression
- [x] 4.3 執行 `python verify_skill_page_v2.py` 必通過；同時 import smoke：`python -c "from main_v2 import main; from src.ui.app import App; from src.ui.app_core import AppCoreMixin"`

## 5. V2AppContext 套用 Mixin（解鎖 wire-v2-skill-page 12.1-12.4）

- [x] 5.1 在 `main_v2.py` 的 `V2AppContext` 繼承 `AppCoreMixin`，於 `__init__` 末段呼叫 `self._init_domain_backing(config_manager)`；落實「V2AppContext 先用 `config_manager.current_profile`，UI 切換延後」決策，直接載入該 profile 狀態
- [x] 5.2 驗證：`python main.py --v2` 啟動 V2 shell；SkillPageV2 顯示所有技能卡片（不再留白）
- [x] 5.3 V2 shell 手動回歸 12.1：點擊任一技能 cooldown chip → V1 `edit_cooldown` dialog 開啟 → 輸入 99 → 儲存 → chip 文字變 "99秒" 且呈 CYAN accent
- [x] 5.4 V2 shell 手動回歸 12.2：點擊 hotkey chip → pynput 進入捕捉 → 按下 F5 → chip 文字變 "F5"
- [x] 5.5 V2 shell 手動回歸 12.3：勾選「常駐」checkbox → 技能浮動視窗出現；取消勾選 → 浮動視窗關閉（WindowManager 行為）
- [x] 5.6 V2 shell 手動回歸 12.4：點擊 Detail（…）按鈕 → SkillDetailDialogV2 開啟 → 修改 alert 秒數並套用 → 卡片 alert pill 顯示新值

## 6. V2 相容性掃描

- [x] 6.1 掃描 `src/ui_v2/dialogs/skill_detail_dialog_v2.py`：確認所有 `app.xxx` 屬性都屬於 mixin 初始化的 dict / 方法；如有 V1-only 依賴（例如 `app.toast`），在 V2AppContext 加最小 stub（優先不直接讀 app 內部屬性）
- [x] 6.2 驗證 6.1：在 V2 shell 開啟 Detail dialog 並完整操作一次（改 cooldown + alert + sound + 勾選常駐 → 套用），檢查 override dict、profile 自動存檔、技能卡片 refresh 全部正確

## 7. 最終驗證與交付

- [x] 7.1 跑 `python verify_skill_page_v2.py` 必通過
- [x] 7.2 跑 import smoke：`python -c "from main_v2 import main; from src.ui.app import App; from src.ui.app_core import AppCoreMixin"` 必成功
- [x] 7.3 V1 回歸：`python main.py` 操作技能頁所有互動、關閉程式確認 profile 存檔正確
- [x] 7.4 V2 回歸：`python main.py --v2` 完成 Step 5.3-5.6 的手動 checklist
- [x] 7.5 確認「每步驟皆須驗證」（Each implementation step SHALL be validated before proceeding）— 每步驟旁皆有對應驗證任務已勾選

## 8. 為 wire-v2-skill-page 解除阻塞

- [x] 8.1 回到 wire-v2-skill-page 的 tasks.md，將 12.1 / 12.2 / 12.3 / 12.4 標記為 `[x]`（此時其前置條件已被本次 change 滿足）
- [x] 8.2 視情況將 wire-v2-skill-page archive（若無剩餘任務）
