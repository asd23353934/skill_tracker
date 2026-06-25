## 1. Domain：PotionService 與練功地圖資料

- [x] 1.1 新增 src/domain/training_maps.py 實作「練功地圖預設：內建少量可編輯掉落清單」：TRAINING_MAP_DROPS 為 地圖名 → {level, items:[[道具名, item_id], …]}，15 張熱門練功地圖（Lv72–128）；提供 map_names / map_level / drops_for；DEFAULT_UNIT_PRICES 對照表為少數熱門道具帶預設參考價（drops_for 帶入，未列者 0）
- [x] 1.2 PotionService 新增 calc_items_total（優先 value 快路徑，否則 max(0,qty)×max(0,unit_price)），落實「服務層 income 納入物品取得」（對應 spec「PotionService computes item-acquisition income total」）
- [x] 1.3 改寫 calc_summary 完成「移除經驗與時間：UI、摘要與服務 schema 全面下架」：income 納入物品取得、移除 exp_* 與任何時間/速率指標，只回傳 income/expense/net（對應 spec「PotionService computes summary」）
- [x] 1.4 改寫 serialize/deserialize 完成「序列化相容：忽略 legacy exp、補空 item_rows」：寫 item_rows 不寫 exp（仍寫 duration_minutes）、讀時忽略 legacy exp 並補空 item_rows、數值安全轉型（對應 spec「PotionService serializes and deserializes records」）
- [x] 1.5 更新 verify_potion_service.py：calc_items_total、3 鍵 summary 形狀、載入含 exp 的 legacy 紀錄案例

## 2. UI：版面重構與物品取得

- [x] 2.1 重排 potion_page_v2 完成「版面：左支出／右收入／下方總結」：上方 QHBoxLayout 左=藥水三區（支出）、右=收入（楓幣 ・ 商店 卡 + 物品取得），下方橫跨總結卡（對應 spec「V2 potion page lays out expense, income, and summary」）
- [x] 2.2 落實「移除經驗與時間」於 UI：刪「獲取經驗」trio、練功時間列與計時器，摘要改 3 指標 總支出/總收入/淨收益（對應 spec「V2 potion page recomputes summary on every input change」）
- [x] 2.3 新增 _StackQty 組數輸入器（組數 × 組大小▼(3000/9900) + 餘數）並用於藥水前/後與物品數量（對應 spec「V2 potion page quantity inputs use stack-based entry」）
- [x] 2.4 新增「物品取得收入」區與列元件（圖示 / 名稱可編輯 / 數量 / 單價 / 唯讀收入 / 刪除）＋「新增道具」（對應 spec「V2 potion page provides item-acquisition income with map presets」）
- [x] 2.5 新增「選擇練功地圖」下拉：選取先清現有列再讀 training_maps 帶出可編輯掉落列（下拉保留所選）、「清除全部」清列並重置下拉；餵入 calc_items_total 計入收入
- [x] 2.6 autosave/restore/具名載入納入 item_rows，並確認舊存檔（含 exp）載入不報錯

## 3. 文件與驗證

- [x] 3.1 頁面標題收支化（「練功收支」）
- [x] 3.2 更新 verify_potion_page_v2.py 並啟動程式手動驗證：左支出/右收入/下方總結、_StackQty、物品取得地圖帶出與編輯、無經驗、無時間/速率、舊檔載入不報錯
