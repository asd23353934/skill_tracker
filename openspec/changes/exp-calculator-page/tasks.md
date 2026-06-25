## 1. Domain：經驗表與服務

- [x] 1.1 新增 src/domain/exp_table.py 落實「經驗表資料：pre-Big-Bang Lv1–199 內建常量」：EXP_TO_NEXT Lv1–199；apply 時跨至少兩來源核對整表並列抽樣值給使用者確認（對應 spec「Classic EXP table data」）
- [x] 1.2 新增 src/domain/exp_service.py 的 exp_remaining，落實「升級所需經驗計算：目前等級 % ＋ 整級加總」（對應 spec「Compute remaining EXP to a target level」）
- [x] 1.3 在 exp_service 實作「需打隻數與預估時間」kills_needed／time_hours（對應 spec「Compute kills needed and estimated time」）
- [x] 1.4 確保「純邏輯分層（exp_service 零 Qt，可 verify）」：exp_service／exp_table 不 import 任何 PySide6（對應 spec「EXP service and table remain free of Qt dependencies」）
- [x] 1.5 新增 verify_exp_service.py：斷言關鍵級數（Lv1=15／Lv2=34／Lv10=1716）、exp_remaining 範例（10,50,12 → 3218）、邊界（target<=level、零速率、Lv200 封頂）

## 2. UI：頁面與導覽

- [x] 2.1 新增 src/ui_v2/pages/exp_calculator_page_v2.py 輸入區＋結果區，走 V2Theme／lucide（對應 spec「EXP calculator page renders inputs and results」）
- [x] 2.2 實作「經驗來源：每小時經驗 或 每隻經驗 × 每小時隻數」兩模式輸入與輸入變更即時重算
- [x] 2.3 落實「頁面結構與導覽（V2 page ＋ sidebar）」：main_v2.py PAGES＋實例化、sidebar_v2.py 導覽項（lucide icon via lucide_pixmap）（對應 spec「Sidebar navigation entry for EXP calculator」）

## 3. 文件與驗證

- [x] 3.1 更新 docs/PROJECT.md：登錄經驗值計算器頁與 exp_table／exp_service domain 檔
- [x] 3.2 跑 verify_exp_service.py 全綠並啟動程式手動驗證計算器頁輸入/結果/兩種速率模式/側邊欄導覽
