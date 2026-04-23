## Context

V2 preview shell（`main_v2.py`）的目標是讓設計師能直接 `python main.py --v2` 看到紫色漸層儀表板並**操作真實資料**，但現行 `V2AppContext`（`main_v2.py:34-60`）只建立 `config_manager`、`hotkey_manager` 占位，不建立 `SkillManager` / `WindowManager` / `SoundManager`，導致所有依賴這些 manager 的 V2 頁面（skill / monster / overlay 等）走保護傘直接 return。

同時，V1 App（`src/ui/app.py`）把 13 個「UI 觸發 → 領域操作」的方法（如 `edit_cooldown` / `toggle_all` / `update_hotkey_display`）寫在 class body 內。V2 shell 若要重用只能複製貼上，行為極易漂移。

wire-v2-skill-page 已落地的 SkillCardV2 / SkillPageV2 皆把狀態寫回 App 層 dict（`cooldown_buttons` / `skill_permanent` 等），V1 App 以這些 dict 為單一事實來源。只要把建構這些 dict + 13 個方法的邏輯抽成 mixin，V1 App 繼續繼承、V2AppContext 新加繼承，兩側即可共用同一份 domain backing。

## Goals / Non-Goals

**Goals:**

- 新增 `src/ui/app_core.py`，提供 `AppCoreMixin` 封裝 domain backing 與共通行為。
- V1 App 零行為變更（`python main.py` 所有互動維持現狀），僅改為 `class App(QMainWindow, AppCoreMixin)` 並刪除已上移的方法本體。
- V2AppContext 繼承 `AppCoreMixin`；`python main.py --v2` 打開 V2 shell 後，SkillPageV2 能顯示全部技能、操作觸發 V1 既有 dialog、狀態寫入共用 dict。
- 每實作一個步驟都要有對應驗證（unit 或手動），驗證通過才能往下一步。

**Non-Goals:**

- 不重寫 V1 UI（Header / Sidebar / StatusBar / Pages）。
- 不變更 `SkillManager` / `HotkeyManager` / `WindowManager` / `SoundManager` / `OverlayManager` 的公開 API。
- 不在 V2 shell 實作 profile 切換 UI。
- 不處理 V2 視覺還原度（已在 wire-v2-skill-page 範圍內）。
- 不把 13 個方法移到 `src/domain/`（仍有 UI 依賴，保持在 `src/ui/` 層）。

## Decisions

### Mixin 而非組合：AppCoreMixin 直接注入方法到 App / V2AppContext

把共通行為抽成 mixin，讓 V1 App 與 V2AppContext 直接繼承。考量：

- 現有 `src/ui_v2/pages/skill_card_v2.py` 中 `app.edit_cooldown(sid)` 的呼叫不需修改。
- 狀態 dict（`skill_permanent` / `cooldown_buttons` ...）是 instance 屬性；使用 composition 會需要 proxy 大量 `__getattr__`，反而增加介面面積。
- Alternatives considered:
  - **Composition (`self.core = AppCore(self)`)**：V2 頁面要改寫全部 `app.xxx` → `app.core.xxx`，範圍太大且破壞 V1 行為。
  - **把方法搬到 `SkillService`**：`edit_cooldown` 會開 dialog、`toggle_all` 會呼叫 `update_hotkey_display` 觸發 UI 更新，違反 domain 層零 Qt 依賴原則。

### `_init_domain_backing(config_manager)`：單一進入點重建 Manager 鏈

Mixin 提供唯一的初始化方法；V1 App 在 `__init__` 末段呼叫它；V2AppContext 也在 `__init__` 末段呼叫。建構順序 `SkillManager → HotkeyManager → WindowManager → SoundManager → OverlayManager`，並同步建立所有狀態 dict 與 widget 登錄 dict。

- 理由：目前 V1 App `__init__` 已是此順序，抽出後行為等價。
- 同時定義 `_load_profile_state(profile_name)` helper，讓兩邊都用同一支 profile loading 流程。

### V2AppContext 先用 `config_manager.current_profile`，UI 切換延後

V2 shell 不額外提供 profile 切換 UI；初始化時讀 `config_manager.current_profile` 即可。這讓 V2 preview 能直接看到使用者日常使用的 profile 狀態，便於回歸測試。

- Alternatives: 在 V2 Header 加 profile 下拉 — 延後到 wire-v2-header，非本次目標。

### 每步驟皆須驗證

沿用 wire-v2-skill-page 採用的驗證節奏，tasks.md 以「實作步驟 + 驗證步驟」成對出現。優先使用：

1. **Unit harness**：擴充既有 `verify_skill_page_v2.py` 或新增 `verify_app_core.py`，用 `MagicMock` 驗證 mixin 方法不依賴具體 App 子類。
2. **Import smoke test**：`python -c "from main_v2 import main"` 必通過。
3. **手動回歸**：V1 `python main.py` / V2 `python main.py --v2`，每個 checkpoint 逐項 check list。

## Risks / Trade-offs

- [mixin 命名衝突] → AppCoreMixin 內屬性全部用 `skill_*` / `cooldown_*` 前綴，與現行 V1 App 屬性一致；若未來 V1 新增衝突屬性，子類 override 即可。
- [V2AppContext 沒有 QMainWindow 父類能承接 WindowManager 的 top-level window] → `WindowManager` 只需要能呼叫的 owner，實際 frameless child window 由 WindowManager 自己建立 top-level QWidget；V2AppContext 作為 parent 即可，不須是 QMainWindow。若遇限制，以 hidden QWidget 作 host 容納。
- [Mixin 引入循環依賴] → `AppCoreMixin` 只 import `SkillManager` / `HotkeyManager` / `WindowManager` / `SoundManager` / `OverlayManager`，不 import `App` 本體；保持單向依賴。
- [行為漂移] → 移動方法時不做語意變更；以 `verify_app_core.py` 比對 V1 App 與 V2AppContext 行為一致性。
- [PyInstaller 打包] → Mixin 檔在 `src/ui/` 底下，與現有匯入模式一致，PyInstaller spec 不需要更新。
