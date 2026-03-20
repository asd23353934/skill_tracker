## 1. 視窗生命週期驗證

- [x] 1.1 確認 `toggle()` 開關行為，符合「Toggle opens or closes a window」規格
- [x] 1.2 確認 `open_window()` 在圖片不存在時不報錯，符合「Open window requires existing image file」規格

## 2. 持久化行為驗證

- [x] 2.1 確認 `set_alpha()` 立即更新視窗並持久化（`round(alpha, 2)`），符合「Alpha update is immediate and persisted」規格
- [x] 2.2 確認拖曳結束後 `_on_position_change()` 持久化 x/y，符合「Position is persisted on drag end」規格
- [x] 2.3 確認 `resize_window()` 使用關閉後重新開啟策略（50ms 延遲），符合「Size change uses close-reopen strategy」規格（對照設計決策「尺寸調整策略：關閉後重新開啟」）

## 3. 格式與尺寸驗證

- [x] 3.1 確認 `add_overlay()` 拒絕非白名單格式，符合「Image format is validated on add」規格（對照設計決策「圖片格式白名單」）
- [x] 3.2 確認初始尺寸計算最長邊 ≤ 600px，符合「Initial size is constrained to 600px on longest edge」規格（對照設計決策「初始尺寸計算」）

## 4. 路徑策略驗證

- [x] 4.1 確認 `_user_path()` 在打包/開發兩種模式下回傳正確路徑，符合「User data paths use exe-relative directory」規格（對照設計決策「使用者資料路徑與打包相容」）

## 5. 刪除行為驗證

- [x] 5.1 確認 `delete_overlay(delete_file=True)` 同時關閉視窗、移除 config 條目、刪除圖片檔案，符合「Delete overlay closes window and removes file」規格
