## Context

Phase 1-4 在 `src/domain/` 建立了 models、repositories、services 三個模組，但依賴方向尚未完全正確：

- `src/domain/repositories.py` 在 TYPE_CHECKING 下引用 `src.ui.config_manager`
- `src/domain/services.py` 在 TYPE_CHECKING 下引用 `src.ui.config_manager` 和 `src.ui.skill_manager`
- `config_manager.py`、`helpers.py` 等零 Qt 依賴的檔案放在 `src/ui/` 裡

目前目錄結構：
```
src/
  domain/        ← models, repositories, services
  ui/            ← 所有東西混在一起（UI + 基礎設施 + 管理器）
```

目標結構：
```
src/
  domain/        ← models, services（零外部依賴）
  infrastructure/← config, helpers, repositories, sound, updater, broadcast
  ui/            ← 純 Qt UI 元件
```

## Goals / Non-Goals

**Goals:**

- 消除 `src/domain/` 對 `src/ui/` 的所有依賴（含 TYPE_CHECKING）
- 建立 `src/infrastructure/` 層，收容零 Qt 依賴的基礎設施模組
- 拆分 `skill_manager.py` 為純資料載入（infrastructure）與 Qt 圖片快取（ui）
- 統一 `_user_path()` 重複定義
- 所有 import 路徑更新後，`python main.py` 與 `pyinstaller skill_tracker.spec` 正常運作

**Non-Goals:**

- 不搬移 `theme.py`（20+ UI 檔案引用，風險高收益低）
- 不搬移 `hotkey_manager.py`、`window_manager.py`、`overlay_manager.py`（操作 Qt widget）
- 不改變功能行為或資料格式

## Decisions

### 新建 `src/infrastructure/` 作為基礎設施層

**決策**：建立 `src/infrastructure/` 目錄，放置零 Qt 依賴的模組。

**理由**：整潔架構中，基礎設施層（I/O、檔案、網路）不屬於 domain 也不屬於 ui。獨立為一層後，依賴方向為 `ui/ → domain/` + `ui/ → infrastructure/` + `infrastructure/ → domain/`，domain 不依賴任何外層。

**替代方案**：把基礎設施檔案放進 `src/domain/`——但 domain 應該是純業務邏輯，config I/O 不是業務邏輯。

### Repository 歸屬 infrastructure 而非 domain

**決策**：`repositories.py` 從 `src/domain/` 搬到 `src/infrastructure/`。

**理由**：Repository 實作包含 ConfigManager 依賴和 JSON dict ↔ model 轉換邏輯，屬於資料存取層（infrastructure），不是純業務規則。domain 層只定義 Repository 的「介面」（透過 TYPE_CHECKING），不持有實作。

### 拆分 skill_manager 為 skill_loader + skill_pixmap_cache

**決策**：
- `src/infrastructure/skill_loader.py`：純 Python，負責從 config 載入技能 dict、合併 skills+items、提供 `get_skill()`/`get_all_skills()`/`get_skill_by_hotkey()` 查詢
- `src/ui/skill_pixmap_cache.py`：Qt 依賴，負責 QPixmap/QImage 快取、PIL 圖片處理，接收 skill_loader 作為資料來源

**理由**：現有 `skill_manager.py` 混合了資料載入（純 Python）和圖片快取（Qt）。拆分後 `services.py` 可以 type hint `SkillLoader` 而非 `SkillManager`，消除 domain → ui 依賴。

**風險**：拆分後所有呼叫 `self.app.skill_manager` 的地方需要判斷要用 `skill_loader`（資料查詢）還是 `skill_pixmap_cache`（圖片）。

### 統一 _user_path 到 helpers.py

**決策**：移除 `overlay_manager.py` 中的 `_user_path()` 重複定義，改用 `src/infrastructure/helpers.py` 的 `user_data_path()`。

**理由**：同一個函數定義在兩處，修改時容易遺漏。統一後維護成本降低。

### Import 更新策略：一次性全量替換

**決策**：所有 `from src.ui.config_manager` 改為 `from src.infrastructure.config_manager`，一次完成，不做漸進式。

**理由**：漸進式會需要在舊路徑放 re-export 兼容層，增加複雜度。此專案只有一個開發者，一次替換風險可控。

### PyInstaller spec 同步更新

**決策**：更新 `skill_tracker.spec` 的 `hiddenimports`（如果有的話）和 `pathex`，確保打包後路徑正確。

**理由**：搬移模組路徑後，PyInstaller 可能找不到動態 import 的模組。

## Risks / Trade-offs

- **[風險] import 數量多（40+），容易漏改** → 用 grep 全量搜索 `from src.ui.config_manager` 等舊路徑，逐一替換後執行 `python main.py` 驗證
- **[風險] PyInstaller 打包可能壞掉** → 更新 `.spec` 檔後執行打包驗證
- **[風險] skill_manager 拆分影響面廣** → skill_loader 保持與原始 skill_manager 相同的公開 API（`get_skill`、`get_all_skills`、`get_skill_by_hotkey`），skill_pixmap_cache 保持 `get_skill_pixmap`、`get_card_pixmap` API，App 持有兩個引用
- **[取捨] 一次性替換 vs 漸進式** → 選擇一次性替換，犧牲安全性換取簡潔度；用啟動測試作為安全網
