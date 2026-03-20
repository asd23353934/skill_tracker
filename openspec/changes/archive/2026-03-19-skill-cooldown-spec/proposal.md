## Why

技能冷卻機制是本工具的核心功能，但目前缺乏正式規格文件，導致未來擴充或修改時缺乏明確的行為契約。
建立此規格文件以記錄現行實作的設計意圖，作為後續變更的基準。

## What Changes

- 新增 `skill-cooldown` 規格文件，描述技能冷卻機制的完整行為
- 涵蓋：觸發流程、計時器、技能狀態機、覆寫系統、警報系統

## Capabilities

### New Capabilities

- `skill-cooldown`: 技能冷卻機制規格，包含狀態機、計時器行為、使用者覆寫與警報系統

### Modified Capabilities

（無）

## Impact

- Affected specs: `openspec/specs/skill-cooldown/spec.md`（新建）
- Affected code:
  - `src/ui/skill_window.py`（計時器核心、狀態機、警報）
  - `src/ui/window_manager.py`（觸發流程）
  - `src/ui/hotkey_manager.py`（快捷鍵觸發）
  - `src/ui/app.py`（狀態管理、覆寫系統）
  - `src/ui/config_manager.py`（配置讀寫）
