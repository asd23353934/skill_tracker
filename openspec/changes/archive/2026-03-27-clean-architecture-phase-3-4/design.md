## Context

Phase 1-2 已建立 Domain Models（`src/domain/models.py`）和 Repository Layer（`src/domain/repositories.py`），但 `App` 類別仍然直接實作所有業務邏輯。目前 App 持有 6+ 狀態 dict（`skill_permanent`、`skill_loop`、`skill_alert_enabled`、`skill_alert_seconds_overrides`、`skill_sound_overrides`、`skill_alert_sound_overrides`），並且在 `update_skill_setting_exclusive()`、`edit_cooldown()`、`toggle_all()` 等方法中直接操作這些 dict。UI 元件透過 `self.app` 存取所有狀態和方法。

此設計將業務邏輯抽取到 Service 層，App 保留 UI 協調職責。

## Goals / Non-Goals

**Goals:**

- 將技能業務邏輯集中到 `SkillService`，消除 App 中 600+ 行的業務方法
- 將怪物業務邏輯集中到 `MonsterService`
- Service 層依賴 Repository 和 Domain Models，不依賴 Qt
- App 成為薄協調層：接收 UI 事件 → 呼叫 Service → 更新 UI
- 遷移所有呼叫端（UI 元件、Manager、Dialog）使用 Service

**Non-Goals:**

- 不引入 Protocol 介面或依賴注入容器
- 不改變 UI 元件的建構簽名（仍接收 `app` 參數）
- 不引入 Event Bus 或觀察者模式
- 不移除 App 上的狀態 dict — 改為由 Service 管理，App 透過 property 委派

## Decisions

### Service 持有狀態而非 App

將 `skill_permanent`、`skill_loop`、`skill_alert_enabled` 等 dict 從 App 移到 `SkillService` 內部。App 透過 `self.skill_service` 存取。遷移期間 App 提供 property 委派以保持向後相容：

```python
# App 上的相容 property
@property
def skill_permanent(self):
    return self.skill_service._permanent
```

這樣 UI 元件的 `self.app.skill_permanent[id]` 存取不需要一次全改，可以逐步遷移。

### Service 不依賴 Qt 但可接收 callback

Service 類別不 import PySide6，但建構時可接收 callback 函數用於通知狀態變更。例如 `SkillService` 建構時接收 `on_state_changed: Callable` callback，App 提供此 callback 來處理 UI 更新。這避免 Service 直接操作 UI，同時保持簡單。

### SkillService 統一管理技能相關狀態

目前技能相關邏輯散落在 App 的 20+ 個方法中。SkillService 統一提供：
- 狀態查詢：`is_permanent()`、`is_loop()`、`get_effective_cooldown()`、`get_alert_seconds()`、`get_sound()`、`get_alert_sound()`
- 狀態變更：`set_permanent()`（內含互斥）、`set_loop()`、`set_alert_enabled()`、`set_cooldown_override()`、`set_alert_seconds_override()`、`set_sound_override()`、`set_alert_sound_override()`
- 快捷鍵：`set_hotkey()`（含衝突偵測）、`clear_hotkey()`、`find_by_hotkey()`
- 批次操作：`toggle_all_permanent()`、`toggle_all_loop()`、`toggle_all_alert()`
- 配置序列化：`serialize_to_dict()`、`load_from_profile()`、`apply_profile()`
- 工具方法：`get_original_cooldown()`

### MonsterService 統一管理怪物相關狀態

將 App 中 `edit_respawn_time()`、`reset_respawn_time()`、`update_monster_loop()` 等方法的業務邏輯抽取到 MonsterService。Service 持有怪物資料的引用，提供：
- 查詢：`get()`、`get_by_hotkey()`、`get_all()`
- 變更：`set_respawn_time()`、`reset_respawn_time()`、`set_hotkey()`、`clear_hotkey()`、`set_loop()`、`set_permanent()`、`set_alert_before()`、`set_sound()`、`set_alert_sound()`
- 持久化：`save()`

### App 方法改為薄委派

App 上的業務方法（如 `edit_cooldown()`）改為：
1. 開啟 UI 對話框（UI 職責，留在 App）
2. 呼叫 Service 方法處理業務邏輯
3. 根據結果更新 UI 按鈕/樣式

例如：
```python
def edit_cooldown(self, skill_id):
    # 1. UI: 開啟對話框
    dialog_result = QInputDialog.getInt(...)
    if not ok:
        return
    # 2. 業務: 委派給 service
    is_modified = self.skill_service.set_cooldown_override(skill_id, new_value)
    # 3. UI: 更新按鈕
    self._update_cooldown_button(skill_id, new_value, is_modified)
```

### SkillDetailDialog 改為回傳資料而非直接寫入 App

目前 `SkillDetailDialog._save()` 直接寫入 `self.app.skill_alert_seconds_overrides` 等 dict。重構後 dialog 回傳結果 dict，由 App 透過 Service 套用變更。

### 遷移順序為由內而外

1. 先建立 Service 類別（純邏輯，不改現有程式碼）
2. 在 App 中建構 Service，將狀態移入 Service
3. 添加 App property 委派保持向後相容
4. 逐一遷移 App 的業務方法為薄委派
5. 最後遷移 UI 元件和 Dialog 使用 Service

## Risks / Trade-offs

- **[風險] 遷移過程中 App 同時有 property 委派和直接存取** → 透過漸進式遷移減少風險，每個方法獨立可測試
- **[風險] Service callback 模式增加間接性** → 比 Event Bus 簡單得多，callback 在建構時明確綁定
- **[取捨] Service 不使用 Protocol 介面** → 目前不需要 mock 測試，保持簡單。後續可加入
- **[取捨] UI 元件仍接收整個 App** → 完整的 Protocol 解耦為後續工作，此階段先讓 App 瘦身
- **[風險] SkillDetailDialog 改為回傳資料可能遺漏欄位** → 用 dataclass 定義回傳結構，型別檢查防止遺漏
