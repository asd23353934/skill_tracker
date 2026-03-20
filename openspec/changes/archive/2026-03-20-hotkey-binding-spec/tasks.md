## 1. 規格對照驗證

- [x] 1.1 確認 `HotkeyManager.start()` 符合「Global keyboard listener」規格：listener 為 daemon thread，應用啟動時即啟動
- [x] 1.2 確認「Hotkey namespaces are isolated」規格：技能與怪物快捷鍵命名空間隔離，相同按鍵可分別指定（對照設計決策：快捷鍵命名空間隔離）
- [x] 1.3 確認「Hotkey capture mode」規格：`begin_capture()` 進入捕捉模式、`enabled=False` 暫停觸發，對照設計決策「捕捉期間暫停觸發」
- [x] 1.4 確認「Key normalization」規格：所有快捷鍵值儲存與比對均為大寫字串
- [x] 1.5 確認「Skill hotkey storage」規格：技能快捷鍵僅存於 `profiles/{name}.json → hotkeys`，設計決策「快捷鍵儲存位置分離」
- [x] 1.6 確認「Monster hotkey storage」規格：怪物快捷鍵存於 `config.json → monsters[].hotkey`，設計決策「快捷鍵儲存位置分離」
- [x] 1.7 確認「Hotkey trigger dispatch」規格：先查技能命名空間、再查怪物命名空間，均透過 `app.after(0, ...)` 排回主執行緒
- [x] 1.8 確認「Thread safety for UI updates」規格：所有 pynput 事件觸發的 UI 操作均透過 `app.after(0, func)` 排隊，對照設計決策「執行緒安全：UI 操作必須回主執行緒」

## 2. 不一致修正

- [x] 2.1 若 `config.json → skills[].hotkey` 欄位仍存在（已知問題），確認 `HotkeyManager` 不讀取此欄位，僅從 profile 讀取
- [x] 2.2 若 `_capture_hotkey` 中技能快捷鍵更新直接修改 `skill["hotkey"]` 而非寫入 profile，修正為透過 profile 層持久化

## 3. 程式碼文件補齊

- [x] 3.1 在 `hotkey_manager.py` 補充 module docstring，說明兩個命名空間的隔離規則與執行緒安全約束
- [x] 3.2 在 `HotkeyManager.begin_capture()` 加上 docstring，說明進入捕捉模式的前置條件與後置效果
- [x] 3.3 在 `HotkeyManager._on_key_press()` 加上 docstring，說明觸發優先順序（技能先、怪物後）
