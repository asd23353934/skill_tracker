## Why

Artale 玩家經常需要監控遊戲內頻道廣播訊息（交易、徵人等），目前需要開啟外部工具或持續盯著遊戲畫面。參考開源專案 Artale-Channel-Broadcast-System，在技能追蹤器內整合頻道廣播監控頁面，讓玩家在同一個桌面工具中即可即時瀏覽、篩選頻道訊息。

## What Changes

- 新增「頻道廣播」頁面，透過封包監聽 (Scapy AsyncSniffer, TCP port 32800) 即時擷取遊戲頻道訊息
- 提供啟動 / 暫停 / 清除控制按鈕
- 可勾選「自動啟動」，每次開啟程式時自動開始監聽
- 支援分類篩選：預設「全部」，使用者可新增關鍵字進行訊息過篩
- 訊息列表顯示頻道、暱稱、內容、時間戳，可複製 FriendTag（暱稱#UserId）
- 黑名單功能：封鎖特定玩家，隱藏其訊息
- 免責聲明對話框：首次使用時顯示，告知使用者此功能為純封包監聽、不修改遊戲資料

## Capabilities

### New Capabilities

- `channel-broadcast`: 頻道廣播監控頁面 — 封包擷取、訊息解析、即時顯示、篩選、黑名單、FriendTag 複製、免責聲明

### Modified Capabilities

（無）

## Impact

- 新增檔案：`src/ui/pages/broadcast_page.py`（頁面 UI）、`src/ui/broadcast_manager.py`（封包監聽與解析）
- 修改檔案：`src/ui/pages/__init__.py`、`src/ui/sidebar.py`、`src/ui/app.py`（註冊新頁面）
- 新增依賴：`scapy`（封包擷取，需 Npcap）
- `config.json` 的 `settings` 新增廣播相關設定（auto_start、blacklist、keywords）
