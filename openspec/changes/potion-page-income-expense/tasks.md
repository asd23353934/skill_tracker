## 1. Domain：PotionService 與練等地圖資料

- [x] 1.1 新增 src/domain/training_maps.py 實作「練等地圖預設：內建少量可編輯掉落清單」：TRAINING_MAP_DROPS 為 地圖名 → [(道具名, 預設單價)]，少量熱門練等地圖；apply 時跨來源整理掉落與商店價並列給使用者核對
- [x] 1.2 PotionService 新增 calc_items_total，落實「服務層 income 納入物品取得；calc_summary 收斂」（對應 spec「PotionService computes item-acquisition income total」）
- [x] 1.3 改寫 calc_summary 完成「移除經驗：UI、摘要與服務 schema 全面下架」：income 納入物品取得、移除 exp_*，回傳 income/expense/net/net_10/net_60（對應 spec「PotionService computes full summary」）
- [x] 1.4 改寫 serialize/deserialize 完成「序列化相容：忽略 legacy exp、補空 item_rows」：寫 item_rows 不寫 exp、讀時忽略 legacy exp 並補空 item_rows（對應 spec「PotionService serializes and deserializes records」）
- [x] 1.5 更新 verify_potion_service.py：calc_items_total、新 summary 形狀、載入含 exp 的 legacy 紀錄案例

## 2. UI：版面重構與物品取得

- [x] 2.1 重排 potion_page_v2 完成「版面：左支出／右收入／下方總結」：上方 QHBoxLayout 左=藥水三區（支出）、右=收入（楓幣/商店/物品取得），下方橫跨總結卡（對應 spec「V2 potion page starts with empty sections」）
- [x] 2.2 落實「移除經驗：UI、摘要與服務 schema 全面下架」於 UI：刪「獲取經驗」trio 與摘要 exp 指標，摘要改 5 指標（對應 spec「V2 potion page recomputes summary on every input change」）
- [x] 2.3 新增「物品取得收入：逐項道具列（名稱＋數量＋單價）」區與列元件（名稱可編輯 / 數量 / 單價 / 唯讀收入 / 刪除）＋「＋ 新增道具」（對應 spec「V2 potion page provides item-acquisition income with map presets」）
- [x] 2.4 新增「選擇練等地圖」下拉：選取讀 training_maps 帶出可編輯掉落列，餵入 calc_items_total 計入收入
- [x] 2.5 autosave/restore/具名載入納入 item_rows，並確認舊存檔（含 exp）載入不報錯

## 3. 文件與驗證

- [x] 3.1 頁面標題收支化（main_v2.py / sidebar_v2.py tooltip 視需要）並更新 docs/DATA_FORMAT.md 之 potion 紀錄 schema 變更與相容說明
- [x] 3.2 更新 verify_potion_page_v2.py 並啟動程式手動驗證：左支出/右收入/下方總結、物品取得地圖帶出與編輯、無經驗、舊檔載入不報錯
