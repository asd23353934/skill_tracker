# sound-system

## Why

音效系統（`SoundManager`）處理內建音效產生、版本管理、WAV/MP3 播放、
舊音效遷移等邏輯，但無正式規格，後續修改音效格式時難以確認影響範圍。

## What Changes

- 建立 `sound-system` 規格，正式記錄：
  - 內建音效的版本管理（`_SOUND_VERSION`）與自動重新產生機制
  - WAV vs MP3 的播放路徑（winsound / Windows MCI）
  - MCI 互斥鎖（同一時間只能有一個 MCI 播放）
  - 舊音效檔名遷移映射（`_MIGRATION_MAP`）
  - 音效匯入流程（複製到 sounds/，同名加後綴）

## Capabilities

### New Capabilities

- `sound-system`: 音效管理規格，涵蓋內建音效版本管理、播放機制、遷移、匯入

### Modified Capabilities

（無）

## Impact

- Affected specs: `sound-system`（新建）
- Affected code:
  - `src/ui/sound_manager.py`（核心實作）
