## 1. 基礎建設

- [x] 1.1 新增 `scapy` 至 `requirements.txt`，更新 `skill_tracker.spec` 的 hiddenimports 處理 Npcap 依賴
- [x] 1.2 依資料存放位置設計，在 `config.json` → `settings` 新增廣播相關欄位（broadcast_auto_start、broadcast_blacklist、broadcast_keywords、broadcast_max_messages、broadcast_disclaimer_accepted），更新 ConfigManager 讀寫邏輯

## 2. 封包監聽架構 — BroadcastManager

- [x] 2.1 建立 `src/ui/broadcast_manager.py`，實作封包擷取與訊息解析（packet capture and message parsing）：AsyncSniffer daemon thread、TOZ 標記搜尋、欄位解析（Nickname/Text/Type/ProfileCode/UserId/Channel）
- [x] 2.2 實作 Npcap 依賴處理（Npcap dependency handling）：偵測 Scapy/Npcap 是否可用，不可用時回傳錯誤而非崩潰
- [x] 2.3 實作訊息顯示上限（message display limit）：超過 broadcast_max_messages 時移除最舊訊息
- [x] 2.4 實作黑名單過濾邏輯（blacklist management）：擷取到的訊息先比對黑名單再派發

## 3. 頁面 UI 結構 — BroadcastPage

- [x] 3.1 建立 `src/ui/pages/broadcast_page.py`，實作頁���註冊（page registration）：繼承 QWidget、匯出至 `pages/__init__.py`、加入 `sidebar.py` PAGES、在 `app.py` `_build_ui()` 初始化
- [x] 3.2 實作啟動/��停/清除控制列（start, pause, and clear controls）
- [x] 3.3 實作自動啟動勾選框（auto-start option），綁定 settings.broadcast_auto_start
- [x] 3.4 實作分類關鍵字篩選 UI（category keyword filtering）：下拉選單（全部 + 自訂關鍵字）、新增/刪除關鍵字按鈕
- [x] 3.5 實作訊息卡��列表：顯示頻道���暱稱、內容、時間戳
- [x] 3.6 實��複製 FriendTag 功能（copy FriendTag）：右鍵選單與按鈕，複製「暱稱#UserId」至剪貼簿
- [x] 3.7 實作黑名單��理 UI（blacklist management）：右鍵選單加入黑名單、黑名單管理對話框（檢視/移除）

## 4. 免責聲明

- [x] 4.1 建立免責聲明對話框（disclaimer dialog）：繼承 BaseDialog，說明純封包監聽、需 Npcap、風險自負
- [x] 4.2 整合免責聲明流程：首次啟動時攔截，接受後記錄 settings.broadcast_disclaimer_accepted

## 5. 整合與驗證

- [x] 5.1 整合 BroadcastManager 與 BroadcastPage，串接 app.after(0, callback) 執行緒安全派發
- [x] 5.2 測試完整流程：啟動/暫停/清除、關鍵字篩選、FriendTag 複製、黑名單、免責聲明、自動啟動
