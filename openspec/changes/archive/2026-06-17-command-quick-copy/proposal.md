## Why

玩家在 Artale 遊戲中常需手打固定聊天指令（如「/箭頭」頭頂標記、「/交換」遠距交易、「/密語」私訊）。其中交易與私訊需帶上對方含「#代碼」的完整玩家 ID（例：Apple#aSqOX），重複手打既慢又易錯。提供一個「一鍵複製指令」的頁面，需名稱的指令自動填入並記住用過的名稱，可大幅加快遊戲中的常用操作。

## What Changes

- 新增「指令」頁（`src/ui_v2/pages/command_page_v2.py`），側邊欄新增一個 lucide 導覽圖示。
- 每個指令呈現為一張卡：指令文字 + 用途說明 + 「複製」鈕；按下即寫入系統剪貼簿，玩家切回遊戲貼上即可。
- 需參數的指令（「/交換」「/密語」）在卡片上提供「玩家名稱」輸入欄 + 下拉（最近用過的）；複製時把名稱填入完整指令（例：複製出「/交換 Apple#aSqOX」）。
- 用過的玩家名稱（含「#代碼」）持久化到 `config_user.json`（跨配置共用的全域可變區），下次開啟直接從下拉選取。
- 內建指令清單採資料驅動（集中定義、易擴充）。首版種子：「/箭頭」「/r」「/關閉」「/放煙火」「/mute」「/desummon」（無參數）、「/交換 玩家名」「/密語 玩家ID#代碼」（需名稱）。

## Non-Goals

- 不自動把指令「輸入」到遊戲（僅複製到剪貼簿）：避免模擬鍵盤注入遊戲程序而觸發反作弊判定。
- 不做指令清單的線上同步或雲端來源（內建種子 + 本地，之後手動擴充）。
- 不在此頁管理技能快捷鍵（與既有快捷鍵功能無關）。
- 不驗證玩家名稱格式或「#代碼」正確性（只做去前後空白與去重，正確性由使用者自負）。

## Capabilities

### New Capabilities

- `command-quick-copy`: 遊戲內聊天指令的一鍵複製頁。涵蓋資料驅動的指令清單、複製到系統剪貼簿、需參數指令的玩家名稱填入，以及用過名稱的記憶與下拉選取（持久化於 config_user.json）。

### Modified Capabilities

（無）

## Impact

- Affected specs: 新增 `command-quick-copy`
- Affected code:
  - New: `src/ui_v2/pages/command_page_v2.py`（指令頁）
  - Modified: `main_v2.py`（頁面註冊與側邊欄頁面切換接線）
  - Modified: `src/ui_v2/sidebar_v2.py`（新增「指令」導覽項）
  - Modified: `src/infrastructure/config_manager.py`（於 config_user.json 的 settings 讀寫「最近使用的玩家名稱」清單）
  - New: `src/ui_v2/icons/terminal.svg`（若所選 lucide 圖示尚未存在則新增對應 SVG）
