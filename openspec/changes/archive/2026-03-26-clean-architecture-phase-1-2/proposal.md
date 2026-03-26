## Why

目前所有資料（技能、怪物、配置、設定）皆以原始 Python dict 傳遞，無型別安全、無業務規則封裝。`App` 類別（1252 行）同時承擔狀態管理、業務邏輯、UI 協調三重職責，且直接操作 `ConfigManager` 的 JSON I/O，導致持久化邏輯散落各處。此重構建立 Domain Models 和 Repository Layer 作為整潔架構的基礎層，為後續 Service Layer 和 UI 解耦做準備。

## What Changes

- **新增 `src/domain/models.py`**：建立純 Python dataclass 領域模型（`SkillMetadata`、`SkillState`、`Profile`、`MonsterData`、`OverlayData`、`GlobalSettings`），`SkillState` 內建 permanent ⊕ loop 互斥規則
- **新增 `src/domain/repositories.py`**：建立 Repository 類別（`SkillRepository`、`ProfileRepository`、`MonsterRepository`、`OverlayRepository`、`SettingsRepository`），包裝現有 `ConfigManager` 提供型別化的資料存取介面
- **修改 `src/ui/app.py`**：在 `__init__` 中建構 Repository 實例，與現有 Manager 並存，不取代現有邏輯

## Non-Goals

- **不引入 Service Layer** — 業務邏輯仍留在 `App`，Service 抽取屬於後續 Phase 3
- **不解耦 UI 元件** — 頁面和卡片元件仍透過 `self.app` 存取狀態，Protocol 解耦屬於 Phase 4
- **不改變 JSON 格式** — `config.json` 和 `profiles/*.json` 的結構完全不變
- **不修改現有 Manager 行為** — `ConfigManager`、`SkillManager` 等保持原樣
- **不新增任何使用者可見功能** — 純粹架構改善

## Capabilities

### New Capabilities

- `domain-models`: 定義純 Python 領域模型（SkillMetadata、SkillState、Profile、MonsterData、OverlayData、GlobalSettings），封裝業務規則（permanent ⊕ loop 互斥）與資料型別
- `data-repositories`: 建立 Repository 層（SkillRepository、ProfileRepository、MonsterRepository、OverlayRepository、SettingsRepository），包裝 ConfigManager 提供型別化的 CRUD 介面

### Modified Capabilities

（無 — 此重構不改變任何現有 spec 的行為需求）

## Impact

- 新增檔案：`src/domain/__init__.py`、`src/domain/models.py`、`src/domain/repositories.py`
- 修改檔案：`src/ui/app.py`（僅新增 repository 建構，不改現有邏輯）
- 依賴的現有模組：`src/ui/config_manager.py`（Repository 的底層，保持不變）
- 無 API 變更、無依賴變更、無打包影響
