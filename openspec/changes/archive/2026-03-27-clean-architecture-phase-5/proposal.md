## Why

Phase 1-4 建立了 `src/domain/` 層（models、repositories、services），但 `src/domain/` 的 type hint 仍反向依賴 `src/ui/config_manager` 和 `src/ui/skill_manager`，違反整潔架構的依賴方向規則。此外，`config_manager.py`、`helpers.py`、`sound_manager.py` 等**零 Qt 依賴**的基礎設施檔案錯放在 `src/ui/`，造成層級邊界模糊。需要將檔案歸位到正確的架構層級，消除內層 → 外層依賴。

## What Changes

- 新增 `src/infrastructure/` 目錄，作為基礎設施層（資料存取、檔案 I/O、音效、網路）
- 搬移零 Qt 依賴的檔案：
  - `src/ui/config_manager.py` → `src/infrastructure/config_manager.py`
  - `src/ui/helpers.py` → `src/infrastructure/helpers.py`
  - `src/ui/sound_manager.py` → `src/infrastructure/sound_manager.py`
  - `src/ui/updater.py` → `src/infrastructure/updater.py`
  - `src/ui/broadcast_manager.py` → `src/infrastructure/broadcast_manager.py`
- 搬移 Repository 層：`src/domain/repositories.py` → `src/infrastructure/repositories.py`（Repository 屬 infrastructure 而非 domain）
- 更新 `src/domain/services.py` 的 TYPE_CHECKING import，從 `src.infrastructure.*` 引入，消除 domain → ui 依賴
- 拆分 `src/ui/skill_manager.py` 為：
  - `src/infrastructure/skill_loader.py`（純 Python 技能資料載入 + config dict 管理）
  - `src/ui/skill_pixmap_cache.py`（Qt QPixmap/QImage 快取，依賴 skill_loader）
- 統一 `_user_path()` 工具函數：移除 `overlay_manager.py` 中的重複定義，統一使用 `src/infrastructure/helpers.py`
- 更新全專案 import 路徑（約 40+ 個 import 語句）

## Non-Goals

- 不遷移 `theme.py`（雖只有一個 QFont import，但被 20+ 個 UI 檔案引用，搬移風險高、收益低）
- 不遷移 `hotkey_manager.py`、`window_manager.py`、`overlay_manager.py`（它們操作 Qt widget 生命週期，屬於 UI 層）
- 不改變任何業務邏輯或功能行為
- 不改變 config.json / profiles/*.json 的格式

## Capabilities

### New Capabilities

- `infrastructure-layer`: 基礎設施層目錄結構與模組歸屬規則，定義 `src/infrastructure/` 的職責邊界和依賴方向約束

### Modified Capabilities

- `data-repositories`: Repository 從 `src/domain/` 搬到 `src/infrastructure/`，import 路徑變更
- `domain-models`: 消除 domain 層對 ui 層的 TYPE_CHECKING 依賴，改為依賴 infrastructure 層

## Impact

- 受影響的 specs：`infrastructure-layer`（新）、`data-repositories`（路徑變更）、`domain-models`（依賴方向修正）
- 受影響的程式碼：
  - **搬移的檔案**（6 個）：config_manager、helpers、sound_manager、updater、broadcast_manager、repositories
  - **拆分的檔案**（1 個）：skill_manager → skill_loader + skill_pixmap_cache
  - **import 更新**（約 40+ 個檔案）：所有引用上述模組的檔案需更新 import 路徑
  - `src/domain/services.py`：TYPE_CHECKING import 改為 `src.infrastructure.*`
  - `src/domain/__init__.py`：更新 re-export
  - `src/infrastructure/__init__.py`：新建，匯出公開 API
