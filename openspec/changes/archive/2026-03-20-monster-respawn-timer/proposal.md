# monster-respawn-timer

## Why

怪物重生計時為應用程式第二大核心功能，但觸發邏輯、loop/permanent/alert 行為
均無正式規格，維護時難以判斷行為是否正確，尤其 permanent 與 loop 的語義需明確區分。

## What Changes

- 建立 `monster-respawn-timer` 規格，正式記錄：
  - 計時器觸發（hotkey → `trigger_monster()`）與視窗生命週期
  - `loop`：計時結束後自動重新開始
  - `permanent`：視窗常駐，計時結束後重置為 idle（不關閉視窗）
  - `alert_before`：提前 N 秒播放提前音效（0 表示停用）
  - 提前音效（`alert_sound`）與結束音效（`sound`）的觸發時機
  - 重生時間的即時修改與重置

## Capabilities

### New Capabilities

- `monster-respawn-timer`: 怪物重生計時規格，涵蓋觸發、計時狀態、loop/permanent/alert 行為

### Modified Capabilities

（無）

## Impact

- Affected specs: `monster-respawn-timer`（新建）
- Affected code:
  - `src/ui/window_manager.py`（`trigger_monster()`、`_create_monster_window()`）
  - `src/ui/skill_window.py`（計時 QTimer 邏輯）
  - `src/ui/pages/monster_page.py`（UI 卡牌、設定互動）
  - `config.json → monsters[]`（資料欄位）
