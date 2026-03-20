## Context

怪物重生計時由 `WindowManager.trigger_monster()` 啟動，
建立 `SkillWindow`（frameless QWidget）作為浮動計時視窗。
怪物資料儲存於 `config.json → monsters[]`，欄位包含：
`id`, `name`, `icon`, `respawn_time`, `hotkey`, `alert_before`, `loop`, `permanent`, `sound`, `alert_sound`

計時器為從 0 計到 `respawn_time`（正向計時），與技能冷卻的倒數方向相反。

## Goals / Non-Goals

**Goals:**
- 記錄 trigger → 視窗建立 → 計時 → 結束/重置 完整流程
- 明確定義 loop 與 permanent 的語義差異
- 記錄 alert_before 觸發時機

**Non-Goals:**
- 修改現有計時邏輯
- 支援多視窗同時計時同一怪物（目前為唯一視窗）

## Decisions

### loop 與 permanent 的語義

- **loop**（`True`/`False`）：計時結束後是否自動重新從 0 開始（循環）。預設 `True`。
- **permanent**（`True`/`False`）：啟動時是否建立常駐視窗（`idle_start=True`）；
  計時結束後視窗不關閉，回到 idle 等待狀態。預設 `False`。
- 兩者可同時啟用：`permanent=True` + `loop=True` → 常駐視窗自動循環計時。

### 重複觸發處理

同一怪物已有計時視窗時，`trigger_monster()` 直接返回，不建立第二個視窗。

### alert_before 觸發時機

當剩餘時間 ≤ `alert_before` 秒時（即 `elapsed >= respawn_time - alert_before`），
播放 `alert_sound`（一次，不重複）。`alert_before = 0` 表示停用提前提示。

## Risks / Trade-offs

- [風險] SkillWindow 計時邏輯同時用於技能與怪物，修改時需注意兩者的差異（倒數 vs 正向）
  → 緩解：spec 明確記錄「怪物計時為正向（0 → respawn_time）」
