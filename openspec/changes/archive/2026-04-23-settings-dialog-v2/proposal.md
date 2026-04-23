## Why

V2 預覽（`python main.py --v2`）目前**沒有任何設定入口**：

- V2 sidebar 底部齒輪按鈕（`src/ui_v2/sidebar_v2.py:95`）有圖示但完全沒接 callback
- V1 的 `SettingsDialog` 從 V1 header 齒輪打開，V2 沒對應 header 元素
- 使用者無法在 V2 內調整音量 / 視窗位置 / 全域提前秒 / 全域聲音 — 必須切回 V1 才能改

且 V1 `App.show_settings()` 內部的 apply 邏輯（同步到 SkillService、寫 ConfigManager.settings、條件式 reposition / rebuild window_manager、refresh alert_seconds_buttons）約 50 行，散落在 App 內。V2 dialog 若 inline 重做這 50 行會出現雙份狀態同步的維護負擔。

## What Changes

- 新增 `src/ui_v2/dialogs/settings_dialog_v2.py`：
  - `SettingsDialogV2(parent, app)` 繼承 `BaseDialogV2`
  - 覆蓋 V1 `SettingsDialog` 的全部 8 個欄位：
    - 技能視窗預設座標 X / Y（QSpinBox）
    - 啟用聲音 (enable_sound, QCheckBox)
    - 全域提前提示秒 (alert_before_seconds, QSpinBox 0-99)
    - 視窗大小 (window_size, QSpinBox 32-128)
    - 全域結束聲音 (global_sound, QComboBox + 試聽按鈕)
    - 全域提前聲音 (global_alert_sound, QComboBox + 試聽按鈕)
    - 音量 (sound_volume, QSlider 0-100)
  - 取消 / 確認按鈕；確認後呼叫 `app.apply_settings(result_dict)`
- 新增 `AppCoreMixin.apply_settings(result: dict)` 到 `src/ui/app_core.py`：
  把 V1 `App.show_settings` 內部 if-result 區段（lines ~292-337）整段抽出，
  變成 V1 / V2 dialog 都能呼叫的純資料 apply 方法。V1 `show_settings`
  改為 build dict → `app.apply_settings(result)`。
- `src/ui_v2/sidebar_v2.py` 底部齒輪 `clicked.connect(...)`：
  - 加 callback 參數 `on_settings_click` 到 `SidebarV2.__init__`
  - `main_v2.py` 傳入 lambda 開 `SettingsDialogV2(self, self.app_ctx)`
- `apply_settings` 完成後呼叫 `self.toast.show("設定已保存並套用", "success")`

## Non-Goals

- **不改 V1 SettingsDialog 視覺**：V1 對話框完全不動，僅將 apply 邏輯抽到 mixin。
- **不引入 profile 管理**（新增 / 改名 / 刪除 profile）：profile 切換已在 skill 頁 dropdown；profile CRUD 另開 spec。
- **不抽 service 層**：兩個 dialog 各自直接讀 `app.config_manager.settings` 取初值；apply 也走 ConfigManager.set_settings + save。
- **不引入新設定欄位**：完全 1:1 覆蓋 V1 SettingsDialog 既有 8 欄。
- **不改 ConfigManager API**：`set_settings` / `save` / `get_settings` 維持現狀。
- **不在 V2 加自訂音效匯入按鈕**：V1 dialog 有此功能，V2 第一版先省略，後續補。

## Capabilities

### New Capabilities

- `settings-dialog-v2`: V2 設定對話框 + AppCoreMixin.apply_settings() 共用 apply 路徑，與 V1 SettingsDialog 結果結構等價。

### Modified Capabilities

(none)

## Impact

- Affected specs: 新增 `settings-dialog-v2`
- Affected code:
  - New:
    - `src/ui_v2/dialogs/settings_dialog_v2.py`
    - `verify_settings_dialog_v2.py`
  - Modified:
    - `src/ui/app_core.py`（新增 `apply_settings(result)`）
    - `src/ui/app.py`（`show_settings` if-result 區段改呼叫 `self.apply_settings(result)`）
    - `src/ui_v2/sidebar_v2.py`（齒輪 callback 參數 + connect）
    - `main_v2.py`（傳 callback 給 SidebarV2，開 SettingsDialogV2）
    - `src/ui_v2/dialogs/__init__.py`（export `SettingsDialogV2`）
  - Removed: 無
