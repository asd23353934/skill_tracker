## Why

目前「需玩家名稱」的指令（/交換、/密語、/搜尋…）以一個可編輯下拉框輸入名稱：名稱只在「按下複製」時被動記住，且所有指令共用同一份名單。使用者想要更直接的操作 — 把常用名稱以可點擊的小塊（chips）呈現，點一下就複製「指令＋該名稱」，並能明確新增／編輯／刪除；而且每個指令各自維護自己的名單（交換對象與密語對象通常不同）。

## What Changes

- 把 needs_name 指令卡片的「可編輯名稱下拉」改為「名稱 chips 列 ＋ 一個新增名稱的輸入」。
- 點擊某個名稱 chip → 立即把「指令模板填入該名稱」的字串複製到系統剪貼簿並顯示 toast（取代原本「下拉選取 ＋ 複製鈕」的流程）。
- 每張 needs_name 卡片提供「新增名稱」輸入：送出後加入該指令的名單並顯示為新 chip。
- 每個名稱 chip 支援「編輯」（改名）與「刪除」。
- 名稱記憶改為「每個指令各自一份」：持久化結構由單一共用清單改為以指令 key 分組的 dict，存於 config_user.json 的 settings。
- 升級相容：既有共用 command_recent_names 仍可讀取（作為相容來源），缺鍵不報錯、不遺失資料。

## Non-Goals

- 不做整個指令清單（關鍵字／模板／說明）的增刪修 — 本次只針對「名稱」（使用者明確「範圍只能單一」）。
- 不更動 no-argument 指令卡片的呈現與行為。
- 不注入按鍵到遊戲，維持「僅複製到剪貼簿」的安全邊界。
- 不做名稱跨指令同步或全域共享（刻意採 per-command 獨立）。

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `command-quick-copy`: 參數化指令的名稱輸入，由「可編輯下拉＋被動記憶」改為「可點擊複製、可增刪改的名稱 chips」，且名單改為 per-command 儲存。

## Impact

- Affected specs: command-quick-copy（modified）
- Affected code:
  - Modified: src/ui_v2/pages/command_page_v2.py（needs_name 卡片改用名稱 chips ＋ 新增/編輯/刪除互動）
  - Modified: src/infrastructure/config_manager.py（per-command 名稱讀寫 API，取代並相容 command_recent_names）
  - Modified: docs/DATA_FORMAT.md（settings 內名稱儲存結構說明更新）
  - Modified: tests/test_command_recent_names.py（更新為 per-command 行為）
- 不影響其他頁面與既有 profiles 結構。
