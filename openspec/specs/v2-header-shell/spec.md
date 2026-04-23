# v2-header-shell Specification

## Purpose

TBD - created by archiving change 'simplify-v2-header'. Update Purpose after archive.

## Requirements

### Requirement: HeaderV2 SHALL contain only window controls and drag area

The system SHALL reduce `src/ui_v2/header_v2.py` `HeaderV2._build` to render only the left-side draggable padding region and the right-side window control buttons (minimize / maximize / close). The following elements SHALL be removed from the header:

- Avatar (purple/pink gradient circle)
- Greeting label (e.g. "Good Evening, 玩家！")
- Subtitle label (e.g. "今天也來追蹤你的技能冷卻吧 ✦")
- Profile selector ArrowComboBox (moved to skill page; see other requirement)
- Orange CTA button (lucide "plus" icon)
- Bell GlyphBtn
- User GlyphBtn

The drag-handle behavior (`mousePressEvent` / `mouseMoveEvent` / `mouseReleaseEvent`) SHALL remain functional. The header SHALL preserve enough horizontal padding on the left to serve as a drag region.

#### Scenario: Header has only window controls

- **WHEN** `HeaderV2` is rendered
- **THEN** scanning all `QPushButton` and `QFrame` direct children finds only the three `WinCtrlBtn` instances (KIND_MIN / KIND_MAX / KIND_CLOSE) and structural layout widgets

#### Scenario: Drag still works

- **WHEN** the user drags an empty area of the header with the left mouse button
- **THEN** the parent window moves correspondingly (mousePressEvent records position, mouseMoveEvent calls window.move())


<!-- @trace
source: simplify-v2-header
updated: 2026-04-23
code:
  - src/ui_v2/header_v2.py
  - src/ui/app_core.py
  - verify_skill_page_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - docs/PROJECT.md
  - profiles/預設配置.json
-->

---
### Requirement: SkillPageV2 SHALL host the profile selector

The system SHALL add a profile selector widget into `SkillPageV2._build_shell`, placed inside the existing top bar between the "技能倒數" title and the right-side stretch+chips group. The widget SHALL:

- Use the existing `ArrowComboBox` component for visual consistency
- Populate items from `self.app.config_manager.list_profiles()` on construction
- Set the initial selection to `self.app.config_manager.get_current_profile()`
- Connect `currentTextChanged` to invoke `self.app.switch_profile(name)`

The selector SHALL NOT fire `switch_profile` during initial population (use `blockSignals` or set selection before connecting the signal).

#### Scenario: Selector populated from ConfigManager

- **GIVEN** `app.config_manager.list_profiles()` returns `["預設配置", "輔助配置"]` and `get_current_profile()` returns `"輔助配置"`
- **WHEN** `SkillPageV2` is built
- **THEN** the selector contains exactly those two items in that order, with `"輔助配置"` shown as current

#### Scenario: User switches profile

- **WHEN** the user picks `"輔助配置"` from the dropdown (different from current)
- **THEN** `app.switch_profile("輔助配置")` is called exactly once

#### Scenario: Initial population does not trigger switch

- **WHEN** `SkillPageV2` is built (selector items populated and initial selection set)
- **THEN** `app.switch_profile` is NOT called


<!-- @trace
source: simplify-v2-header
updated: 2026-04-23
code:
  - src/ui_v2/header_v2.py
  - src/ui/app_core.py
  - verify_skill_page_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - docs/PROJECT.md
  - profiles/預設配置.json
-->

---
### Requirement: AppCoreMixin SHALL provide switch_profile(name)

The system SHALL add `switch_profile(name)` to `src/ui/app_core.py` `AppCoreMixin`. The method SHALL:

1. Persist the selection: `self.config_manager.set_current_profile(name)` and `self.config_manager.save()`.
2. Reload domain state: `self._load_profile_state(name)` (rebuilds SkillService internals).
3. Trigger UI rebuild for any V2 SkillPageV2 currently registered: if the V2 skill page exposes a `rebuild()` method via `app.skill_card_widgets` registration or a registered `app.skill_page_v2`, call it. The mixin SHALL look for `getattr(self, "skill_page_v2", None)` and call `.rebuild()` if present and the attribute has that method.

The method SHALL be callable from V1 App without breaking V1 (V1 has its own profile-switch path through `_apply_profile`; calling `switch_profile` directly from V1 SHALL produce equivalent state in SkillService).

The method SHALL be a no-op if `name == self.current_profile_name`.

#### Scenario: Switching profile reloads service state

- **GIVEN** profile "A" is current with `skill_permanent["bishop_bless"] == True`, profile "B" exists with `skill_permanent["bishop_bless"] == False`
- **WHEN** `app.switch_profile("B")` is called
- **THEN** `app.current_profile_name == "B"` and `app.skill_permanent["bishop_bless"] == False`

#### Scenario: Switching to current profile is a no-op

- **WHEN** `app.switch_profile(app.current_profile_name)` is called
- **THEN** `config_manager.set_current_profile` is NOT called and `_load_profile_state` is NOT called

#### Scenario: V2 skill page rebuild on switch

- **GIVEN** `app.skill_page_v2` references a V2 `SkillPageV2` instance with a `rebuild()` method
- **WHEN** `app.switch_profile("B")` is called (B differs from current)
- **THEN** `app.skill_page_v2.rebuild()` is called exactly once after `_load_profile_state` returns


<!-- @trace
source: simplify-v2-header
updated: 2026-04-23
code:
  - src/ui_v2/header_v2.py
  - src/ui/app_core.py
  - verify_skill_page_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - docs/PROJECT.md
  - profiles/預設配置.json
-->

---
### Requirement: SkillPageV2 SHALL self-register as app.skill_page_v2

The system SHALL set `app.skill_page_v2 = self` inside `SkillPageV2.__init__` (when `app is not None`), mirroring the existing `MonsterPageV2 → app.monster_page = self` pattern. This enables `AppCoreMixin.switch_profile` to trigger rebuilds without holding direct references.

#### Scenario: SkillPageV2 self-registers

- **WHEN** `SkillPageV2(parent, app)` is constructed
- **THEN** `app.skill_page_v2 is the_page` is True

<!-- @trace
source: simplify-v2-header
updated: 2026-04-23
code:
  - src/ui_v2/header_v2.py
  - src/ui/app_core.py
  - verify_skill_page_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - docs/PROJECT.md
  - profiles/預設配置.json
-->