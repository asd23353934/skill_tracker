## 1. 指令資料與頁面骨架

- [x] 1.1 依「指令以 UI 層模組常量集中定義（資料驅動）」，在指令頁模組定義指令目錄常量（key / label / template / description / needs_name），並實作 Seed command catalog 的 8 條種子（「/箭頭」「/r」「/關閉」「/放煙火」「/mute」「/desummon」無參數；「/交換 {name}」「/密語 {name}」需參數）
- [x] 1.2 建立 Command quick-copy page（`src/ui_v2/pages/command_page_v2.py`，繼承 QWidget），把目錄渲染為卡片清單（每卡：指令文字 + 用途說明 + 複製鈕），主題用 V2Theme、圖示走 lucide_pixmap

## 2. 複製與參數代入

- [x] 2.1 依「複製到系統剪貼簿，不自動輸入遊戲」，實作 Copy command to system clipboard：複製鈕呼叫 `QApplication.clipboard().setText()`、以既有 Toast 回饋「已複製」、不注入任何按鍵
- [x] 2.2 依「需參數指令的玩家名稱填入與佔位代入」，實作 Parameterized commands substitute a player name：needs_name 卡片加可編輯下拉名稱欄，複製時將去空白的名稱以 `{name}` 代入 template；名稱為空時複製「關鍵字 + 單一空格」

## 3. 名稱記憶（持久化）

- [x] 3.1 依「用過的玩家名稱持久化於 config_user.json settings」，在 `src/infrastructure/config_manager.py` 與 `src/ui/app_core.py` 實作 command_recent_names 的讀取與「新增名稱」：promote 到最前、去重、上限 20、含「#」後綴原樣保存、經 `config_manager.save()` 持久化
- [x] 3.2 接線 Remember used player names：複製非空名稱時呼叫新增並刷新所有參數卡片的名稱下拉；確保 Backward-compatible recent-names storage（config_user.json 缺該欄位時讀為空清單、不報錯）

## 4. 導覽接線

- [x] 4.1 依「側邊欄導覽與頁面註冊」，實作 Sidebar navigation entry：於 `src/ui_v2/sidebar_v2.py` 新增 lucide 導覽項、於 `main_v2.py` 註冊指令頁並接好切換；若選用的 lucide SVG 尚未存在則新增到 `src/ui_v2/icons/`

## 5. 驗證

- [x] 5.1 新增 `tests/test_command_recent_names.py`（純邏輯層）：覆蓋名稱 promote / 去重 / 上限 20 / 缺欄位讀為空，對應 Remember used player names 與 Backward-compatible recent-names storage
- [x] 5.2 offscreen smoke：啟動 app 與指令頁渲染種子卡片；複製無參數指令驗證剪貼簿內容正確、參數指令代入名稱正確、複製後名稱出現在下拉
