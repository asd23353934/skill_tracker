## 1. config.json 靜態區清理

- [x] 1.1 從 `config.json → skills[]` 每筆記錄移除 `hotkey` 欄位，確認「Static zone is read-only metadata」規格（欄位枚舉）
- [x] 1.2 從 `config.json → settings` 移除 `skill_permanent` 物件，確認「Global mutable zone stores cross-profile state」規格（settings 不含 skill_permanent）

## 2. SkillManager 靜態區寫入修正

- [x] 2.1 修正 `SkillManager.update_hotkey()`：移除對 `config_manager.config["skills"][i]["hotkey"]` 的寫入，僅更新 `self.skills[skill_id]["hotkey"]`（對照設計決策「靜態區 initial_skills 快照策略」與規格「SkillManager.update_hotkey does not write to static zone」）
- [x] 2.2 驗證 `ConfigManager.save()` 使用 `initial_skills` 快照，確認「Static zone survives runtime mutations」規格

## 3. App 讀取確認

- [x] 3.1 確認 `app._apply_profile()` 不讀取 `settings.skill_permanent`，符合「Profile zone stores all per-profile user state」規格（hotkey 從 profile 讀取）
- [x] 3.2 確認 `ConfigManager.load_profile()` 對缺失欄位補足空字典，符合「Profile fields are complete on load」規格

## 4. 規格文件建立

- [x] 4.1 確認 `openspec/specs/data-format/spec.md` 已正確建立，完整記載資料分區邊界文件化規則（三個分區的邊界定義與禁止欄位）

## 5. 最終驗證

- [x] 5.1 執行程式，切換配置並設定快捷鍵，確認快捷鍵正常儲存/載入（端對端驗證）
- [x] 5.2 檢查 `config.json` 磁碟內容，確認靜態區無 `hotkey` 欄位、settings 無 `skill_permanent`（對照設計決策「config.json 欄位移除策略」）
