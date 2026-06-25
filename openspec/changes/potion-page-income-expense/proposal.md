## Why

練功水頁原本把支出（藥水）、收入（楓幣／商店）與經驗混在同一捲動表單。經驗已獨立成「經驗值計算器」頁，因此本頁聚焦在「收支」：刪除所有經驗欄位、刪除任何計時／速率欄位、清楚分成「左支出／右收入」、下方放總結；並在收入側新增「物品取得」（可選練功地圖自動帶出掉落道具、逐項填數量單價估算收入）。

## What Changes

- 移除所有經驗相關：頁面的「獲取經驗」輸入列、摘要的 exp_total／exp_10／exp_60，以及 PotionService 的 exp_start／exp_end 與相關 summary 欄位。**BREAKING（內部 schema）**：calc_summary 不再回傳 exp_* 鍵。
- 移除所有「計時／速率」相關：本頁不再有練功時間列、計時器、每小時花費／速率。calc_summary 只回傳 `income / expense / net`，**不含任何除以時間的指標**（無 net_10 / net_60）。`duration_minutes` 仍保留於 serialize/deserialize schema（向後相容），但不參與摘要計算。
- 版面重構為「左：支出（HP／MP／複合藥水，各自捲動）」「右：收入（撿取楓幣 前後、商店收益 前後、物品取得）」「下方：橫跨全寬的總結卡（總支出／總收入／淨收益）」。
- 數量輸入改用組數輸入器 `_StackQty`：`組數 × 組大小▼ ＋ 餘數`，組大小下拉只有 3000／9900；藥水列前/後預設 3000、物品列預設 9900（卷軸類預設 3000）。qty = 組數×組大小 + 餘數。
- 新增「物品取得」收入區：逐項道具列（道具圖示 ＋ 名稱 ＋ 數量 ＋ 單價 → 該列收入），排版比照藥水列；提供「選擇練功地圖」下拉帶出該圖掉落道具列（單價預設 0），切換地圖會先清除現有列再帶新圖、下拉保留所選，「清除全部」清列並重置下拉；帶出後每列可自由增刪改。道具圖示讀自 `images/item_icons/<item_id>.png`，缺圖 fallback 綠色 package 徽章。
- 收入 ＝ 撿取楓幣差 ＋ 商店收益差 ＋ 物品取得合計（差值以 max(0, 後−前) 計，不為負）；總結顯示 總支出／總收入／淨收益。
- 序列化／autosave：移除 exp 欄位、新增 item_rows；deserialize 容忍舊存檔的 exp 欄位（忽略）與缺 item_rows（補空 list），既有 potion_autosave.json／具名紀錄不報錯；損壞存檔以安全轉型（_as_int）載入不崩。
- 頁面標題改為收支導向（「練功收支」）。

## Non-Goals

- 不在本頁做經驗計算（移到 exp-calculator 頁）。
- 不在本頁做任何時間／速率計算（無計時器、無每小時指標）。
- 不建立完整 Artale 全地圖掉落資料庫 — 僅內建少量熱門練功地圖預設（15 張，Lv72–128），帶出的列可編輯。
- 不更動 HP／MP／複合藥水列的既有計算（前−後 × 單價）。
- 不更動 profiles 結構（本頁狀態走 potion autosave／具名紀錄，不入 profiles）。

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `potion-cost-service`: calc_summary 移除 exp_* 與時間／速率指標、只回 income／expense／net 並把物品取得合計納入 income；serialize／deserialize 改 schema（移除 exp、新增 item_rows、保留 duration_minutes、容忍 legacy 欄位）。
- `potion-cost-ui-v2`: 版面改為左支出／右收入／下方總結；移除經驗與時間輸入與相關摘要；數量改用 `_StackQty` 組數輸入器；新增物品取得區與練功地圖預設。

## Impact

- Affected specs: potion-cost-service（modified）, potion-cost-ui-v2（modified）
- Affected code:
  - Modified: src/domain/potion_service.py（PotionFormData／ItemRowData schema、calc_items_total、calc_summary、serialize／deserialize）
  - New: src/domain/training_maps.py（練功地圖 → 掉落道具預設，零 Qt 依賴）
  - Modified: src/ui_v2/pages/potion_page_v2.py（版面重構、移除經驗與時間、_StackQty 組數輸入器、新增物品取得與地圖預設）
  - Modified: verify_potion_page_v2.py（更新頁面驗證腳本）
  - Modified: verify_potion_service.py（更新服務層驗證腳本）
  - New asset: images/item_icons/<item_id>.png（道具圖示，maplestory.io）
