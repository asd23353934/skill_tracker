## Context

`config.json` 分為三個資料分區，但目前存在邊界模糊問題：

1. **靜態區**（`skills[]` / `items[]`）：設計為唯讀元資料，但每筆 skill/item 均有 `hotkey: ""` 欄位，
   此為使用者狀態，不屬於元資料。
2. **全域可變區**（`settings`）：`settings.skill_permanent` 為 94 個布林值的物件，
   與 `profiles/*.json → permanent` 完全重複，執行時只讀 profile，settings 版本被忽略。
3. **配置可變區**（`profiles/*.json`）：正確儲存所有使用者狀態。

受影響程式碼：
- `skill_manager.py`：`update_hotkey()` 同時寫入 `skill["hotkey"]`（記憶體）與 `config["skills"][i]["hotkey"]`（靜態區記憶體副本）
- `config_manager.py`：`save()` 使用 `initial_skills`（啟動快照），不會持久化 `hotkey` 欄位到磁碟——因此靜態區磁碟內容不受汙染，但記憶體狀態不一致
- `app.py`：`_apply_profile()` 不讀 `settings.skill_permanent`（已正確），但 settings 中仍存在此欄位

## Goals / Non-Goals

**Goals:**
- 定義三個資料分區的邊界規則，形成正式規格
- 移除 `config.json → skills[].hotkey` 欄位（靜態區清理）
- 移除 `config.json → settings.skill_permanent` 欄位（重複狀態清理）
- 修正 `skill_manager.py`：`update_hotkey()` 不再寫入靜態區記憶體副本
- 確認 `ConfigManager.save()` 不會意外將 hotkey 持久化到靜態區

**Non-Goals:**
- 修改 profile 的儲存格式或欄位結構
- 移除 monsters / overlays 等其他全域可變區欄位

## Decisions

### 靜態區 initial_skills 快照策略

`ConfigManager.__init__()` 以 `self.initial_skills = self.config.get('skills', [])` 建立啟動快照，
`save()` 使用此快照而非執行期修改後的 `config["skills"]`，故磁碟上的靜態區不受 `update_hotkey()` 污染。

**決策**：移除 `update_hotkey()` 中寫入 `config["skills"][i]["hotkey"]` 的那段程式碼，
只保留記憶體內 `self.skills[skill_id]["hotkey"]` 的更新。Profile 的持久化依靠 `auto_save_current_profile()`。

### 資料分區邊界文件化

三個分區規則需形成正式 spec（`data-format`），供後續所有開發者參考。

### config.json 欄位移除策略

移除欄位採**就地清理**：
- `skills[].hotkey`：直接從 `config.json` 移除每筆記錄的 `hotkey` 欄位
- `settings.skill_permanent`：從 `config.json → settings` 移除此 key

無需 migration script，因為這些欄位執行時從未被讀取（hotkey 從 profile 讀取，skill_permanent 被忽略）。

## Risks / Trade-offs

- [風險] 舊版 config.json 若有自訂 `hotkey` 欄位，升級後欄位會消失
  → 緩解：此欄位從未被程式讀取（hotkey 只從 profile.hotkeys 載入），消失不影響功能
- [風險] `skill_manager.update_hotkey()` 有外部呼叫者依賴 config["skills"] 的 hotkey
  → 緩解：grep 確認只有 `clear_all_hotkeys()` 使用 `update_hotkey()`，而 clear 時亦會呼叫 `auto_save`

## Migration Plan

1. 更新 `config.json`：移除 `skills[].hotkey` 與 `settings.skill_permanent`
2. 修正 `skill_manager.py`：`update_hotkey()` 移除對 `config_manager.config["skills"]` 的寫入
3. 驗證：執行程式，確認快捷鍵載入/儲存正常
