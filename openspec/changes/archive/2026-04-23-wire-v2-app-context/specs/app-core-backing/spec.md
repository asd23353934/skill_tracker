## ADDED Requirements

### Requirement: AppCoreMixin SHALL provide shared domain backing for App and V2AppContext

The system SHALL provide an `AppCoreMixin` class in `src/ui/app_core.py` that, when mixed into a host object alongside a Qt widget base, constructs the full domain backing (skill manager, hotkey manager, window manager, sound manager, overlay manager) and initializes the App-level state dicts so that both `src/ui/app.py:App` and `main_v2.py:V2AppContext` SHALL share identical runtime behavior for skill interactions.

The mixin SHALL expose a single initialization entry point named `_init_domain_backing(config_manager)` and SHALL NOT import the concrete `App` class, preventing circular dependencies.

#### Scenario: V1 App initialization stays behaviorally identical

- **WHEN** `App.__init__` runs and calls `self._init_domain_backing(self.config_manager)`
- **THEN** `self.skill_manager`, `self.hotkey_manager`, `self.window_manager`, `self.sound_manager`, and `self.overlay_manager` MUST be set to the same Manager types as before, in the same construction order

#### Scenario: V2AppContext gains the same domain backing

- **WHEN** `python main.py --v2` is launched and `V2AppContext.__init__` finishes
- **THEN** `context.skill_manager` MUST be a `SkillManager` instance with skills loaded from the same `config.json`, and `SkillPageV2.rebuild()` MUST render all skill cards instead of returning early

### Requirement: AppCoreMixin SHALL expose the 13 shared App interaction methods

The mixin SHALL provide these 13 methods with the exact same signatures and behavior as they had on the V1 `App` class prior to this change: `edit_cooldown`, `reset_cooldown`, `reset_hotkey`, `update_skill_setting_exclusive`, `update_alert_setting`, `edit_alert_seconds`, `toggle_all`, `update_hotkey_display`, `get_alert_seconds`, `get_original_cooldown`, `auto_save_current_profile`, `show_skill_detail`, `on_skill_triggered`.

After the change lands, the V1 `App` class MUST NOT define its own copies of these 13 methods; they MUST be inherited from the mixin.

#### Scenario: SkillCardV2 method calls succeed against V2AppContext

- **WHEN** a `SkillCardV2` bound to `V2AppContext` dispatches `app.edit_cooldown(skill_id)` from its cooldown chip click handler
- **THEN** the same cooldown-edit dialog flow that runs under V1 `App` MUST execute, and the resulting override MUST be written to `app.skill_cooldown_overrides[skill_id]`

#### Scenario: V1 App delegates through the mixin

- **WHEN** an automated harness inspects `App.edit_cooldown` via `App.edit_cooldown.__qualname__`
- **THEN** the qualname MUST begin with `AppCoreMixin.` and not with `App.`, proving the method body was removed from App

### Requirement: AppCoreMixin SHALL initialize the App-level state registries

The mixin SHALL, during `_init_domain_backing`, create and attach these instance dicts with the documented semantics:

- Skill state dicts: `skill_hotkeys`, `skill_permanent`, `skill_loop`, `skill_alert_enabled`, `skill_cooldown_overrides`, `skill_alert_seconds_overrides`, `skill_sound_overrides`, `skill_alert_sound_overrides`.
- Widget registry dicts: `cooldown_buttons`, `hotkey_buttons`, `alert_seconds_buttons`, `permanent_vars`, `loop_vars`, `alert_enabled_vars`, `skill_card_widgets`.

The mixin SHALL load the current profile's state into the skill state dicts using the same semantics as V1 App: `skill_hotkeys` is populated from the current profile's `hotkeys` map, and the override dicts are populated from the corresponding profile keys.

#### Scenario: Dict attributes exist after init on both hosts

- **WHEN** either `App()` (V1) or `V2AppContext(config_manager)` (V2) finishes construction
- **THEN** all 15 named dicts above MUST be present as instance attributes with type `dict`, and `skill_hotkeys` MUST contain the entries from the current profile

##### Example: state attributes after init

| Attribute | Type | Initial source |
| --------- | ---- | -------------- |
| `skill_hotkeys` | `dict[str, str]` | `profile["hotkeys"]` |
| `skill_permanent` | `dict[str, bool]` | `profile["permanent"]` |
| `skill_cooldown_overrides` | `dict[str, int]` | `profile["cooldown_overrides"]` |
| `cooldown_buttons` | `dict[str, QPushButton]` | `{}` |
| `skill_card_widgets` | `dict[str, QWidget]` | `{}` |

### Requirement: AppCoreMixin SHALL NOT introduce circular imports or regressions

The module `src/ui/app_core.py` SHALL only import from `src/ui/skill_manager.py`, `src/ui/hotkey_manager.py`, `src/ui/window_manager.py`, `src/ui/sound_manager.py`, `src/ui/overlay_manager.py`, `src/ui/config_manager.py`, and standard library / PySide6. It SHALL NOT import from `src/ui/app.py` or `main_v2.py`.

The V1 regression suite — namely `verify_skill_page_v2.py` and any existing verify scripts — MUST continue to pass after the mixin is introduced.

#### Scenario: Import smoke test passes

- **WHEN** the command `python -c "from main_v2 import main; from src.ui.app import App; from src.ui.app_core import AppCoreMixin"` is executed from the project root
- **THEN** the command MUST exit with code 0

#### Scenario: Regression harness stays green

- **WHEN** `python verify_skill_page_v2.py` is executed
- **THEN** the process MUST exit with code 0 and MUST print "All checks passed."

### Requirement: Each implementation step SHALL be validated before proceeding

The implementation of this change SHALL proceed in named steps (see tasks.md), and each step SHALL have a paired validation action that MUST pass before the next step begins. Acceptable validation actions are: running an import smoke test, running an existing verify script, running a newly added verify script, or executing a listed manual QA checklist item.

#### Scenario: Step pairing

- **WHEN** a task in tasks.md is marked `[x]`
- **THEN** a corresponding validation task referencing that step MUST also be marked `[x]` in the same commit
