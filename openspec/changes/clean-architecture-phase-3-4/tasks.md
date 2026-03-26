## 1. 建立 Service 類別

- [ ] 1.1 在 `src/domain/services.py` 建立 `SkillService` 類別骨架，接收 `SkillRepository`、`ProfileRepository`、global settings 參數，初始化內部狀態 dict（permanent、loop、alert_enabled、cooldown_overrides 等）（Service 持有狀態而非 App）
- [ ] 1.2 實作 SkillService 狀態查詢方法：`is_permanent()`、`is_loop()`、`is_alert_enabled()`、`get_effective_cooldown()`、`get_alert_seconds()`、`get_sound()`、`get_alert_sound()`、`get_hotkey()`、`get_original_cooldown()`（SkillService provides skill state queries）
- [ ] 1.3 實作 SkillService 互斥狀態變更：`set_permanent(skill_id, value) -> dict`、`set_loop(skill_id, value) -> dict`，回傳 `{"permanent": bool, "loop": bool}`（SkillService enforces permanent and loop mutual exclusion on state changes）
- [ ] 1.4 實作 SkillService 覆寫管理：`set_cooldown_override()`、`clear_cooldown_override()`、`set_alert_seconds_override()`、`clear_alert_seconds_override()`、`set_alert_enabled()`、`set_sound_override()`、`clear_sound_override()`、`set_alert_sound_override()`、`clear_alert_sound_override()`（SkillService manages cooldown and alert overrides）
- [ ] 1.5 實作 SkillService 快捷鍵管理：`set_hotkey(skill_id, key_str) -> str | None`（衝突偵測）、`clear_hotkey(skill_id)`、`find_by_hotkey(key_str) -> str | None`（SkillService manages hotkey binding with conflict detection）
- [ ] 1.6 實作 SkillService 批次操作：`toggle_all_permanent()`、`toggle_all_loop()`、`toggle_all_alert()`，各回傳 `dict[str, bool]`（SkillService provides bulk toggle operations）
- [ ] 1.7 實作 SkillService 配置序列化：`serialize_to_dict() -> dict`、`load_from_profile(profile_data: dict)`、`reset_all_to_defaults()`（SkillService handles profile serialization and loading）
- [ ] 1.8 確認 SkillService 零 Qt 依賴（SkillService has zero Qt dependency）
- [ ] 1.9 在 `src/domain/services.py` 建立 `MonsterService` 類別，接收 `ConfigManager` 參數（Service 不依賴 Qt 但可接收 callback）
- [ ] 1.10 實作 MonsterService 查詢方法：`get()`、`get_by_hotkey()`、`get_all()`、`get_original_respawn_time()`（MonsterService provides monster state queries）
- [ ] 1.11 實作 MonsterService 重生時間管理：`set_respawn_time(monster_id, seconds) -> bool`、`reset_respawn_time(monster_id) -> int | None`（MonsterService manages respawn time with reset support）
- [ ] 1.12 實作 MonsterService 快捷鍵管理：`set_hotkey(monster_id, key_str) -> str | None`（衝突偵測）、`clear_hotkey(monster_id)`（MonsterService manages monster hotkey binding）
- [ ] 1.13 實作 MonsterService 狀態管理：`set_loop()`、`set_permanent()`、`set_alert_before()`、`set_sound()`、`set_alert_sound()`（MonsterService manages loop and permanent state）
- [ ] 1.14 實作 MonsterService 持久化：`save() -> bool`，呼叫 `ConfigManager.save()`（MonsterService persists changes via ConfigManager）
- [ ] 1.15 確認 MonsterService 零 Qt 依賴（MonsterService has zero Qt dependency）

## 2. App 整合 Service 並移轉狀態

- [ ] 2.1 在 `app.py` 的 `__init__` 中建構 `SkillService` 和 `MonsterService`，將 `_init_state()` 中的狀態初始化邏輯改為由 SkillService 載入（遷移順序為由內而外）
- [ ] 2.2 在 App 上添加 property 委派：`skill_permanent`、`skill_loop`、`skill_alert_enabled`、`skill_alert_seconds_overrides`、`skill_sound_overrides`、`skill_alert_sound_overrides` 委派到 `self.skill_service` 內部 dict，保持 UI 元件向後相容（Service 持有狀態而非 App）
- [ ] 2.3 將 App 的查詢方法改為委派：`get_original_cooldown()`、`get_alert_seconds()`、`get_sound_for_skill()`、`get_alert_sound_for_skill()` 委派到 `self.skill_service`（SkillService 統一管理技能相關狀態）
- [ ] 2.4 將 App 的怪物查詢方法改為委派：`get_monster()`、`get_monster_by_hotkey()`、`get_all_monsters()`、`save_monsters()` 委派到 `self.monster_service`（MonsterService 統一管理怪物相關狀態）

## 3. 遷移 App 業務方法為薄委派

- [ ] 3.1 重構 `update_skill_setting_exclusive()` 為薄委派：呼叫 `skill_service.set_permanent/set_loop()` 取得新狀態，App 僅負責更新 UI checkbox 和視窗生命週期（App 方法改為薄委派）
- [ ] 3.2 重構 `edit_cooldown()` 和 `reset_cooldown()` 為薄委派：對話框留在 App，業務邏輯呼叫 `skill_service.set_cooldown_override/clear_cooldown_override()`
- [ ] 3.3 重構 `edit_alert_seconds()` 為薄委派：對話框留在 App，業務邏輯呼叫 `skill_service.set_alert_seconds_override/clear_alert_seconds_override()`
- [ ] 3.4 重構 `update_alert_setting()` 為薄委派：呼叫 `skill_service.set_alert_enabled()`
- [ ] 3.5 重構 `reset_hotkey()` 為薄委派：呼叫 `skill_service.clear_hotkey()`
- [ ] 3.6 重構 `toggle_all()` 為薄委派：呼叫 `skill_service.toggle_all_permanent/loop/alert()`，用回傳的 dict 更新所有 UI checkbox
- [ ] 3.7 重構 `auto_save_current_profile()` 和 `_get_current_settings()` 為薄委派：呼叫 `skill_service.serialize_to_dict()`
- [ ] 3.8 重構 `_apply_profile()` 為薄委派：呼叫 `skill_service.reset_all_to_defaults()` + `skill_service.load_from_profile()`
- [ ] 3.9 重構怪物方法為薄委派：`edit_respawn_time()`、`reset_respawn_time()`、`reset_monster_hotkey()`、`edit_monster_alert_before()`、`update_monster_loop()`、`update_monster_permanent()`、`update_monster_alert_sound()`、`update_monster_end_sound()` 呼叫對應 `monster_service` 方法

## 4. 遷移外部呼叫端

- [ ] 4.1 修改 `hotkey_manager.py`：快捷鍵綁定邏輯改為呼叫 `app.skill_service.set_hotkey()` 和 `app.monster_service.set_hotkey()`，衝突偵測改用 `skill_service.find_by_hotkey()` 和 `monster_service.get_by_hotkey()`
- [ ] 4.2 修改 `window_manager.py`：技能狀態查詢改為透過 `app.skill_service.is_permanent()`、`app.skill_service.get_effective_cooldown()` 等方法
- [ ] 4.3 修改 `skill_card.py`：狀態讀取改為 `app.skill_service.is_permanent()`、`app.skill_service.get_alert_seconds()` 等
- [ ] 4.4 修改 `skill_item.py`：同 skill_card.py 的遷移模式
- [ ] 4.5 修改 `pages/skill_page.py`：`toggle_all()` 呼叫改為透過 `app.skill_service`
- [ ] 4.6 修改 `pages/monster_page.py`：怪物操作改為透過 `app.monster_service`
- [ ] 4.7 修改 `dialogs/skill_detail_dialog.py`：不再直接寫入 App 狀態 dict，改為回傳結果由 App 透過 `skill_service` 套用（SkillDetailDialog 改為回傳資料而非直接寫入 App）

## 5. 驗證

- [ ] 5.1 驗證 `python main.py` 啟動正常，所有頁面功能不受影響
- [ ] 5.2 驗證技能 permanent/loop 互斥行為正常
- [ ] 5.3 驗證快捷鍵綁定、衝突偵測、重設功能正常
- [ ] 5.4 驗證配置切換（profile switch）功能正常
- [ ] 5.5 驗證怪物重生計時、快捷鍵、提示音功能正常
- [ ] 5.6 驗證 config.json 和 profiles/*.json 存檔格式不變
