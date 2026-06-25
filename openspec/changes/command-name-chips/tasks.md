## 1. 資料層：ConfigManager per-command 名稱

- [x] 1.1 在 src/infrastructure/config_manager.py 實作「per-command 名稱儲存結構」API：get_command_names(key) / add_command_name(key,name) / remove_command_name(key,name) / rename_command_name(key,old,new)，寫入 settings.command_names；沿用 MRU 置前、去重、上限 20、verbatim #（對應 spec「Remember used player names」）
- [x] 1.2 在 ConfigManager 實作「升級相容（非破壞遷移）」fallback：command_names 缺鍵時以舊 command_recent_names 作唯讀種子、不改寫舊鍵；兩者皆缺回空（對應 spec「Backward-compatible recent-names storage」）
- [x] 1.3 更新 tests/test_command_recent_names.py 為 per-command 行為（promotion/insertion/cap、per-command 隔離、legacy fallback）

## 2. UI：名稱 chips

- [x] 2.1 改寫 src/ui_v2/pages/command_page_v2.py 的 needs_name 卡片：以「名稱以 chips 呈現，點擊即複製」取代 ArrowComboBox — chips 列（FlowLayout）＋ 新增名稱輸入；chip 與刪除鈕走 V2Theme/lucide（對應 spec「Parameterized commands substitute a player name」）
- [x] 2.2 實作點擊 chip → 以 cmd.template.format(name=…) 複製「指令＋名稱」並 toast，並把該名稱 MRU 置前
- [x] 2.3 實作「新增同時複製並保存（合併舊 auto-save 行為）」：新增輸入送出非空 → 複製並保存為 chip；空送出 → 複製關鍵字＋單一尾空格且不新增 chip
- [x] 2.4 實作 chip 刪除（× 鈕）與就地編輯（雙擊改名、Enter 確認 / Esc 取消），每次操作即時持久化（對應 spec「Remember used player names」之增刪改）

## 3. 文件與驗證

- [x] 3.1 更新 docs/DATA_FORMAT.md：settings.command_names 結構與 legacy 相容說明
- [x] 3.2 跑 tests/ 全綠並啟動程式手動驗證指令頁 chips 之新增/編輯/刪除/點擊複製與空送出語意
