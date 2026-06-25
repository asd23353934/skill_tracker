## 1. Domain：經驗表與服務

- [x] 1.1 新增 src/domain/exp_table.py 落實「經驗表資料：pre-Big-Bang Lv1–199 內建常量」：MAX_LEVEL=200、EXP_TO_NEXT Lv1–199；apply 時跨至少兩來源核對整表並列抽樣值給使用者確認（對應 spec「Classic EXP table data」）
- [x] 1.2 新增 src/domain/exp_service.py 的 exp_remaining／exp_remaining_in_level，落實「升級所需經驗計算：目前等級 % ＋ 整級加總」（對應 spec「Compute remaining EXP to a target level」「Compute remaining EXP within the current level」）
- [x] 1.3 在 exp_service 實作「練功效率：單一輸入」hourly_rate（區間經驗推每小時）與「預估時間」time_hours／format_duration（HH:MM:SS）（對應 spec「Derive hourly EXP rate from an interval sample」「Estimate time and format as HH:MM:SS」）
- [x] 1.4 確保「純邏輯分層（exp_service 零 Qt，可 verify）」：exp_service／exp_table 不 import 任何 PySide6（對應 spec「EXP service and table remain free of Qt dependencies」）
- [x] 1.5 新增 verify_exp_service.py：斷言關鍵級數（Lv1=15／Lv2=34／Lv10=1716）、exp_remaining 範例（10,50,12 → 3218）、邊界（target<=level、零速率、Lv200 封頂）、hourly_rate（10/30/60 分鐘區間）、format_duration（HH:MM:SS）

## 2. UI：頁面與導覽

- [x] 2.1 新增 src/ui_v2/pages/exp_calculator_page_v2.py 輸入區＋結果區（結果只三項：還需總經驗／距下一級還需／預估時間），走 V2Theme／lucide（對應 spec「EXP calculator page renders inputs and results」）
- [x] 2.2 實作「練功效率：單一輸入（區間經驗 ＋ 區間下拉）」（一個經驗數字 ＋ 區間下拉 10/30/60 分鐘，預設 10 分鐘）與輸入變更即時重算
- [x] 2.3 落實「結果只呈現三項」與「預估時間（HH:MM:SS）」：結果區顯示還需總經驗／距下一級還需／預估時間（時分秒），不持久化輸入（對應 spec「Calculator inputs are not persisted」）
- [x] 2.4 落實「頁面結構與導覽（V2 page ＋ page_registry 單一來源）」：在 src/ui_v2/page_registry.py 加入 exp 頁面登錄（PageSpec，lucide icon via lucide_pixmap），main_v2.py 與 sidebar_v2.py 自動同步（對應 spec「Sidebar navigation entry for EXP calculator」）

## 3. 文件與驗證

- [x] 3.1 更新 docs/PROJECT.md：登錄經驗值計算器頁與 exp_table／exp_service domain 檔
- [x] 3.2 跑 verify_exp_service.py 全綠並啟動程式手動驗證計算器頁輸入/結果/區間下拉/側邊欄導覽
