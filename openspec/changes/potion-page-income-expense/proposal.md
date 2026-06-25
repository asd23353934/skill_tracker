## Why

練功水頁目前把支出（藥水）、收入（楓幣／商店）與經驗混在同一捲動表單。經驗即將獨立成「經驗值計算器」頁，因此本頁應聚焦在「收支」：刪除所有經驗欄位、清楚分成「左支出／右收入」、下方放總結；並在收入側新增「物品取得」（可選練等地圖自動帶出掉落道具、逐項填數量單價估算收入）。

## What Changes

- 移除所有經驗相關：頁面的「獲取經驗」輸入列、摘要的 exp_total／exp_10／exp_60，以及 PotionService 的 exp_start／exp_end 與相關 summary 欄位。**BREAKING（內部 schema）**：calc_summary 不再回傳 exp_* 鍵。
- 版面重構為「左：支出（HP／MP／複合藥水）」「右：收入（撿取楓幣 前後、商店收益、物品取得）」「下方：總結」。
- 新增「物品取得」收入區：逐項道具列（名稱＋數量＋單價 → 該列收入），排版比照藥水列；提供「選擇練等地圖」帶出該圖掉落道具的預設列（單價預設 0、已知商店價則帶入），帶出後每列可自由增刪改。
- 收入 ＝ 撿取楓幣差 ＋ 商店收益差 ＋ 物品取得合計；總結顯示 總支出／總收入／淨收益 ＋ 每 10／60 分鐘淨收益（不含經驗）。
- 保留練功時間列（手動／計時器），供速率計算。
- 序列化／autosave：移除 exp 欄位、新增 item_rows；deserialize 容忍舊存檔的 exp 欄位（忽略）與缺 item_rows（補空 list），既有 potion_autosave.json／具名紀錄不報錯。
- 頁面標題改為收支導向（如「練功收支」）。

## Non-Goals

- 不在本頁做經驗計算（移到 exp-calculator 頁）。
- 不建立完整 Artale 全地圖掉落資料庫 — 僅內建少量熱門練等地圖預設，帶出的列可編輯。
- 不更動 HP／MP／複合藥水列的既有計算（前−後 × 單價）。
- 不更動 profiles 結構（本頁狀態走 potion autosave／具名紀錄，不入 profiles）。

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `potion-cost-service`: calc_summary 移除 exp_* 並把物品取得合計納入 income；serialize／deserialize 改 schema（移除 exp、新增 item_rows、容忍 legacy 欄位）。
- `potion-cost-ui-v2`: 版面改為左支出／右收入／下方總結；移除經驗輸入與摘要；新增物品取得區與練等地圖預設。

## Impact

- Affected specs: potion-cost-service（modified）, potion-cost-ui-v2（modified）
- Affected code:
  - Modified: src/domain/potion_service.py（PotionFormData schema、calc_summary、serialize／deserialize）
  - New: src/domain/training_maps.py（練等地圖 → 掉落道具預設，零 Qt 依賴）
  - Modified: src/ui_v2/pages/potion_page_v2.py（版面重構、移除經驗、新增物品取得與地圖預設）
  - Modified: main_v2.py（頁面標題收支化，如有調整）
  - Modified: src/ui_v2/sidebar_v2.py（tooltip 收支化，如有調整）
  - Modified: verify_potion_page_v2.py（更新頁面驗證腳本）
  - Modified: verify_potion_service.py（更新服務層驗證腳本）
  - Modified: docs/DATA_FORMAT.md（potion 紀錄 schema 變更與相容說明）
