## 1. 建立 Domain 模組結構

- [x] 1.1 建立 `src/domain/__init__.py`，匯出所有 domain models
- [x] 1.2 建立 `src/domain/models.py`，加入模組 docstring 說明此為整潔架構的領域層

## 2. 實作 Domain Models（dataclass）

- [x] 2.1 實作 `SkillMetadata` — 不可變技能元資料 dataclass（id, name, icon, cooldown, category, subcategory），對應 config.json skills/items 靜態區（SkillMetadata is an immutable data model）
- [x] 2.2 實作 `SkillState` — 每配置可變技能狀態 dataclass（hotkey, permanent, loop, alert_enabled, cooldown_override, alert_seconds_override, sound_override, alert_sound_override），所有欄位有預設值（SkillState encapsulates per-profile mutable skill state）
- [x] 2.3 實作 `SkillState.set_permanent()` 和 `SkillState.set_loop()`，內建 permanent ⊕ loop 互斥規則（SkillState enforces permanent and loop mutual exclusion）
- [x] 2.4 實作 `Profile` dataclass（name, skill_states dict），包含 `get_state(skill_id)` 方法提供 lazy 初始化（Profile aggregates SkillState by skill ID）
- [x] 2.5 實作 `MonsterData` dataclass（id, name, icon, respawn_time, hotkey, alert_before, loop, permanent, sound, alert_sound）（MonsterData represents monster respawn configuration）
- [x] 2.6 實作 `OverlayData` dataclass（id, name, file, alpha, x, y, width, height）（OverlayData represents overlay image configuration）
- [x] 2.7 實作 `GlobalSettings` dataclass（player_name, skill_start_x, skill_start_y, enable_sound, window_size, alert_before_seconds, global_sound, global_alert_sound, current_profile）（GlobalSettings represents cross-profile application settings）
- [x] 2.8 確認 domain models 零 Qt 依賴 — `src/domain/models.py` 不可 import PySide6（Domain models have zero Qt dependency）

## 3. 實作 Repository Layer

- [x] 3.1 建立 `src/domain/repositories.py`，加入模組 docstring 說明 Repository 包裝 ConfigManager 而非取代
- [x] 3.2 實作 `SkillRepository` — 包裝 ConfigManager，合併 initial_skills 和 initial_items，提供 get_all/get/get_by_category 回傳 SkillMetadata（SkillRepository provides read-only skill metadata access）
- [x] 3.3 實作 `ProfileRepository` — 包裝 ConfigManager 的 profile 方法，load 時將 JSON dict 轉為 Profile model，save 時將 Profile 轉回 JSON dict 格式（ProfileRepository provides typed profile CRUD）
- [x] 3.4 實作 `MonsterRepository` — 包裝 ConfigManager 的 monsters 資料，提供 get_all/get/get_by_hotkey/save_all/get_original_respawn_time（MonsterRepository provides typed monster data access）
- [x] 3.5 實作 `OverlayRepository` — 包裝 ConfigManager 的 overlays 資料，提供 get_all/save_all（OverlayRepository provides typed overlay data access）
- [x] 3.6 實作 `SettingsRepository` — 包裝 ConfigManager 的 settings 資料，提供 load/save 回傳 GlobalSettings（SettingsRepository provides typed global settings access）
- [x] 3.7 確認 repositories 零 Qt 依賴 — `src/domain/repositories.py` 不可 import PySide6（Repositories have zero Qt dependency）

## 4. 整合到 App

- [x] 4.1 在 `src/ui/app.py` 的 `__init__` 中建構所有 Repository 實例（`self.skill_repo`, `self.profile_repo`, `self.monster_repo`, `self.overlay_repo`, `self.settings_repo`），與現有 manager 並存（Repository 建構在 App.__init__ 中與現有 manager 並存；模組位置選擇 src/domain/ 而非 src/models/）
- [x] 4.2 驗證 `python main.py` 啟動正常，所有頁面功能不受影響

## 5. 驗證

- [x] 5.1 驗證 Domain Models 使用 dataclass 而非 TypedDict — 確認所有 model 使用 `@dataclass` 裝飾器
- [x] 5.2 驗證 SkillState 互斥規則內建於 setter 方法 — 手動測試 `set_permanent(True)` 清除 loop 且 `set_loop(True)` 清除 permanent
- [x] 5.3 驗證技能倒數、快捷鍵綁定、配置切換、怪物重生計時等功能正常運作
- [x] 5.4 驗證 config.json 和 profiles/*.json 存檔格式不變（Profile 使用 dict[str, SkillState] 而非 list）
