## 1. 計時觸發規格驗證

- [x] 1.1 確認 `trigger_monster()` 重複觸發時直接返回，符合「Timer is triggered by hotkey」規格（重複觸發忽略）
- [x] 1.2 確認計時方向為正向（0 → respawn_time），符合「Timer counts upward from zero」規格

## 2. loop / permanent 行為驗證

- [x] 2.1 確認 `loop=True` 時計時結束後自動重置並繼續，符合「loop mode auto-restarts the timer」規格（對照設計決策「loop 與 permanent 的語義」）
- [x] 2.2 確認 `loop=False` 時計時結束後視窗關閉，符合「loop mode」規格
- [x] 2.3 確認 `permanent=True` 時啟動即建立常駐視窗（idle 狀態），符合「permanent mode creates always-on window」規格（對照設計決策「loop 與 permanent 的語義」）
- [x] 2.4 確認 permanent 視窗計時結束後重置為 idle 而非關閉，符合「permanent mode」規格

## 3. 提前提示驗證

- [x] 3.1 確認 `alert_before > 0` 時在 `respawn_time - alert_before` 秒時播放一次提前音效，符合「alert_before triggers advance sound」規格（對照設計決策「alert_before 觸發時機」）
- [x] 3.2 確認 `alert_before = 0` 時不播放提前音效，符合「Zero alert_before disables alert」規格

## 4. 音效驗證

- [x] 4.1 確認計時結束時播放 `monster.sound`，符合「End sound plays on timer completion」規格

## 5. 重生時間編輯驗證

- [x] 5.1 確認重生時間可編輯並儲存，符合「Respawn time is editable and resettable」規格
- [x] 5.2 確認重置功能從 `ConfigManager.initial_monsters` 還原原始值，符合「Reset respawn time」規格（對照設計決策「重複觸發處理」中的 initial_monsters 機制）
