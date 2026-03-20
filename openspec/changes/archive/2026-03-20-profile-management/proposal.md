# profile-management

## Why

配置管理（Profile）系統是應用程式核心功能之一，支援多角色配置切換，
但目前缺乏正式規格，Profile 的 CRUD、切換邏輯、狀態重置行為均無文件記錄，
維護者難以判斷修改是否符合設計意圖。

## What Changes

- 建立 `profile-management` 規格，正式記錄：
  - Profile 的建立、載入、儲存、刪除、重命名行為
  - 切換 Profile 時的技能狀態重置順序
  - `current_profile` 的持久化機制
  - `load_profile()` 的缺失欄位補足規則
  - 安全性：檔名驗證防止 Path Traversal

## Capabilities

### New Capabilities

- `profile-management`: 配置管理規格，涵蓋 CRUD、切換狀態重置、檔名安全驗證

### Modified Capabilities

（無）

## Impact

- Affected specs: `profile-management`（新建）
- Affected code:
  - `src/ui/config_manager.py`（所有 profile CRUD 方法）
  - `src/ui/app.py`（`_apply_profile()`、`auto_save_current_profile()`、`_get_current_settings()`）
  - `src/ui/dialogs/profile_dialog.py`（Profile 管理 UI）
