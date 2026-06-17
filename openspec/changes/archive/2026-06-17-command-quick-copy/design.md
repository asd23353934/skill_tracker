## Context

Artale（楓之谷世界）有一組固定的遊戲內聊天指令，社群整理出常用清單（研究來源見 proposal）。玩家在戰鬥 / 交易 / 私訊時需手打這些指令；其中「/交換」「/密語」需帶上對方含「#代碼」的完整玩家 ID，重打慢且易錯。

本專案為 PySide6 桌面應用，既有 5 個 V2 頁（技能 / 怪物 / 浮動圖片 / 練功水錢 / 資源中心）皆放在 `src/ui_v2/pages/`，透過側邊欄（`src/ui_v2/sidebar_v2.py`）切換、由 `main_v2.py` 協調；全域可變設定存於 `config_user.json` 的 settings 區（由 `src/infrastructure/config_manager.py` 管理）。本功能新增第 6 個頁，遵循相同模式。

## Goals / Non-Goals

**Goals:**

- 一頁列出常用 Artale 指令，每個一鍵複製到系統剪貼簿。
- 需參數指令可填玩家名稱並記住用過的（含 #代碼），下拉快速重用。
- 指令清單資料驅動、集中定義、易擴充。

**Non-Goals:**

- 不自動輸入到遊戲（僅複製，避免反作弊判定）。
- 不做雲端 / 線上指令同步。
- 不驗證玩家名稱格式（僅去前後空白、去重）。
- 不更動 config.json 靜態區或既有 data-format 分區規範。

## Decisions

### 指令以 UI 層模組常量集中定義（資料驅動）

指令清單定義為指令頁模組內的模組常量（一個 list，每筆為小型結構：`key` / `label` / `template` / `description` / `needs_name`）。`template` 對需參數指令含 `{name}` 佔位（如「/交換 {name}」），無參數指令即完整指令字串。

- 理由：這些是 app 提供的呈現資料（屬 UI 層），非使用者資料；用模組常量最簡單、最易擴充，且不需動 config.json 靜態區或 data-format spec。
- 替代方案（否決）：放 config.json 的新 commands 區 → 會牽動 data-format 分區與 release strip 流程，過度設計。

### 複製到系統剪貼簿，不自動輸入遊戲

「複製」鈕呼叫 `QApplication.clipboard().setText(...)`，並以既有 Toast 回饋「已複製」。

- 理由：模擬鍵盤把字串注入遊戲程序有觸發反作弊的風險；複製 + 玩家手動貼上安全且足夠。
- 替代方案（否決）：用 pynput 自動 type 到前景遊戲 → 反作弊風險，否決。

### 需參數指令的玩家名稱填入與佔位代入

需參數的卡片含一個可編輯下拉（沿用 `src/ui_v2/components.py` 的 ArrowComboBox 或 QComboBox 編輯模式）：可直接輸入新名稱，下拉列「最近用過的名稱」。按複製時取當前文字（去前後空白），以 `{name}` 佔位代入 template；名稱為空時複製到「指令關鍵字 + 空格」（如「/交換 」）讓玩家在遊戲補打。

- 理由：一個欄位同時支援「打新名稱」與「選舊名稱」，符合使用者「填入並自動記錄」的需求。

### 用過的玩家名稱持久化於 config_user.json settings

最近使用的玩家名稱存為 settings 的清單欄位（`command_recent_names`: `list[str]`，最近在前、去重、上限 20）。複製需參數指令且名稱非空時，把該名稱 promote 到最前、去重、截斷，並經 `config_manager.save()` 持久化。頁面透過 `self.app` 取得清單與「新增名稱」方法（讀寫委派給 app_core / config_manager）。

- 理由：settings 是跨配置共用的全域可變區（config_user.json），交易 / 私訊對象與技能配置無關，放全域最合適；名稱含 #代碼原樣保存；屬既有 settings 區的新欄位，不改變 data-format 分區規範。
- 替代方案（否決）：存 profiles/{name}.json（per-config）→ 對象與配置無關，否決；獨立新檔 → settings 已是小型全域清單的自然歸宿，否決。

### 側邊欄導覽與頁面註冊

於 `src/ui_v2/sidebar_v2.py` 新增一個 lucide 導覽項，並在 `main_v2.py` 的頁面堆疊與切換接線中註冊新頁，沿用既有 5 頁的註冊模式（實作時對照既有頁註冊處）。圖示走 `lucide_pixmap`；若選用的 lucide SVG（如 terminal）尚未存在於 `src/ui_v2/icons/`，新增對應 SVG（同 info.svg 前例）。

- 理由：與既有頁一致的整合方式，最低認知成本。

## Risks / Trade-offs

- [玩家名稱含 #代碼，使用者可能打錯] → 只去空白去重不驗證；下拉記憶降低重打錯誤機率。
- [複製非自動輸入，玩家仍需手動貼上] → 設計取捨（反作弊安全），可接受。
- [選用的 lucide 圖示可能無對應 SVG] → 缺則新增 SVG（同 info.svg 前例）。
- [command_recent_names 無上限會膨脹] → 上限 20、promote + 去重 + 截斷。
- [既有 config_user.json 升級無此欄位] → 缺鍵時讀為空清單，向後相容。

## Open Questions

- 側邊欄圖示選哪個 lucide（terminal / copy / clipboard）—— 實作時挑語意最貼切者。
- 指令種子用 8 條（核心 6 條 + /mute + /desummon）；清單資料驅動，使用者可後續增減。
