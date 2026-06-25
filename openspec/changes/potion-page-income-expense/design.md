## Context

src/ui_v2/pages/potion_page_v2.py 原本是「左捲動表單（HP/MP/複合藥水 + 楓幣/商店/經驗 + 時間）／右側固定摘要」。計算與序列化集中於 src/domain/potion_service.py（calc_summary 回傳含 exp_* 的多鍵；serialize/deserialize 含 exp_start/exp_end）。autosave 檔 potion_autosave.json 與具名紀錄沿用此 schema。

需求：經驗移到新「經驗值計算器」頁；本頁聚焦收支 — 刪除經驗、刪除任何計時／速率、版面改「左支出／右收入／下方總結」、收入新增「物品取得」（可選練功地圖帶出掉落道具）。

約束：
- 零 Qt 的 domain 計算層（potion_service）須維持純邏輯、可被 verify 腳本涵蓋。
- 既有 potion_autosave.json／具名紀錄不可因 schema 變更而載入失敗。
- UI 一律走 V2Theme／lucide。

## Goals / Non-Goals

Goals:
- 本頁不再出現任何經驗欄位／指標。
- 本頁不再出現任何計時器／練功時間／每小時速率欄位或指標。
- 版面：左支出（藥水）、右收入（楓幣＋商店＋物品取得）、下方總結。
- 物品取得可逐項手填，亦可選練功地圖帶出可編輯的掉落列。
- 數量以「組數 × 組大小 ＋ 餘數」直覺輸入。
- 舊存檔可無痛載入。

Non-Goals:
- 不做完整全地圖掉落庫；只少量熱門地圖預設。
- 不改藥水列既有計算。
- 不在本頁做經驗計算，亦不做時間／速率計算。

## Decisions

### 移除經驗與時間：UI、摘要與服務 schema 全面下架

下架頁面「獲取經驗」trio、練功時間列與計時器、摘要的 exp_* 與每小時／每區間速率；calc_summary 不再回傳 exp_* 也不回傳任何 net_10/net_60，只回 `income / expense / net` 三鍵；PotionFormData 移除 exp_start/exp_end。
理由：經驗改由獨立計算器負責，速率非本頁訴求，本頁職責收斂為「本次收支」。
取代：原本多指標摘要（含 exp 與時間速率）→ 3 指標（income/expense/net）。

> 註：`duration_minutes` 仍保留於 serialize/deserialize schema（向後相容舊存檔／不破壞既有檔形狀），但 UI 不再提供其輸入，也不參與 calc_summary。

### 版面：左支出／右收入／下方總結

主體改為上方 QHBoxLayout：左欄=支出（HP/MP/複合藥水區，捲動），右欄=收入（楓幣 ・ 商店 卡：撿取楓幣前後＋商店收益前後；其下物品取得區，捲動）；其下放一張橫跨整寬的總結卡（總支出/總收入/淨收益）；最上方工具列（清除/全部重置/載入紀錄/儲存）＋頁面標題「練功收支」。撿取楓幣「後」變動時自動鏡射為商店收益「前」。
理由：使用者明確要「左支出右收入下方總結」。
取代：原「左捲動表單／右固定摘要」與其中的時間列。

### 數量輸入：_StackQty 組數輸入器

新增 `_StackQty` widget：`[組數] × [組大小▼] ＋ [餘數]`，qty = 組數×組大小 + 餘數；組大小下拉固定 (3000, 9900)。藥水列前/後預設組大小 3000、物品列預設 9900（卷軸類預設 3000）。`set_qty(total, stack)` 以整除還原組/餘且不觸發重算。
理由：遊戲道具以固定上限堆疊，使用者多半知道「幾組＋餘幾個」而非確切總數。

### 物品取得收入：逐項道具列（圖示＋名稱＋數量＋單價）

新增「物品取得」收入區，列形狀＝道具圖示 ＋ 可編輯道具名 ＋ 數量（_StackQty）＋ 單價 ＋ 該列收入（唯讀＝數量×單價）＋ 刪除；排版比照 _PotionRowV2。提供「新增道具」加空白列。道具圖示讀 `images/item_icons/<item_id>.png`，缺圖 fallback 綠色 package 徽章。
理由：對應「項目排版跟藥水列類似」，且道具名需可改。
取代：原本收入只有楓幣＋商店。

### 練功地圖預設：內建少量可編輯掉落清單

新增 src/domain/training_maps.py，TRAINING_MAP_DROPS 結構為 地圖名 → {"level": 等級, "items": [[道具名, item_id], …]}；15 張熱門練功地圖（Lv72–128，神木村龍系列、時間之路、深海峽谷等），多數道具單價 0（賣價由使用者填），少數熱門道具經 DEFAULT_UNIT_PRICES 帶市場參考預設價。`map_names()` 依等級排序、`drops_for()` 回傳 item row（name/item_id/qty=0/unit_price 取自 DEFAULT_UNIT_PRICES、未列者 0）。右欄收入區提供「選擇練功地圖帶出掉落」下拉，選取即「先清除現有列、再帶出該圖掉落列」（下拉保留所選地圖）；「清除全部」清列並把下拉重置回 placeholder。帶出的列可再增刪改。
理由：兼顧便利與資料風險 — 預設只是起點，列可編輯，不依賴完整正確的全地圖庫。少數高頻道具（如龍系列雜物）以 item_id→預設價對照帶市場參考價，跨地圖同價對齊、省去逐次手填，價可隨時改。
取代：手動逐項輸入（仍保留為基本路徑）。

### 服務層 income 納入物品取得；calc_summary 收斂為 3 鍵

PotionFormData 新增 item_rows: list[{name, item_id, qty, stack_size, unit_price, value}]；新增 `calc_items_total(rows)`＝Σ（優先 value，否則 max(0,qty)×max(0,unit_price)）。income = max(0,mesos_end−mesos_start) ＋ max(0,shop_after−shop_before) ＋ items_total。calc_summary 回傳 `{income, expense, net}`，無時間項。
理由：物品取得是收入的一部分，集中在純邏輯層計算；速率非本頁職責故不計算。

### 序列化相容：忽略 legacy exp、補空 item_rows、安全轉型

serialize 不再寫 exp_start/exp_end，改寫 item_rows（仍寫 duration_minutes 以維持檔形狀）；deserialize 忽略任何 exp_* 舊鍵、缺 item_rows 時補空 list、數值欄位以非負轉型。UI `_StackQty`／`_as_int` 對手改或中斷寫入造成的非數值欄位安全轉換，載入損壞 autosave 不崩。autosave 同步。
理由：既有 potion_autosave.json／具名紀錄含 exp 欄位，必須能載入不報錯。

## Risks / Trade-offs

- [地圖掉落資料不完整或過期] → 預設僅作起點且列可編輯；多數道具單價 0 由使用者自填，少數熱門道具帶市場參考預設價（可能過時，故僅作起點、隨時可改）。
- [舊存檔含 exp 欄位／非數值欄位] → deserialize 明確忽略未知鍵、安全轉型；verify 腳本含「載入 legacy 含 exp 紀錄」案例。
- [版面從單欄改雙欄＋底部，回歸風險] → 保留既有 row/section 元件，僅重排容器；以 verify 腳本與手動啟動驗證。

## Migration Plan

- 讀：deserialize 忽略 exp_*，缺 item_rows 補空 list，數值安全轉型。
- 寫：serialize/autosave 改新 schema（無 exp、有 item_rows，仍含 duration_minutes）。
- 回退：移除本變更後，新存檔的 item_rows 會被舊程式忽略，exp 欄位則因本頁不再產生而為 0；不致崩潰。

## Open Questions

(none)
