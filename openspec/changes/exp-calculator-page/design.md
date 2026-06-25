## Context

練功水頁移除經驗後，新增獨立「經驗值計算器」頁做升級時間估算。專案無任何經驗資料。Artale（MapleStory Worlds 經典服）經驗曲線＝經典 pre-Big-Bang 楓之谷，每級所需經驗為固定表（已從多個社群來源確認 Lv1=15、Lv2=34、Lv3=57…）。架構比照既有 potion：純邏輯 domain（零 Qt、可 verify）＋ V2 頁面。

約束：
- domain 層零 Qt 依賴，可被 verify_*.py 涵蓋。
- UI 走 V2Theme／lucide（禁止自繪 icon）。
- 頁面與側邊欄登錄沿用既有 PAGES 機制（main_v2.py / sidebar_v2.py）。

## Goals / Non-Goals

Goals:
- 由目前等級＋經驗 %、目標等級、經驗速率，算出還需經驗、需打隻數、預估時間。
- 經驗表內建、可被服務層查詢。
- 與既有頁面一致的 V2 外觀與導覽。

Non-Goals:
- 不持久化輸入。
- 不支援非經典經驗曲線。
- 不混合多段速率。

## Decisions

### 經驗表資料：pre-Big-Bang Lv1–199 內建常量

src/domain/exp_table.py 定義 EXP_TO_NEXT：等級 L（1–199）→ 由 L 升到 L+1 所需經驗；Lv200 為頂級無下一級。apply 階段跨至少兩個來源核對整張表並把來源與抽樣值列給使用者確認。
理由：經典表固定且權威，內建最準。
取代：通用公式近似（邊界誤差，捨棄）。

### 升級所需經驗計算：目前等級 % ＋ 整級加總

exp_service.exp_remaining(level, pct, target)：target<=level 回 0；否則 remaining_current = EXP_TO_NEXT[level]×(1−pct/100)，full = Σ EXP_TO_NEXT[L]（L 從 level+1 到 target−1），total = round(remaining_current)+full。pct 夾在 [0,100)，level/target 夾在 [1,200]。
理由：% 是遊戲內顯示的自然輸入；整級加總精確。

### 經驗來源：每小時經驗 或 每隻經驗 × 每小時隻數

服務接受 exp_per_hour；UI 兩模式：直接填每小時經驗，或填每隻經驗與每小時隻數（exp_per_hour = 每隻 × 每小時隻數）。
理由：兩種使用者習慣都常見。

### 需打隻數與預估時間

kills_needed = ceil(total / exp_per_kill)（exp_per_kill>0 才有，否則 None）；time_hours = total / exp_per_hour（exp_per_hour>0 才有，否則 None）；時間以 HH:MM 呈現。
理由：直接回應「要打幾隻、還要多久」。

### 頁面結構與導覽（V2 page ＋ sidebar）

新增 src/ui_v2/pages/exp_calculator_page_v2.py（輸入區＋結果區）；main_v2.py PAGES 與實例化、sidebar_v2.py PAGES 各加一項（lucide icon via lucide_pixmap）。
理由：沿用既有頁面登錄與導覽機制。

### 純邏輯分層（exp_service 零 Qt，可 verify）

計算全部置於 exp_service（零 Qt），頁面僅收集輸入、呼叫服務、顯示結果；新增 verify_exp_service.py 覆蓋邊界（target<=level、pct 邊界、200 封頂、零速率）。
理由：與 potion_service 一致，利於測試與重用。

## Risks / Trade-offs

- [經驗表抄錯] → apply 跨兩來源核對 ＋ verify 腳本斷言關鍵級數（如 Lv1=15、Lv2=34、Lv30、Lv70、Lv199 與到 200 累計）。
- [輸入非法（target<=level、等級超界）] → 服務夾值並回 0／N/A；UI 以 spin 範圍限制。
- [零速率除以零] → exp_per_hour<=0 時 time 回 None，UI 顯示「—」。

## Migration Plan

- 純新增，無既有資料遷移；移除本變更即移除新檔與兩處 PAGES 登錄。

## Open Questions

(none)
