## Why

使用者需要一個「升級時間估算」工具：輸入目前等級＋經驗 %、目標等級，以及練功效率（在一段區間內獲得的經驗），即可算出「還需多少經驗、距下一級還需多少、預估升級時間」。練功收支頁移除經驗欄位後，經驗相關功能集中於此新頁。

## What Changes

- 新增「經驗值計算器」頁（src/ui_v2/pages/exp_calculator_page_v2.py）：輸入區（目前等級／目前經驗 %／目標等級／練功效率）＋ 結果區（還需總經驗／距下一級還需／預估時間）。
- 新增 domain 純邏輯：src/domain/exp_table.py（經典 pre-Big-Bang 楓之谷每級所需經驗，Lv1–199，MAX_LEVEL=200；Artale 同系）與 src/domain/exp_service.py（區間經驗推每小時速率、剩餘經驗、預估時間計算，零 Qt 依賴）。
- 練功效率為**單一輸入**：一個經驗數字 ＋ 一個區間下拉（每 10 分鐘 / 30 分鐘 / 1 小時，預設 10 分鐘），由 hourly_rate 推得每小時經驗。
- 頁面註冊走既有單一來源 src/ui_v2/page_registry.py，sidebar 與 main_v2 自動同步（lucide icon，走 lucide_pixmap）。

## Non-Goals

- 不持久化計算器輸入（不動 profiles／config_user）。
- 僅支援經典 pre-Big-Bang／Artale 同系經驗曲線，不涵蓋大改版後曲線。
- 不做掉寶／楓幣估算（屬練功收支頁職責）。
- 不做跨等級多段速率混合，採單一速率估算。
- 不計算「需打隻數（kills needed）」；結果只呈現經驗與時間。

## Capabilities

### New Capabilities

- `exp-calculator`: 升級時間估算頁、其純邏輯服務（exp_service）、經驗表資料（exp_table）與側邊欄導覽項。

### Modified Capabilities

(none)

## Impact

- Affected specs: exp-calculator（new）
- Affected code:
  - New: src/domain/exp_table.py（Lv1–199 每級所需經驗常量，MAX_LEVEL=200）
  - New: src/domain/exp_service.py（純邏輯：exp_remaining／exp_remaining_in_level／hourly_rate／time_hours／format_duration）
  - New: src/ui_v2/pages/exp_calculator_page_v2.py（V2 頁面）
  - New: verify_exp_service.py（服務層驗證腳本，比照 verify_potion_service.py）
  - Modified: src/ui_v2/page_registry.py（新增 exp 頁面登錄；sidebar_v2.py 與 main_v2.py 透過此單一來源自動取得導覽項）
  - Modified: docs/PROJECT.md（新頁面登錄）
