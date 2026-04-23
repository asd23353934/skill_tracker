## 1. 準備與檔案拆分（Decision: 拆出 SkillCardV2 / SkillColumnV2 到獨立檔）

- [x] 1.1 閱讀 V1 `src/ui/pages/skill_page.py` / `src/ui/skill_column.py` / `src/ui/skill_card.py`，登錄 App 方法與 V1 widget dict，確立「Decision: 複用 V1 App 方法而非新增 V2 專屬 callback」的接點清單。
- [x] 1.2 執行「Decision: 拆出 SkillCardV2 / SkillColumnV2 到獨立檔」：建立 `src/ui_v2/pages/skill_card_v2.py`，把 `SkillCard` 類別搬過去，imports 同步調整。
- [x] 1.3 執行「Decision: 拆出 SkillCardV2 / SkillColumnV2 到獨立檔」：建立 `src/ui_v2/pages/skill_column_v2.py`，把 `SkillColumn` 類別搬過去。
- [x] 1.4 清理 `src/ui_v2/pages/skill_page_v2.py`：移除 `DEMO_DATA` / `CATEGORY_DEFS` 寫死示範資料，為後續真實資料接線讓出位置。

## 2. Renders real skill data from SkillManager

- [x] 2.1 實作 Requirement「Renders real skill data from SkillManager」：`SkillPageV2._build()` 呼叫 `app.skill_manager.get_skills()` 與 `get_items()`，依 `category in ('player','boss','item')` 切三組。
- [x] 2.2 每組內按 `subcategory` 子分組，傳給 `SkillColumnV2` 的 `sections` 參數為 `[(subcat, [skill_dict, ...]), ...]`。
- [x] 2.3 子分類順序沿用 V1（依 config.json 首次出現順序），避免切換版面造成使用者混淆。
- [x] 2.4 空分類仍顯示 header 與計數 `0`，不渲染卡片列。

## 3. Skill card displays per-skill state

- [x] 3.1 實作 Requirement「Skill card displays per-skill state」：`SkillCardV2.__init__` 接 `(parent, app, skill_id, skill_meta, accent)`；圖示改用 `app.skill_manager.qpixmaps_card.get(skill_id)`。
- [x] 3.2 冷卻 chip 初始值：`skill_cooldown_overrides.get(id)` 存在時顯示 `{override}秒` + CYAN 修改色，否則顯示 `{metadata.cooldown}秒`。
- [x] 3.3 熱鍵 chip 初始值：`skill_hotkeys.get(id)` 非空顯示按鍵 + YELLOW 色，空字串顯示 `未設`。
- [x] 3.4 三 checkbox 初始值：讀 `skill_permanent` / `skill_loop` / `skill_alert_enabled[id]`。
- [x] 3.5 提前秒數 pill 初始值：`skill_alert_seconds_overrides.get(id)` 或全域 `alert_before_seconds`。

## 4. Card controls delegate to App methods

- [x] 4.1 實作 Requirement「Card controls delegate to App methods」：冷卻 chip 點擊綁 `app.edit_cooldown(id)`；reset 按鈕綁 `app.reset_cooldown(id)`。
- [x] 4.2 熱鍵 chip 點擊綁 `app.hotkey_manager.begin_capture(id, name)`；reset 按鈕綁 `app.reset_hotkey(id)`。
- [x] 4.3 常駐 / 循環 checkbox `stateChanged` 綁 `app.update_skill_setting_exclusive(id, key, cb)`。
- [x] 4.4 提醒 checkbox `stateChanged` 綁 `app.update_alert_setting(id, cb)`。
- [x] 4.5 提前秒數 pill 點擊綁 `app.edit_alert_seconds(id)`。
- [x] 4.6 ⋮ 按鈕點擊綁 `app.show_skill_detail(id)`；App 方法缺席時 fallback 直接 `SkillDetailDialogV2(self.window(), app, id).exec()`。

## 5. Card registers into App widget dictionaries（Decision: V2 Card refresh 介面契約）

- [x] 5.1 實作 Requirement「Card registers into App widget dictionaries」：`SkillCardV2._build()` 結尾把 `cooldown_value_btn` / `hotkey_value_btn` / `alert_pill` / `cb_perm` / `cb_loop` / `cb_alert` 分別寫入 V1 六個 widget dict（`app.cooldown_buttons` / `app.hotkey_buttons` / `app.alert_seconds_buttons` / `app.permanent_vars` / `app.loop_vars` / `app.alert_enabled_vars`）。
- [x] 5.2 在 rebuild 前 `SkillPageV2` 清除上次註冊過的 `skill_id`（記錄於 `self._registered_ids: set`），避免殘留 deleted widget reference。
- [x] 5.3 確認 V1 App 方法接收 V2 widget 實例後可正常 `setText` / `isChecked` / `setChecked`；必要時把 V1 「直接操作 styleSheet」改為呼叫 widget setter。

## 6. Card exposes a refresh method

- [x] 6.1 實作 Requirement「Card exposes a refresh method」：`SkillCardV2.refresh()` 重讀 App state 並更新冷卻 chip 文字 + 樣式。
- [x] 6.2 refresh 更新熱鍵 chip 文字 + 樣式。
- [x] 6.3 refresh 更新三 checkbox 的 `setChecked`，呼叫前以 `blockSignals(True)` 包住，避免再觸發 `stateChanged`。
- [x] 6.4 refresh 更新提前秒數 pill 文字 + 樣式。
- [x] 6.5 在 `SkillPageV2` 提供 `refresh_card(skill_id)` helper，供 App 狀態改變後局部更新，不 rebuild（此為「Decision: rebuild 策略 — 粗粒度 + 局部 refresh」的局部分支）。

## 7. Page rebuilds on first show and profile switch（Decision: rebuild 策略 — 粗粒度 + 局部 refresh）

- [x] 7.1 實作 Requirement「Page rebuilds on first show and profile switch」：`SkillPageV2._build()` 拆為 `_clear_layout()` + `_populate_layout()`，讓 rebuild 可重入。
- [x] 7.2 `showEvent` 首次 rebuild 後設 flag，避免 App 尚未就緒時建構失敗。
- [x] 7.3 訂閱 `app.profile_changed`（若存在）或 hook `config_manager.current_profile` setter，在 handler 內 rebuild。
- [x] 7.4 驗證 checkbox toggle 不觸發 rebuild：`stateChanged` handler 只呼叫 App 方法；App 回寫後只呼叫 `refresh_card(id)`。

## 8. Header quick-toggle chips call toggle_all（Decision: 頁首「全選」chip 行為）

- [x] 8.1 實作 Requirement「Header quick-toggle chips call toggle_all」：把 `_toast_pending` 三顆 chip callback 改綁 `app.toggle_all('permanent'|'loop'|'alert')`。
- [x] 8.2 toggle_all 後對所有已註冊卡片呼叫 `refresh()`（或確認 V1 `toggle_all` 內部已透過 `{cb}.setChecked(...)` 同步）。
- [x] 8.3 測 `toggle_all` 對 94 技能 + items 全跑一輪不超過 100ms。

## 9. Hotkey capture dispatches to main thread

- [x] 9.1 實作 Requirement「Hotkey capture dispatches to main thread」：檢查 `hotkey_manager` 成功觸發後的 callback chain 是否已走 `app.after(0, ...)`；未走則在 `HotkeyManager` 觸發 `app.on_skill_triggered(id)` 前補上 dispatch。
- [x] 9.2 驗證 V2 Card 的 `refresh()` 不在 daemon thread 被呼叫（可用 `threading.current_thread()` 斷言）。

## 10. SkillDetailDialogV2 reads and writes sound overrides（Decision: SkillDetailDialogV2 擴充）

- [x] 10.1 實作 Requirement「SkillDetailDialogV2 reads and writes sound overrides」：`src/ui_v2/dialogs/skill_detail_dialog_v2.py` 建構子改 `(parent, app, skill_id)`，用 `skill_manager.get_skill_by_id(id)` 做 header。
- [x] 10.2 End-sound：QComboBox 列出 `sound_manager.list_sound_files()`；初值 `skill_sound_overrides.get(id)` 或 `default`；試聽按鈕呼叫 `sound_manager.play(path)`。
- [x] 10.3 Alert-sound：同上，綁定 `skill_alert_sound_overrides`。
- [x] 10.4 「從清單移除」按鈕呼叫 `app.remove_skill_from_profile(id)` 並關閉對話框，觸發頁面 rebuild。
- [x] 10.5 Accept 把下拉選值寫入對應 override dict 並呼叫 `config_manager.save_profile(name, snapshot)`；cancel 不寫入。
- [x] 10.6 Cancel 狀態驗證：試聽後取消 `skill_sound_overrides` 保持原值。

## 11. 驗證腳本（verify_skill_page_v2.py）

- [x] 11.1 建立 `verify_skill_page_v2.py`，使用 `_FakeApp` + `_FakeSkillManager` 最小化 fixture（參考 `verify_potion_page_v2.py`）。
- [x] 11.2 test: 三欄分類正確（player / boss / item 各自收到相應數量的 skill dict）。
- [x] 11.3 test: `SkillCardV2` 顯示 cooldown / hotkey / checkbox / alert_seconds 初始值符合 fixture。
- [x] 11.4 test: 點擊 cooldown chip 觸發 `app.edit_cooldown(id)`（mock 紀錄 call）；reset 觸發 `app.reset_cooldown(id)`。
- [x] 11.5 test: `card.refresh()` 後顯示同步，且期間 `stateChanged` callback 不增加。
- [x] 11.6 test: `SkillPageV2` rebuild 後 `app.cooldown_buttons[id]` 指向新卡片而非舊 deleted widget。
- [x] 11.7 test: 頁首三顆 chip 各自觸發 `app.toggle_all(key)`。
- [x] 11.8 全腳本通過 exit 0；納入後續回歸流程。

## 12. 手動回歸

- [x] 12.1 `python main.py --v2` 啟動，觀察技能頁首次顯示不卡頓（<300ms）。
- [x] 12.2 擷取熱鍵、切常駐 / 循環 / 提醒、改冷卻、改提前秒數，切換 profile，回來確認狀態持久化正確。
- [x] 12.3 開 ⋮ 詳細設定對話框：改結束聲音、試聽、按確認；另一次試聽後按取消確認未寫入。
- [x] 12.4 V1 / V2 同時切換：V1 改狀態 → 切 V2 頁 → 確認 V2 顯示同步；反之亦然。
