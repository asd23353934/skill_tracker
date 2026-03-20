# data-format-cleanup

## Why

`config.json` 靜態區（`skills[]` / `items[]`）殘留不應存在的使用者狀態欄位，
且 `settings.skill_permanent` 與 `profiles/*.json → permanent` 完全重複，
導致資料來源不明確，維護時易誤讀或誤寫錯誤的欄位。

## What Changes

- **BREAKING** 從 `config.json → skills[]` 與 `items[]` 移除 `hotkey` 欄位（靜態區禁止存放使用者狀態）
- 從 `config.json → settings` 移除 `skill_permanent` 物件（重複欄位，執行時只讀 profile）
- 確認 `ConfigManager` 與 `SkillManager` 完全不依賴靜態區的 `hotkey` 欄位
- 確認 `App` 完全不讀取 `settings.skill_permanent`，狀態僅從 profile 載入

## Capabilities

### New Capabilities

- `data-format`: 資料分區規格——靜態區、全域可變區、配置可變區的邊界定義與禁止欄位規則

### Modified Capabilities

（無）

## Impact

- Affected specs: `data-format`（新建）
- Affected code:
  - `config.json`（移除殘留欄位）
  - `src/ui/config_manager.py`（確認 save() 使用 initial_skills，不寫入 hotkey）
  - `src/ui/skill_manager.py`（update_hotkey() 目前同時寫入靜態區，須修正）
  - `src/ui/app.py`（確認 _apply_profile() 不讀 settings.skill_permanent）
