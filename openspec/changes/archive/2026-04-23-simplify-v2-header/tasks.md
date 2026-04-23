## 1. 前置驗證

- [x] 1.1 跑 `python verify_skill_page_v2.py` + `python verify_monster_page_v2.py` 確認既有 V2 全綠
- [x] 1.2 渲染 `python _preview_shot.py` 為 baseline，記錄 header 區占位（80px）

## 2. AppCoreMixin SHALL provide switch_profile(name)

- [x] 2.1 落實 Requirement「AppCoreMixin SHALL provide switch_profile(name)」：在 `src/ui/app_core.py` `AppCoreMixin` 末段新增 `switch_profile(self, name: str)` 方法。流程：name == current_profile_name → return；否則 `config_manager.set_current_profile(name)` + `config_manager.save()` + `self._load_profile_state(name)`；最後若 `getattr(self, "skill_page_v2", None)` 存在且有 `.rebuild()` 即呼叫
- [x] 2.2 import smoke：`python -c "from src.ui.app_core import AppCoreMixin; assert hasattr(AppCoreMixin, 'switch_profile')"`
- [x] 2.3 V1 行為驗證：`python verify_skill_page_v2.py` 通過（mixin 未動到既有方法）

## 3. SkillPageV2 SHALL self-register as app.skill_page_v2

- [x] 3.1 落實 Requirement「SkillPageV2 SHALL self-register as app.skill_page_v2」：在 `src/ui_v2/pages/skill_page_v2.py` `SkillPageV2.__init__` 末段（在 `_build_shell` 後）加 `if app is not None: app.skill_page_v2 = self`
- [x] 3.2 驗證：擴充 `verify_skill_page_v2.py` 加新測試 `test_skill_page_self_registers`，build SkillPageV2 後 assert `app.skill_page_v2 is page`

## 4. SkillPageV2 SHALL host the profile selector

- [x] 4.1 落實 Requirement「SkillPageV2 SHALL host the profile selector」第一步：在 `src/ui_v2/pages/skill_page_v2.py` import `from src.ui_v2.components import ArrowComboBox`
- [x] 4.2 在 `_build_shell` 的 top bar 內，於 「技能倒數」title 後面、`bar.addStretch()` 之前插入 ProfileSelector 區塊：建立 `ArrowComboBox`，從 `self.app.config_manager.list_profiles()` 取項目；先 `combo.blockSignals(True)` → addItems → setCurrentText(get_current_profile()) → `blockSignals(False)`；再 connect `currentTextChanged` → `lambda name: self.app.switch_profile(name)`；用 V2 樣式（fixed height 30, min width 140, BG_SURFACE, BORDER_SOFT）
- [x] 4.3 V2 渲染驗證：`python _preview_shot.py` → `_shot_page.png` 中可見 profile dropdown 在「技能倒數」title 後方，並顯示當前 profile 名
- [x] 4.4 擴充 `verify_skill_page_v2.py` 加新測試 `test_profile_selector`：fixture app 提供 `config_manager.list_profiles` 回 `["A", "B"]`、`get_current_profile` 回 "B"、`switch_profile` 用 MagicMock；build SkillPageV2 後 (a) 找到 ArrowComboBox 子元件 (b) 其 currentText == "B" (c) `app.switch_profile.call_count == 0`；接著 `combo.setCurrentText("A")` → 驗 `app.switch_profile.assert_called_once_with("A")`

## 5. HeaderV2 SHALL contain only window controls and drag area

- [x] 5.1 落實 Requirement「HeaderV2 SHALL contain only window controls and drag area」：在 `src/ui_v2/header_v2.py` `_build` 移除 7 段元素（avatar / greeting / subtitle / profile combo / 橘色 CTA / GlyphBtn bell / GlyphBtn user）。保留：左側 `setContentsMargins` 拖曳 padding、`addStretch()`、3 個 WinCtrlBtn
- [x] 5.2 移除已不再使用的 import：若 `GlyphBtn` / `ArrowComboBox` / `lucide_pixmap` / `QIcon` 在 header_v2.py 不再被引用，刪 import；`GlyphBtn` 類定義若全模組無使用者，保留檔案但留註解標示可後續清除
- [x] 5.3 渲染驗證：`python _preview_shot.py` → 5 頁 header 區塊縮為視窗控制 + 拖曳區，無 avatar / greeting / dropdown
- [x] 5.4 拖曳行為驗證：手動跑 `python main.py --v2`，按住 header 空白處拖曳 → 視窗跟隨；點 min/max/close → 各自有對應行為

## 6. 收尾

- [x] 6.1 跑 `/simplify` 與 `/spectra-audit` 檢視 mixin 補丁 + header / skill page diff
- [x] 6.2 同步 docs/PROJECT.md：在 `src/ui/app_core.py` 條目補「+ switch_profile」、`src/ui_v2/header_v2.py` 條目註明「精簡為視窗控制+拖曳」
- [ ] 6.3 commit：純 V2 重構、V1 行為等價、不 bump version
