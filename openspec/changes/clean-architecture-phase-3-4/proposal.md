## Why

Phase 1-2 建立了 Domain Models 和 Repository Layer，但 `App` 類別（1263 行）仍然是 God Object：所有業務邏輯（permanent/loop 互斥、快捷鍵衝突偵測、配置序列化、冷卻覆寫等）直接實作在 QMainWindow 方法中，UI 元件透過 `self.app` 直接存取 30+ 個狀態 dict 和方法。此階段將業務邏輯抽取到 Service Layer，並讓 App 成為薄協調層。

## What Changes

- **新增 `src/domain/services.py`**：建立 `SkillService`（技能狀態查詢與變更、冷卻覆寫、提示音覆寫、配置序列化）、`MonsterService`（怪物操作）、`SettingsService`（全域設定管理）三個服務類別
- **修改 `src/ui/app.py`**：App 建構 Service 實例，將 100+ 行業務邏輯方法改為委派給 Service，App 僅負責 UI 協調（對話框、按鈕更新、視窗生命週期）
- **修改 `src/ui/hotkey_manager.py`**：快捷鍵衝突偵測和綁定邏輯改為呼叫 SkillService/MonsterService
- **修改 `src/ui/window_manager.py`**：技能狀態查詢改為透過 SkillService
- **修改 `src/ui/skill_card.py`**：狀態讀取改為透過 Service 方法
- **修改 `src/ui/pages/monster_page.py`**：怪物操作改為透過 MonsterService
- **修改 `src/ui/dialogs/skill_detail_dialog.py`**：不再直接寫入 App 狀態 dict，改為透過 Service

## Non-Goals

- **不引入 Event Bus** — 沿用現有 callback 模式，不引入額外的事件系統
- **不改變 UI 元件的建構方式** — 元件仍接收 `self.app`，但透過 `app.skill_service` 等存取業務邏輯
- **不引入 Protocol/ABC 介面** — UI 元件暫不使用窄介面，完整的 Protocol 解耦留給未來
- **不改變 JSON 格式或使用者功能** — 純粹內部架構改善

## Capabilities

### New Capabilities

- `skill-service`: 技能業務邏輯服務層 — 狀態查詢（permanent/loop/alert/cooldown/sound）、狀態變更（互斥規則）、配置序列化/反序列化、批次操作
- `monster-service`: 怪物業務邏輯服務層 — 狀態查詢、重生時間管理、提示音管理、快捷鍵管理

### Modified Capabilities

（無 — 此重構不改變任何現有 spec 的行為需求）

## Impact

- 新增檔案：`src/domain/services.py`
- 修改檔案：`src/ui/app.py`、`src/ui/hotkey_manager.py`、`src/ui/window_manager.py`、`src/ui/skill_card.py`、`src/ui/skill_item.py`、`src/ui/pages/skill_page.py`、`src/ui/pages/monster_page.py`、`src/ui/dialogs/skill_detail_dialog.py`
- 依賴的新模組：`src/domain/models.py`、`src/domain/repositories.py`（Phase 1-2 產出）
- 無 API 變更、無依賴變更、無打包影響
