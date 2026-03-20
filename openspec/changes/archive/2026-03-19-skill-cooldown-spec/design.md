## Context

技能追蹤器的冷卻機制已完整實作於 `src/ui/skill_window.py`、`window_manager.py`、`hotkey_manager.py` 與 `app.py`。
此 design 文件的目的是記錄現行設計決策，作為規格文件撰寫的依據，而非規劃新的實作。

## Goals / Non-Goals

**Goals:**

- 記錄現行冷卻機制的設計決策與技術理由
- 提供 `skill-cooldown/spec.md` 的設計依據
- 確立各模組的職責邊界

**Non-Goals:**

- 修改現行實作
- 設計新功能

## Decisions

### 計時器使用 QTimer 輪詢（100ms/50ms）

使用 `QTimer` 每 100ms 觸發一次 `_tick()`，剩餘不足 1 秒時切換為 50ms。

**理由**：PySide6 的 QTimer 在主執行緒執行，天然執行緒安全；精度對冷卻追蹤已足夠（誤差 < 100ms）。
採用 `perf_counter()` 計算 elapsed，避免 QTimer 本身的累積誤差。

### 技能狀態以布林字典集中管理（App 層）

`App` 持有 `skill_permanent`、`skill_loop`、`skill_alert_enabled` 等 dict，而非分散在各 SkillWindow。

**理由**：狀態需跨視窗持久化（配置切換、視窗重建），並需要同步到 UI 控件（QCheckBox）和配置檔。集中管理減少狀態不同步的風險。

### 跨執行緒透過 _Dispatcher 排回主執行緒

pynput listener 為 daemon thread，透過 `_Dispatcher.schedule(0, func)` 以 Qt QueuedConnection 排回主執行緒執行 UI 操作。

**理由**：Qt 不允許在非主執行緒操作 Widget。`schedule(0)` 確保回調在主執行緒下一個事件循環執行，`schedule(ms>0)` 再加 `QTimer.singleShot` 延遲。

### 覆寫系統（cooldown / alert_seconds / sound）存於 profiles

使用者對冷卻時間、警報秒數、音效的個人化覆寫，儲存在 `profiles/{name}.json` 的對應 `*_overrides` 欄位。

**理由**：覆寫屬於「配置可變區」，應隨配置切換。`config.json` 的 skills/items 為唯讀靜態資料，不可存入使用者狀態。

### 警報為一次性觸發，以 alert_triggered 旗標防重複

警報條件滿足後設定 `self.alert_triggered = True`，同一冷卻週期不再觸發第二次。

**理由**：防止在 50ms 快速輪詢階段因多次觸發造成音效重疊或閃爍異常。

## Risks / Trade-offs

- [風險] QTimer 在系統負載高時可能延遲 → 以 `perf_counter()` 計算實際 elapsed 補償，顯示誤差可接受
- [風險] `skill_permanent` 在 `config.json.settings` 與 `profiles` 同時存在（重複） → 現行只讀 profile，settings 版本被忽略，應在未來清理（見 DATA_FORMAT.md 已知問題）
