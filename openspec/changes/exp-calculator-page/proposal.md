## Why

使用者需要一個「升級時間估算」工具：輸入目前等級＋經驗 %、目標等級，以及每小時經驗（或每隻經驗 × 每小時隻數），即可算出「還需多少經驗、要打幾隻、預估升級時間」。練功水頁移除經驗欄位後，經驗相關功能集中於此新頁。

## What Changes

- 新增「經驗值計算器」頁（src/ui_v2/pages/exp_calculator_page_v2.py）：輸入區（目前等級／目前經驗 %／目標等級／經驗來源）＋ 結果區（還需總經驗／距下一級還需／需打隻數／預估時間）。
- 新增 domain 純邏輯：src/domain/exp_table.py（經典 pre-Big-Bang 楓之谷每級所需經驗，Lv1–199；Artale 同系）與 src/domain/exp_service.py（區間經驗、需打隻數、預估時間計算，零 Qt 依賴）。
- 經驗來源支援兩種模式：直接填「每小時經驗」，或填「每隻經驗 × 每小時隻數」推得每小時經驗。
- 側邊欄與 main_v2 的 PAGES 新增導覽項（lucide icon，走 lucide_pixmap）。

## Non-Goals

- v1 不持久化計算器輸入（不動 profiles／config_user）。
- 僅支援經典 pre-Big-Bang／Artale 同系經驗曲線，不涵蓋大改版後曲線。
- 不做掉寶／楓幣估算（屬練功收支頁職責）。
- 不做跨等級多段速率混合，採單一速率估算。

## Capabilities

### New Capabilities

- `exp-calculator`: 升級時間估算頁、其純邏輯服務（exp_service）、經驗表資料（exp_table）與側邊欄導覽項。

### Modified Capabilities

(none)

## Impact

- Affected specs: exp-calculator（new）
- Affected code:
  - New: src/domain/exp_table.py（Lv1–199 每級所需經驗常量）
  - New: src/domain/exp_service.py（純邏輯：exp_between／kills_needed／time_estimate）
  - New: src/ui_v2/pages/exp_calculator_page_v2.py（V2 頁面）
  - New: verify_exp_service.py（服務層驗證腳本，比照 verify_potion_service.py）
  - Modified: main_v2.py（PAGES 與頁面實例化）
  - Modified: src/ui_v2/sidebar_v2.py（導覽項 ＋ lucide icon）
  - Modified: docs/PROJECT.md（新頁面登錄）
