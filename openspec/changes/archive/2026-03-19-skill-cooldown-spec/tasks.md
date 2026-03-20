## 1. 建立規格文件

- [x] 1.1 將 `specs/skill-cooldown/spec.md` 移至 `openspec/specs/skill-cooldown/spec.md`
- [x] 1.2 確認 Cooldown Trigger via Hotkey 規格與 `hotkey_manager.py` 及 `window_manager.py` 實作一致
- [x] 1.3 確認 Countdown Timer Accuracy 規格與 `skill_window.py` 計時器使用 QTimer 輪詢（100ms/50ms）邏輯一致
- [x] 1.4 確認 Skill States 規格與技能狀態以布林字典集中管理（App 層）的實作一致
- [x] 1.5 確認 Cooldown Duration Override 規格與覆寫系統（cooldown / alert_seconds / sound）存於 profiles 的實作一致

## 2. 驗證規格完整性

- [x] 2.1 確認 Alert System 規格中的一次性觸發行為（警報為一次性觸發，以 alert_triggered 旗標防重複）描述正確
- [x] 2.2 確認 Overlay Progress Visualization 規格中的覆蓋比例計算與 `skill_window.py` `_update_overlay()` 一致
- [x] 2.3 確認跨執行緒透過 _Dispatcher 排回主執行緒的規格描述在 Cooldown Trigger via Hotkey 中已涵蓋
- [x] 2.4 執行 `spectra validate skill-cooldown-spec` 確認無錯誤

## 3. 更新 openspec/config.yaml

- [x] 3.1 在 `openspec/config.yaml` 加入專案 context（技術棧、慣例），讓後續 spec 共享背景知識
