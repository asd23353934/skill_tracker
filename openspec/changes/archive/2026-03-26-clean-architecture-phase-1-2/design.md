## Context

Skill Tracker 的所有資料以原始 Python dict 傳遞，無型別安全。`App` 類別持有 6+ 狀態 dict（`skill_permanent`、`skill_loop`、`skill_alert_enabled` 等），業務規則（如 permanent ⊕ loop 互斥）散落在 `App.update_skill_setting_exclusive()` 等 UI 方法中。`ConfigManager` 負責所有 JSON I/O，但呼叫端直接操作 `config_manager.config` dict，無抽象層。

此設計為 Phase 1-2，建立 Domain Models 和 Repository Layer 兩個基礎層。現有程式碼的行為不變，新層作為後續 Phase 3（Service Layer）和 Phase 4（UI Protocol 解耦）的基礎。

## Goals / Non-Goals

**Goals:**

- 建立純 Python dataclass 領域模型，封裝資料型別和業務不變式
- 建立 Repository 層，提供型別化的資料存取介面
- 所有 Repository 包裝現有 `ConfigManager`，JSON 格式不變
- Domain 層零 Qt 依賴，可獨立單元測試

**Non-Goals:**

- 不將現有呼叫端遷移到新 API — 遷移屬於後續階段
- 不引入 Service Layer 或 Event Bus
- 不修改 `ConfigManager` 的內部實作
- 不建立抽象基底類別或 Protocol — Repository 直接作為具體類別

## Decisions

### Domain Models 使用 dataclass 而非 TypedDict

使用 `@dataclass` 而非 `TypedDict`，因為需要在模型上定義方法（如 `SkillState.set_permanent()`）。TypedDict 僅提供型別提示，不支援方法封裝。也不使用 Pydantic 以避免新增外部依賴。

### SkillState 互斥規則內建於 setter 方法

`SkillState.set_permanent(True)` 自動將 `loop` 設為 `False`，反之亦然。這確保不論在何處呼叫，互斥規則都無法被違反。直接修改 `.permanent` 屬性仍然可行（Python dataclass 不強制），但慣例上應使用 setter。

### Repository 包裝 ConfigManager 而非取代

Repository 在內部呼叫 `ConfigManager` 的方法（`load_profile`、`save_profile`、`save` 等），將 raw dict 轉為 domain models 回傳。這避免重寫 JSON I/O 邏輯，且確保 Strangler 邊界清晰。`ConfigManager` 保持不變。

### Profile 使用 dict[str, SkillState] 而非 list

Profile 內部以 `skill_id` 為鍵的 dict 儲存 `SkillState`，與現有 profiles JSON 格式的結構一致（`hotkeys`、`permanent`、`loop` 等都是 `{skill_id: value}` 的 dict）。`Profile.get_state()` 提供 lazy 初始化，存取不存在的 skill_id 會自動建立預設 SkillState。

### Repository 建構在 App.__init__ 中與現有 manager 並存

在 `App.__init__` 中建構 repository 實例，存為 `self.skill_repo`、`self.profile_repo` 等。現有的 `self.config_manager`、`self.skill_manager` 不受影響。這允許後續階段逐步遷移呼叫端。

### 模組位置選擇 src/domain/ 而非 src/models/

使用 `src/domain/` 命名空間，因為此層不僅包含資料結構，還包含業務規則。為後續 Phase 3 的 `src/domain/services.py` 預留空間。

## Risks / Trade-offs

- **[風險] Domain models 與現有 dict 並存造成混淆** → 在 `models.py` 的模組 docstring 中清楚說明此為新架構層，現有程式碼尚未遷移
- **[風險] Repository 的 dict↔model 轉換增加微量效能開銷** → 此應用為桌面工具，資料量小（< 100 筆技能），影響可忽略
- **[取捨] dataclass 不強制使用 setter** → 靠慣例而非強制。後續可改用 `__setattr__` 或 property，但目前不需要
- **[取捨] Repository 暴露 ConfigManager 的限制**（如一次讀取整個 config.json） → 可接受，因為資料量小且只有單一使用者
