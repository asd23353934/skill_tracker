# hotkey-binding-spec

## Why

快捷鍵綁定系統已在程式碼中實作（`HotkeyManager`、`pynput` 監聽），但缺乏正式規格文件。
建立此規格以確保行為一致性、避免技能與怪物快捷鍵邏輯分歧，並為未來維護提供明確契約。

## What Changes

- 建立 `hotkey-binding` 規格文件，正式描述快捷鍵的儲存、捕捉、觸發與衝突解決行為
- 涵蓋技能快捷鍵（存於 `profiles/{name}.json → hotkeys`）與怪物快捷鍵（存於 `config.json → monsters[].hotkey`）兩個子系統
- 記錄執行緒安全約束：pynput daemon thread → `app.after(0, func)` → 主執行緒

## Capabilities

### New Capabilities

- `hotkey-binding`: 快捷鍵綁定系統規格，涵蓋捕捉流程、衝突解決、觸發機制、儲存位置與執行緒安全要求

### Modified Capabilities

（無）

## Impact

- Affected specs: `hotkey-binding`（新建）
- Affected code:
  - `src/ui/hotkey_manager.py`（核心實作）
  - `src/ui/config_manager.py`（快捷鍵持久化）
  - `src/ui/app.py`（`update_hotkey_display`、`auto_save_current_profile`）
  - `src/ui/skill_manager.py`（`get_skill_by_hotkey`）
  - `src/ui/pages/monster_page.py`（怪物快捷鍵 UI）
