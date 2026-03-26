## Context

技能追蹤器目前提供技能倒數、怪物重生、覆蓋圖片、藥水費用、MapleWorld 資源等頁面。玩家在遊戲中需要監控頻道廣播（交易訊息等），目前需使用外部工具。參考開源專案 Artale-Channel-Broadcast-System，將頻道廣播監控整合進技能追蹤器，讓玩家在同一工具中完成所有操作。

## Goals / Non-Goals

**Goals:**

- 在技能追蹤器新增「頻道廣播」頁面，即時顯示遊戲頻道訊息
- 提供啟動/暫停/清除操作，以及自動啟動選項
- 支援關鍵字分類篩選、黑名單過濾
- 可複製玩家 FriendTag（暱稱#UserId）
- 首次使用時顯示免責聲明

**Non-Goals:**

- 不做 Discord Bot 整合
- 不做 WebSocket 伺服器（純本機監聽）
- 不修改遊戲封包（純被動監聽）
- 不做訊息持久化儲存（僅記憶體中暫存）

## Decisions

### 封包監聽架構 — BroadcastManager

使用 Scapy `AsyncSniffer` 監聽 TCP port 32800，在獨立 daemon thread 中執行。解析邏輯參考 Artale-Channel-Broadcast-System 的 ChatParser：搜尋 `TOZ ` 標記、讀取欄位（Nickname、Text、Type、ProfileCode、UserId）、偵測頻道編號。

**替代方案**：使用 raw socket 或 pyshark。Scapy 生態成熟、文件豐富，且原始專案已驗證可行，選擇沿用。

解析後的訊息透過 `app.after(0, callback)` 排回主執行緒更新 UI，符合現有架構的執行緒安全模式。

### 頁面 UI 結構 — BroadcastPage

遵循現有頁面模式（繼承 QWidget、接受 parent/app 參數）：

- **頂部控制列**：啟動/暫停按鈕、清除按鈕、自動啟動勾選框
- **篩選列**：分類下拉選單（全部 + 使用者自訂關鍵字）、關鍵字管理（新增/刪除）
- **訊息列表**：QScrollArea 內的訊息卡片，每張顯示頻道、暱稱、內容、時間戳，右鍵選單可複製 FriendTag 或加入黑名單
- **底部**：黑名單管理按鈕、訊息計數

### 資料存放位置

廣播設定存入 `config.json` → `settings`（跨配置共用）：
- `broadcast_auto_start`: bool
- `broadcast_blacklist`: list[str]（FriendTag 格式）
- `broadcast_keywords`: list[str]（篩選關鍵字）
- `broadcast_max_messages`: int（顯示上限，預設 200）

這些設定不屬於配置可變區（不因 profile 而異），適合放在全域 settings。

### 免責聲明

首次點擊啟動時彈出 BaseDialog 風格的免責聲明對話框，告知：純封包監聽、不修改遊戲、需安裝 Npcap、使用風險自負。使用者同意後記錄到 `settings.broadcast_disclaimer_accepted`，後續不再顯示。

## Risks / Trade-offs

- **[需要管理員權限]** → Scapy 封包監聽需要管理員權限與 Npcap。在免責聲明中明確告知，啟動失敗時顯示 Toast 提示安裝 Npcap。
- **[新增依賴 scapy]** → 增加打包體積約 10-15MB。考慮到功能價值，這是可接受的取捨。需更新 `requirements.txt` 與 `skill_tracker.spec`。
- **[記憶體使用]** → 長時間運行可能累積大量訊息。設定 `broadcast_max_messages` 上限（預設 200），超過時移除最舊訊息。
- **[封包格式變更]** → 遊戲更新可能改變封包格式。解析邏輯集中在 BroadcastManager，便於日後維護。
