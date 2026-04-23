## 1. 前置驗證

- [x] 1.1 跑既有 verify：`python verify_skill_page_v2.py && python verify_monster_page_v2.py && python verify_toast_v2.py` 全綠

## 2. AppCoreMixin SHALL provide apply_settings(result)

- [x] 2.1 落實 Requirement「AppCoreMixin SHALL provide apply_settings(result)」第 1-3 步：在 `src/ui/app_core.py` 末段新增 `apply_settings(self, result: dict)`，記下 pre-apply 的 `old_window_size = self.window_size` 與 `old_xy = (self.skill_start_x, self.skill_start_y)`；接著從 result 讀 8 個 key 寫到 self（用 result.get + 文件預設值）；呼叫 `self.sound_manager.set_volume(self.sound_volume / 100.0)`；同步 `alert_before_seconds / global_sound / global_alert_sound` 到 `self.skill_service`
- [x] 2.2 落實第 4 步（持久化）：依序呼叫 `self.config_manager.set_settings(...)` 寫 8 個 key，最後 `self.config_manager.save()`
- [x] 2.3 落實第 5 步（refresh alert_seconds_buttons）：iter `self.alert_seconds_buttons.items()`，對沒在 `skill_alert_seconds_overrides` 內的 sid 改 `btn.setText(f"{self.alert_before_seconds}s")`
- [x] 2.4 落實第 6 步（window_manager 條件式同步）：`if self.window_size != old_window_size`：close_all + initialize_persistent_skills；else：iter active_windows 設 `enable_sound` + `refresh_window_sound_params(sid)`，再 if `(x,y) != old_xy`：`reposition_all()`
- [x] 2.5 落實第 7 步（toast）：`toast = getattr(self, "toast", None); if toast: toast.show("設定已保存並套用", "success")`
- [x] 2.6 在 `src/ui/app.py` `show_settings` 內把 `if result: ... 對應第 292-337 行整段` 替換為單行 `self.apply_settings(result)`，移除舊內聯邏輯

## 3. V1 行為 regression 驗證

- [x] 3.1 import smoke：`python -c "from src.ui.app import App; assert hasattr(App, 'apply_settings')"`
- [x] 3.2 跑既有 verify：`python verify_skill_page_v2.py && python verify_monster_page_v2.py && python verify_toast_v2.py` 全綠
- [x] 3.3 V1 手動：開 `python main.py` → header 齒輪 → SettingsDialog → 改音量 + window_size → 儲存 → 確認 toast「設定已保存並套用」、視窗有重建、再開 dialog 看到新值

## 4. SettingsDialogV2 SHALL expose all 8 V1 settings fields

- [x] 4.1 落實 Requirement「SettingsDialogV2 SHALL expose all 8 V1 settings fields」：新建 `src/ui_v2/dialogs/settings_dialog_v2.py`，`class SettingsDialogV2(BaseDialogV2)`，建構 `(parent, app)`；在 `_build` 內依序加 8 個欄位（label + widget），順序：x, y → enable_sound → alert_before_seconds → window_size → global_sound (combo+試聽) → global_alert_sound (combo+試聽) → sound_volume (slider+%)
- [x] 4.2 sound combo 建構：用「— 無 —」當第一項 (filename=""); 其餘從 `app.sound_manager.list_sounds()` + label 用 `get_sound_label(filename)`；當前選項依 `app.global_sound` / `app.global_alert_sound` 對應；建 `label→filename` map 放在 self
- [x] 4.3 試聽按鈕：每個 sound combo 旁 QPushButton「試聽」，click → 取當前 combo 的 filename（從 label_map），非空才呼 `app.sound_manager.play(filename)`
- [x] 4.4 取消 / 確認按鈕：取消 → `self.reject()`；確認 → 構 result dict（8 keys 同 V1 SettingsDialog.result 結構）→ 呼 `self.app.apply_settings(result)` → `self.accept()`
- [x] 4.5 將 `SettingsDialogV2` 加到 `src/ui_v2/dialogs/__init__.py` 的 export

## 5. SidebarV2 settings gear SHALL open SettingsDialogV2

- [x] 5.1 落實 Requirement「SidebarV2 settings gear SHALL open SettingsDialogV2」第 1 部分：`src/ui_v2/sidebar_v2.py` `SidebarV2.__init__` 加 `on_settings_click=None` 參數，存到 self；底部齒輪 `settings.clicked.connect(lambda: self._on_settings_click and self._on_settings_click())`
- [x] 5.2 第 2 部分：`main_v2.py` 建 SidebarV2 那行傳入 lambda：`lambda: SettingsDialogV2(self, self.app_ctx).exec()`；import `from src.ui_v2.dialogs import SettingsDialogV2`

## 6. 驗證腳本

- [x] 6.1 新建 `verify_settings_dialog_v2.py`，仿其他 verify_*：用 MagicMock 建 fake app；提供 sound_manager.list_sounds 回 ["a.wav", "b.wav"]、get_sound_label 用 lambda；初始 8 個欄位值
- [x] 6.2 test_initial_values: build SettingsDialogV2(None, app) → 斷言 x_spin/y_spin/sound_cb/alert_spin/size_spin/volume_slider 顯示 fixture 值；global_sound combo currentText 對應 fixture filename
- [x] 6.3 test_confirm_calls_apply_settings: 改 volume slider 為 50，呼叫 dialog._on_confirm()（不依賴 exec），assert `app.apply_settings.call_count == 1`，call_args[0][0] dict 含正確 8 keys 含 sound_volume=50
- [x] 6.4 test_cancel_does_not_apply: 改值後呼 dialog._on_cancel() / reject()，assert `app.apply_settings.call_count == 0`
- [x] 6.5 全腳本通過 exit 0

## 7. 手動驗證

- [x] 7.1 `python main.py --v2` 啟動，sidebar 底部齒輪 → SettingsDialogV2 開啟，看到 8 欄初值正確
- [x] 7.2 改音量為 30 + 啟用聲音 toggle off + 全域聲音換一個 → 確認 → 對話框關 → 右下角綠色 toast 顯示「設定已保存並套用」
- [x] 7.3 重開 SettingsDialogV2 確認剛改的值已持久化
- [x] 7.4 改 window_size + 確認 → V1 的常駐技能視窗重建（V2 不直接顯示，但 close_all/initialize 已跑）
- [x] 7.5 試聽按鈕：選一個非「— 無 —」的全域結束聲音 → 點試聽 → 聽到聲音

## 8. 收尾

- [x] 8.1 跑 `/simplify` 與 `/spectra-audit`
- [x] 8.2 同步 docs/PROJECT.md：在 `src/ui_v2/dialogs/` 條目加入 `settings_dialog_v2.py`；`src/ui/app_core.py` 條目補「+ apply_settings」
- [ ] 8.3 commit + archive
