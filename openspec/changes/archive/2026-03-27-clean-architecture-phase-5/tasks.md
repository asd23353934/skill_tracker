## 1. 新建 infrastructure 層目錄結構

- [x] 1.1 新建 `src/infrastructure/` 作為基礎設施層：建立目錄，新增空白 `__init__.py`（Infrastructure layer directory exists at src/infrastructure/）

## 2. 搬移零 Qt 依賴模組至 infrastructure

- [x] 2.1 將 `src/ui/config_manager.py` 複製到 `src/infrastructure/config_manager.py`，確認無 Qt import（ConfigManager resides in src/infrastructure/config_manager.py）
- [x] 2.2 將 `src/ui/helpers.py` 複製到 `src/infrastructure/helpers.py`，將 `user_path()` 重新命名為 `user_data_path()`（helpers module resides in src/infrastructure/helpers.py，統一 _user_path 到 helpers.py）
- [x] 2.3 將 `src/ui/sound_manager.py` 複製到 `src/infrastructure/sound_manager.py`，將 `from src.ui.overlay_manager import _user_path` 改為 `from src.infrastructure.helpers import user_data_path`，並替換所有 `_user_path` 呼叫為 `user_data_path`（SoundManager resides in src/infrastructure/sound_manager.py）
- [x] 2.4 將 `src/ui/updater.py` 複製到 `src/infrastructure/updater.py`，將內部 `from src.ui.helpers import resource_path` 改為 `from src.infrastructure.helpers import resource_path`（Updater resides in src/infrastructure/updater.py）
- [x] 2.5 將 `src/ui/broadcast_manager.py` 複製到 `src/infrastructure/broadcast_manager.py`，確認無 Qt import（BroadcastManager resides in src/infrastructure/broadcast_manager.py）

## 3. Repository 歸屬 infrastructure

- [x] 3.1 將 `src/domain/repositories.py` 複製到 `src/infrastructure/repositories.py`，將 TYPE_CHECKING 下的 `from src.ui.config_manager import ConfigManager` 改為 `from src.infrastructure.config_manager import ConfigManager`（Repository 歸屬 infrastructure 而非 domain，repositories have zero Qt dependency）

## 4. 拆分 skill_manager 為 skill_loader + skill_pixmap_cache

- [x] 4.1 建立 `src/infrastructure/skill_loader.py`，從 `src/ui/skill_manager.py` 提取純 Python 邏輯：`_load_skills()` 資料載入、`get_skill()`、`get_all_skills()`、`get_categories()`、`update_hotkey()`、`clear_all_hotkeys()`、`get_skill_by_hotkey()`。SkillLoader 不 import PySide6 或 PIL，僅依賴 ConfigManager（SkillLoader provides pure-Python skill data access，拆分 skill_manager 為 skill_loader + skill_pixmap_cache）
- [x] 4.2 建立 `src/ui/skill_pixmap_cache.py`，從 `src/ui/skill_manager.py` 提取 Qt 圖片快取邏輯：`_pil_to_qpixmap()`、`_load_skill_image()`、四組 QPixmap dict（qpixmaps/qpixmaps_small/qpixmaps_medium/qpixmaps_card）、`skill_image_paths`。SkillPixmapCache 建構時接收 SkillLoader 取得 skill 列表及 icon 路徑（SkillPixmapCache wraps SkillLoader for Qt image caching）

## 5. 更新 src/domain/ 消除反向依賴

- [x] 5.1 更新 `src/domain/services.py`：將 TYPE_CHECKING 下的 `from src.ui.config_manager import ConfigManager` 改為 `from src.infrastructure.config_manager import ConfigManager`，將 `from src.ui.skill_manager import SkillManager` 改為 `from src.infrastructure.skill_loader import SkillLoader`，並將所有 `SkillManager` type hint 改為 `SkillLoader`（domain models have zero Qt dependency，dependency direction enforced across layers）
- [x] 5.2 刪除 `src/domain/repositories.py`（原檔案已搬到 `src/infrastructure/repositories.py`），確認 domain 層無反向 import
- [x] 5.3 更新 `src/domain/__init__.py`：移除 `from src.domain.repositories import ...`（若有），保留 models 和 services 的 re-export。確認 `src/domain/` 所有 `.py` 不 import `src.ui` 或 `src.infrastructure`（domain layer has no outward imports）

## 6. 更新 infrastructure __init__.py 公開 API

- [x] 6.1 更新 `src/infrastructure/__init__.py`，匯出 `ConfigManager`、`SkillLoader`、`SoundManager`、`BroadcastManager`、`resource_path`、`user_data_path`（infrastructure package is importable）

## 7. 一次性全量替換 import 路徑

- [x] 7.1 更新 `src/ui/app.py`：`from src.ui.config_manager` → `from src.infrastructure.config_manager`、`from src.ui.helpers` → `from src.infrastructure.helpers`、`from src.ui.sound_manager` → `from src.infrastructure.sound_manager`、`from src.ui.broadcast_manager` → `from src.infrastructure.broadcast_manager`、`from src.ui.updater` → `from src.infrastructure.updater`、`from src.ui.skill_manager import SkillManager` → 拆為 `from src.infrastructure.skill_loader import SkillLoader` + `from src.ui.skill_pixmap_cache import SkillPixmapCache`（import 更新策略：一次性全量替換）
- [x] 7.2 更新 `src/ui/app.py` 中 `SkillManager` 的建構與使用：先建 `SkillLoader(config_manager)`，再建 `SkillPixmapCache(skill_loader)`。將 `self.skill_manager` 分為 `self.skill_loader`（資料查詢）和 `self.skill_pixmap_cache`（圖片），或保留 `self.skill_manager` 指向 `SkillPixmapCache`（向後相容）加 `self.skill_loader` 指向 `SkillLoader`
- [x] 7.3 更新 `src/ui/window_manager.py`：`from src.ui.helpers import resource_path` → `from src.infrastructure.helpers import resource_path`
- [x] 7.4 更新 `src/ui/pages/monster_page.py`：`from src.ui.helpers import resource_path` → `from src.infrastructure.helpers import resource_path`
- [x] 7.5 更新 `src/ui/pages/mapleworld_page.py`：`from src.ui.helpers import user_path` → `from src.infrastructure.helpers import user_data_path`，並將所有 `user_path(...)` 呼叫改為 `user_data_path(...)`
- [x] 7.6 更新 `src/ui/dialogs/base_dialog.py`：`from src.ui.helpers import resource_path` → `from src.infrastructure.helpers import resource_path`
- [x] 7.7 更新 `src/ui/dialogs/update_dialog.py`：`from src.ui.updater import Updater` → `from src.infrastructure.updater import Updater`
- [x] 7.8 更新 `src/ui/overlay_manager.py`：刪除 `_user_path()` 函數定義，改為 `from src.infrastructure.helpers import user_data_path`，將所有 `_user_path(...)` 呼叫替換為 `user_data_path(...)`（統一 _user_path 到 helpers.py）
- [x] 7.9 更新 `src/ui/pages/overlay_page.py`：`from src.ui.overlay_manager import _user_path` → `from src.infrastructure.helpers import user_data_path`，將 `_user_path(...)` 呼叫替換為 `user_data_path(...)`
- [x] 7.10 更新 `src/domain/services.py` 的 `from src.domain.repositories import` → `from src.infrastructure.repositories import`
- [x] 7.11 更新 `src/ui/app.py` 的 `from src.domain.repositories import` → `from src.infrastructure.repositories import`

## 8. 刪除舊檔案

- [x] 8.1 刪除 `src/ui/config_manager.py`（已搬到 infrastructure）
- [x] 8.2 刪除 `src/ui/helpers.py`（已搬到 infrastructure）
- [x] 8.3 刪除 `src/ui/sound_manager.py`（已搬到 infrastructure）
- [x] 8.4 刪除 `src/ui/updater.py`（已搬到 infrastructure）
- [x] 8.5 刪除 `src/ui/broadcast_manager.py`（已搬到 infrastructure）
- [x] 8.6 刪除 `src/ui/skill_manager.py`（已拆分為 skill_loader + skill_pixmap_cache）

## 9. PyInstaller spec 同步更新

- [x] 9.1 檢查並更新 `skill_tracker.spec` 的 `hiddenimports`，新增 `src.infrastructure.*` 模組路徑，移除舊路徑（PyInstaller spec 同步更新）

## 10. 驗證

- [x] 10.1 執行 `python main.py` 確認應用程式正常啟動、所有頁面可切換、技能倒數正常
- [x] 10.2 用 grep 全量搜索確認無殘留的 `from src.ui.config_manager`、`from src.ui.helpers`、`from src.ui.sound_manager`、`from src.ui.updater`、`from src.ui.broadcast_manager`、`from src.ui.skill_manager`、`from src.domain.repositories` 等舊路徑 import
- [x] 10.3 確認 `src/domain/` 所有 `.py` 檔不包含 `src.ui` 或 `src.infrastructure` 的 import（infrastructure modules have zero Qt dependency）
- [x] 10.4 確認 `src/infrastructure/` 所有 `.py` 檔不包含 PySide6 import（infrastructure modules have zero Qt dependency）
