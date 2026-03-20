## 1. 規格驗證

- [x] 1.1 確認 `ConfigManager._validate_filename()` 符合「Profile filename security validation」規格：空字串、含 `/`/`\`/`..` 均被拒絕
- [x] 1.2 確認所有 CRUD 方法（list/save/load/delete/rename）均先呼叫 `_validate_filename()`，符合「Profile CRUD operations」規格
- [x] 1.3 確認 `load_profile()` 對缺失欄位補足空字典，符合「Missing profile fields are filled on load」規格（對照設計決策「load_profile 缺失欄位補足」）
- [x] 1.4 確認 `_apply_profile()` 先重置再套用的執行順序，符合「Profile switch resets skill state before applying」規格（對照設計決策「切換時先重置後套用」）
- [x] 1.5 確認 `set_current_profile()` 呼叫 `save()` 持久化，符合「current_profile is persisted in settings」規格
- [x] 1.6 確認 `ensure_default_profile()` 在首次啟動時建立預設配置，符合「Default profile is ensured on startup」規格

## 2. 安全性補充

- [x] 2.1 確認 `_validate_filename()` 防護範圍涵蓋所有 CRUD 方法（對照設計決策「檔名安全驗證（Path Traversal 防護）」）

## 3. 程式碼文件

- [x] 3.1 在 `config_manager.py` 補充或確認 `_apply_profile` 相關方法的 docstring，說明重置順序
- [x] 3.2 在 `config_manager.py` 確認 `load_profile()` docstring 說明缺失欄位補足行為
