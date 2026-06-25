## Context

src/ui_v2/pages/potion_page_v2.py 目前是「左捲動表單（HP/MP/複合藥水 + 楓幣/商店/經驗 + 時間）／右側 320px 摘要」。計算與序列化集中於 src/domain/potion_service.py（calc_summary 回傳 8 鍵含 exp_*；serialize/deserialize 含 exp_start/exp_end）。autosave 檔 potion_autosave.json 與具名紀錄沿用此 schema。

需求：經驗移到新「經驗值計算器」頁；本頁聚焦收支 — 刪除經驗、版面改「左支出／右收入／下方總結」、收入新增「物品取得」（可選練等地圖帶出掉落道具）。

約束：
- 零 Qt 的 domain 計算層（potion_service）須維持純邏輯、可被 verify 腳本涵蓋。
- 既有 potion_autosave.json／具名紀錄不可因 schema 變更而載入失敗。
- UI 一律走 V2Theme／lucide。

## Goals / Non-Goals

Goals:
- 本頁不再出現任何經驗欄位／指標。
- 版面：左支出（藥水）、右收入（楓幣＋商店＋物品取得）、下方總結。
- 物品取得可逐項手填，亦可選練等地圖帶出可編輯的掉落列。
- 舊存檔可無痛載入。

Non-Goals:
- 不做完整全地圖掉落庫；只少量熱門地圖預設。
- 不改藥水列既有計算。
- 不在本頁做經驗計算。

## Decisions

### 移除經驗：UI、摘要與服務 schema 全面下架

下架頁面「獲取經驗」trio、摘要的 exp_total/exp_10/exp_60；calc_summary 不再回傳 exp_* 鍵；PotionFormData 移除 exp_start/exp_end。
理由：經驗改由獨立計算器負責，本頁職責收斂為收支。
取代：原本 8 指標摘要 → 5 指標（income/expense/net/net_10/net_60）。

### 版面：左支出／右收入／下方總結

主體改為上方 QHBoxLayout：左欄=支出（HP/MP/複合藥水區，可捲動），右欄=收入（撿取楓幣前後、商店收益、物品取得，可捲動）；其下放一張橫跨整寬的總結卡（總支出/總收入/淨收益＋每 10/60 分鐘淨收益）；最上方工具列（清除/重置/載入/儲存）不變。練功時間列置於右欄收入區下方或總結區附近，供速率計算。
理由：使用者明確要「左支出右收入下方總結」。
取代：原「左捲動表單／右固定摘要」。

### 物品取得收入：逐項道具列（名稱＋數量＋單價）

新增「物品取得」收入區，列形狀＝可編輯道具名 ＋ 數量 ＋ 單價 ＋ 該列收入（唯讀＝數量×單價）＋ 刪除；排版比照 _PotionRowV2。提供「＋ 新增道具」加空白列。
理由：對應「項目排版跟藥水列類似」，且道具名需可改（手動輸入）。
取代：原本收入只有楓幣＋商店。

### 練等地圖預設：內建少量可編輯掉落清單

新增 src/domain/training_maps.py，定義 TRAINING_MAP_DROPS: 地圖名 → [(道具名, 預設單價)]；少量熱門練等地圖，單價預設 0、已知商店價則填入。右欄收入區提供「選擇練等地圖…」下拉，選取即把該圖掉落道具帶成多列（可再增刪改）。資料於 apply 階段跨來源整理並列給使用者核對。
理由：兼顧便利與資料風險 — 預設只是起點，列可編輯，不依賴完整正確的全地圖庫。
取代：手動逐項輸入（仍保留為基本路徑）。

### 服務層 income 納入物品取得；calc_summary 收斂

PotionFormData 新增 item_rows: list[{name, qty, unit_price}]；新增 calc_items_total(rows)=Σ(qty×unit_price)。income = max(0,mesos_end−mesos_start) ＋ max(0,shop_after−shop_before) ＋ items_total。calc_summary 回傳 income/expense/net/net_10/net_60。
理由：物品取得是收入的一部分，集中在純邏輯層計算。

### 序列化相容：忽略 legacy exp、補空 item_rows

serialize 不再寫 exp_start/exp_end，改寫 item_rows；deserialize 忽略任何 exp_* 舊鍵、缺 item_rows 時補空 list。autosave 同步。
理由：既有 potion_autosave.json／具名紀錄含 exp 欄位，必須能載入不報錯。

## Risks / Trade-offs

- [地圖掉落資料不完整或過期] → 預設僅作起點且列可編輯；apply 時於程式內標註資料為近似、可由使用者修正。
- [舊存檔含 exp 欄位] → deserialize 明確忽略未知鍵，verify 腳本加一筆「載入 legacy 含 exp 紀錄」案例。
- [版面從單欄改雙欄＋底部，回歸風險] → 保留既有 row/section 元件，僅重排容器；先以 verify 腳本與手動啟動驗證。

## Migration Plan

- 讀：deserialize 忽略 exp_*，缺 item_rows 補空 list。
- 寫：serialize/autosave 改新 schema（無 exp、有 item_rows）。
- 回退：移除本變更後，新存檔的 item_rows 會被舊程式忽略，exp 欄位則因本頁不再產生而為 0；不致崩潰。

## Open Questions

(none)
