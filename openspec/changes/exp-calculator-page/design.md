## Context

練功收支頁移除經驗後，新增獨立「經驗值計算器」頁做升級時間估算。專案無任何經驗資料。Artale（MapleStory Worlds 經典服）經驗曲線＝經典 pre-Big-Bang 楓之谷，每級所需經驗為固定表（已從多個社群來源確認 Lv1=15、Lv2=34、Lv3=57…）。架構比照既有 potion：純邏輯 domain（零 Qt、可 verify）＋ V2 頁面。

約束：
- domain 層零 Qt 依賴，可被 verify_*.py 涵蓋。
- UI 走 V2Theme／lucide（禁止自繪 icon）。
- 頁面與側邊欄登錄沿用既有 page_registry 單一來源（src/ui_v2/page_registry.py）。

## Goals / Non-Goals

Goals:
- 由目前等級＋經驗 %、目標等級、練功效率（區間經驗），算出還需經驗、距下一級還需、預估時間。
- 經驗表內建、可被服務層查詢。
- 與既有頁面一致的 V2 外觀與導覽。

Non-Goals:
- 不持久化輸入。
- 不支援非經典經驗曲線。
- 不混合多段速率。
- 不計算需打隻數（kills needed）。

## Decisions

### 經驗表資料：pre-Big-Bang Lv1–199 內建常量

src/domain/exp_table.py 定義 `MAX_LEVEL = 200` 與 `EXP_TO_NEXT`：等級 L（1–199）→ 由 L 升到 L+1 所需經驗；Lv200 為頂級、無下一級。apply 階段跨至少兩個來源核對整張表並把來源與抽樣值列給使用者確認。
理由：經典表固定且權威，內建最準。
取代：通用公式近似（邊界誤差，捨棄）。

### 升級所需經驗計算：目前等級 % ＋ 整級加總

`exp_service.exp_remaining(level, pct, target)`：target<=level 回 0；否則 ＝ `exp_remaining_in_level(level, pct)`（＝ `round(EXP_TO_NEXT[level]×(1−pct/100))`）＋ Σ EXP_TO_NEXT[L]（L 從 level+1 到 target−1）。pct 夾在 [0,100]，level/target 夾在 [1, MAX_LEVEL]，非數值輸入被 coerce（level/target→1、pct→0）而非丟例外。
理由：% 是遊戲內顯示的自然輸入；整級加總精確。

### 練功效率：單一輸入（區間經驗 ＋ 區間下拉）

UI 只收**一個經驗數字**與**一個區間下拉**（每 10 分鐘 / 30 分鐘 / 1 小時，預設 10 分鐘），由 `exp_service.hourly_rate(exp_per_interval, minutes) = exp×60/minutes` 推得每小時經驗（非正輸入回 0）。
理由：單一輸入比「每小時經驗／每隻×每小時隻數」兩模式更直覺；玩家最容易報的就是一段時間內升了多少經驗。
取代：每小時經驗 或 每隻經驗×每小時隻數 兩模式（複雜、與需打隻數綁定，已捨棄）。

### 預估時間（HH:MM:SS）

`time_hours(total, exp_per_hour)`＝ total / 每小時經驗（每小時經驗 <= 0 回 None）；`format_duration(hours)` 把小時數格式化為零補位 `HH:MM:SS`（時分秒），None 回 `"—"`。
理由：直接回應「還要多久」，時分秒比 HH:MM 更精確。
取代：HH:MM 呈現（精度不足，已捨棄）。

### 結果只呈現三項

結果區只顯示：還需總經驗（total）、距下一級還需（in_level）、預估時間（time）。不計算也不顯示「需打隻數」。
理由：頁面聚焦「經驗與時間」；掉寶／隻數屬其他職責，避免欄位膨脹。
取代：含「需打隻數 / kills_needed」欄（連同 exp_per_kill 輸入一併移除）。

### 頁面結構與導覽（V2 page ＋ page_registry 單一來源）

新增 src/ui_v2/pages/exp_calculator_page_v2.py（輸入區＋結果區）；在 src/ui_v2/page_registry.py 的 `PAGE_REGISTRY` 加一筆 `PageSpec("exp", "經驗計算", "calculator", "經驗計算器", ExpCalculatorPageV2)`。main_v2.py 與 sidebar_v2.py 皆從此單一來源讀取，導覽自動同步（lucide icon via lucide_pixmap）。
理由：沿用既有單一來源登錄機制，新增頁面只改一處。

### 純邏輯分層（exp_service 零 Qt，可 verify）

計算全部置於 exp_service（零 Qt），頁面僅收集輸入、呼叫服務、顯示結果；新增 verify_exp_service.py 覆蓋邊界（target<=level、pct 邊界、200 封頂、零速率、區間推速率、HH:MM:SS 格式）。
理由：與 potion_service 一致，利於測試與重用。

## Risks / Trade-offs

- [經驗表抄錯] → apply 跨兩來源核對 ＋ verify 腳本斷言關鍵級數（Lv1=15、Lv2=34、Lv10=1716、高段抽樣 Lv50/70/100/120/150/199、Lv1→200 累計）。
- [輸入非法（target<=level、等級超界、空白速率）] → 服務夾值並回 0／None；UI 以 spin 範圍限制、空白速率時間顯示「—」。
- [零速率除以零] → exp_per_hour<=0 時 time 回 None，UI 顯示「—」。

## Migration Plan

- 純新增，無既有資料遷移；移除本變更即移除新檔與 page_registry 內 exp 那一筆登錄。

## Open Questions

(none)
