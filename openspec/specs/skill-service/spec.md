# skill-service Specification

## Purpose

TBD - created by archiving change 'clean-architecture-phase-3-4'. Update Purpose after archive.

## Requirements

### Requirement: SkillService provides skill state queries

The system SHALL provide a `SkillService` class in `src/domain/services.py` that centralizes all skill state query logic. It SHALL provide: `is_permanent(skill_id) -> bool`, `is_loop(skill_id) -> bool`, `is_alert_enabled(skill_id) -> bool`, `get_effective_cooldown(skill_id) -> int` (returns override or original), `get_alert_seconds(skill_id) -> int` (returns override or global default), `get_sound(skill_id) -> str` (returns override or global default), `get_alert_sound(skill_id) -> str` (returns override or global default), `get_hotkey(skill_id) -> str`, and `get_original_cooldown(skill_id) -> int | None`.

#### Scenario: Query permanent state for a skill

- **WHEN** `is_permanent("mapleWarrior")` is called and the skill's permanent flag is True
- **THEN** `True` is returned

#### Scenario: Get effective cooldown with override

- **WHEN** `get_effective_cooldown("mapleWarrior")` is called and a cooldown override of 180 exists for that skill (original is 270)
- **THEN** `180` is returned

#### Scenario: Get effective cooldown without override

- **WHEN** `get_effective_cooldown("mapleWarrior")` is called and no cooldown override exists
- **THEN** the original cooldown `270` from SkillRepository is returned

#### Scenario: Get alert seconds falls back to global

- **WHEN** `get_alert_seconds("mapleWarrior")` is called with no per-skill override and the global `alert_before_seconds` is 10
- **THEN** `10` is returned

#### Scenario: Get sound falls back to global

- **WHEN** `get_sound("mapleWarrior")` is called with no per-skill override and `global_sound` is `"alert_urgent.wav"`
- **THEN** `"alert_urgent.wav"` is returned


<!-- @trace
source: clean-architecture-phase-3-4
updated: 2026-03-27
code:
  - skill_tracker.spec
  - src/infrastructure/updater.py
  - src/domain/__init__.py
  - src/infrastructure/sound_manager.py
  - src/domain/models.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/infrastructure/repositories.py
  - .spectra.yaml
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/overlay_page.py
  - src/domain/services.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/skill_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/pages/monster_page.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/overlay_manager.py
  - src/infrastructure/config_manager.py
  - requirements.txt
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - config.json
  - src/infrastructure/broadcast_manager.py
  - src/ui/sound_manager.py
  - src/ui/updater.py
  - src/ui/pages/broadcast_page.py
  - src/ui/sidebar.py
  - src/infrastructure/__init__.py
  - src/domain/repositories.py
  - src/infrastructure/skill_loader.py
  - src/ui/config_manager.py
  - src/ui/dialogs/update_dialog.py
  - src/infrastructure/helpers.py
  - src/ui/window_manager.py
-->

---
### Requirement: SkillService enforces permanent and loop mutual exclusion on state changes

The system SHALL provide `set_permanent(skill_id, value) -> dict` and `set_loop(skill_id, value) -> dict` methods on SkillService. When `set_permanent(skill_id, True)` is called, the skill's loop flag SHALL be set to False. When `set_loop(skill_id, True)` is called, the skill's permanent flag SHALL be set to False. Both methods SHALL return a dict containing the new values of both `permanent` and `loop` for the given skill_id, so the caller can update UI accordingly.

#### Scenario: Enable permanent disables loop and returns new state

- **WHEN** skill "mapleWarrior" has `loop=True` and `set_permanent("mapleWarrior", True)` is called
- **THEN** the method returns `{"permanent": True, "loop": False}` and internal state reflects these values

#### Scenario: Enable loop disables permanent and returns new state

- **WHEN** skill "mapleWarrior" has `permanent=True` and `set_loop("mapleWarrior", True)` is called
- **THEN** the method returns `{"permanent": False, "loop": True}` and internal state reflects these values

#### Scenario: Disable permanent does not affect loop

- **WHEN** skill "mapleWarrior" has `permanent=True, loop=False` and `set_permanent("mapleWarrior", False)` is called
- **THEN** the method returns `{"permanent": False, "loop": False}`


<!-- @trace
source: clean-architecture-phase-3-4
updated: 2026-03-27
code:
  - skill_tracker.spec
  - src/infrastructure/updater.py
  - src/domain/__init__.py
  - src/infrastructure/sound_manager.py
  - src/domain/models.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/infrastructure/repositories.py
  - .spectra.yaml
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/overlay_page.py
  - src/domain/services.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/skill_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/pages/monster_page.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/overlay_manager.py
  - src/infrastructure/config_manager.py
  - requirements.txt
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - config.json
  - src/infrastructure/broadcast_manager.py
  - src/ui/sound_manager.py
  - src/ui/updater.py
  - src/ui/pages/broadcast_page.py
  - src/ui/sidebar.py
  - src/infrastructure/__init__.py
  - src/domain/repositories.py
  - src/infrastructure/skill_loader.py
  - src/ui/config_manager.py
  - src/ui/dialogs/update_dialog.py
  - src/infrastructure/helpers.py
  - src/ui/window_manager.py
-->

---
### Requirement: SkillService manages cooldown and alert overrides

The system SHALL provide: `set_cooldown_override(skill_id, seconds) -> bool` (returns True if value differs from original), `clear_cooldown_override(skill_id)`, `set_alert_seconds_override(skill_id, seconds)`, `clear_alert_seconds_override(skill_id)`, `set_alert_enabled(skill_id, value)`, `set_sound_override(skill_id, filename)`, `clear_sound_override(skill_id)`, `set_alert_sound_override(skill_id, filename)`, and `clear_alert_sound_override(skill_id)`.

#### Scenario: Set cooldown override returns modified flag

- **WHEN** `set_cooldown_override("mapleWarrior", 180)` is called and the original cooldown is 270
- **THEN** the method returns `True` (indicating the value is modified from original)

#### Scenario: Set cooldown to original value returns not modified

- **WHEN** `set_cooldown_override("mapleWarrior", 270)` is called and the original cooldown is 270
- **THEN** the method returns `False` (indicating the value matches original)

#### Scenario: Clear alert seconds override reverts to global

- **WHEN** `clear_alert_seconds_override("mapleWarrior")` is called
- **THEN** `get_alert_seconds("mapleWarrior")` returns the global `alert_before_seconds` value


<!-- @trace
source: clean-architecture-phase-3-4
updated: 2026-03-27
code:
  - skill_tracker.spec
  - src/infrastructure/updater.py
  - src/domain/__init__.py
  - src/infrastructure/sound_manager.py
  - src/domain/models.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/infrastructure/repositories.py
  - .spectra.yaml
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/overlay_page.py
  - src/domain/services.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/skill_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/pages/monster_page.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/overlay_manager.py
  - src/infrastructure/config_manager.py
  - requirements.txt
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - config.json
  - src/infrastructure/broadcast_manager.py
  - src/ui/sound_manager.py
  - src/ui/updater.py
  - src/ui/pages/broadcast_page.py
  - src/ui/sidebar.py
  - src/infrastructure/__init__.py
  - src/domain/repositories.py
  - src/infrastructure/skill_loader.py
  - src/ui/config_manager.py
  - src/ui/dialogs/update_dialog.py
  - src/infrastructure/helpers.py
  - src/ui/window_manager.py
-->

---
### Requirement: SkillService manages hotkey binding with conflict detection

The system SHALL provide `set_hotkey(skill_id, key_str) -> str | None` that assigns a hotkey to a skill. If another skill already has the same hotkey, the old binding SHALL be cleared and the displaced skill_id SHALL be returned. If no conflict exists, `None` SHALL be returned. The system SHALL also provide `clear_hotkey(skill_id)` and `find_by_hotkey(key_str) -> str | None`.

#### Scenario: Set hotkey with no conflict

- **WHEN** `set_hotkey("mapleWarrior", "F1")` is called and no other skill has hotkey "F1"
- **THEN** `None` is returned and `get_hotkey("mapleWarrior")` returns `"F1"`

#### Scenario: Set hotkey displaces existing binding

- **WHEN** `set_hotkey("mapleWarrior", "F1")` is called and skill "sharpEyes" already has hotkey "F1"
- **THEN** `"sharpEyes"` is returned, `get_hotkey("sharpEyes")` returns `""`, and `get_hotkey("mapleWarrior")` returns `"F1"`

#### Scenario: Find skill by hotkey

- **WHEN** `find_by_hotkey("F1")` is called and skill "mapleWarrior" has hotkey "F1"
- **THEN** `"mapleWarrior"` is returned


<!-- @trace
source: clean-architecture-phase-3-4
updated: 2026-03-27
code:
  - skill_tracker.spec
  - src/infrastructure/updater.py
  - src/domain/__init__.py
  - src/infrastructure/sound_manager.py
  - src/domain/models.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/infrastructure/repositories.py
  - .spectra.yaml
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/overlay_page.py
  - src/domain/services.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/skill_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/pages/monster_page.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/overlay_manager.py
  - src/infrastructure/config_manager.py
  - requirements.txt
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - config.json
  - src/infrastructure/broadcast_manager.py
  - src/ui/sound_manager.py
  - src/ui/updater.py
  - src/ui/pages/broadcast_page.py
  - src/ui/sidebar.py
  - src/infrastructure/__init__.py
  - src/domain/repositories.py
  - src/infrastructure/skill_loader.py
  - src/ui/config_manager.py
  - src/ui/dialogs/update_dialog.py
  - src/infrastructure/helpers.py
  - src/ui/window_manager.py
-->

---
### Requirement: SkillService provides bulk toggle operations

The system SHALL provide `toggle_all_permanent() -> dict[str, bool]`, `toggle_all_loop() -> dict[str, bool]`, and `toggle_all_alert() -> dict[str, bool]`. Each method SHALL determine whether all skills are currently enabled (toggle off) or any are disabled (toggle on), apply the change to all skills, enforce mutual exclusion rules where applicable, and return a dict mapping each skill_id to its new boolean value.

#### Scenario: Toggle all permanent when some are off

- **WHEN** `toggle_all_permanent()` is called and 3 out of 10 skills have permanent=True
- **THEN** all 10 skills are set to permanent=True, all loop flags are set to False, and the returned dict has all values as True

#### Scenario: Toggle all permanent when all are on

- **WHEN** `toggle_all_permanent()` is called and all skills have permanent=True
- **THEN** all skills are set to permanent=False and the returned dict has all values as False


<!-- @trace
source: clean-architecture-phase-3-4
updated: 2026-03-27
code:
  - skill_tracker.spec
  - src/infrastructure/updater.py
  - src/domain/__init__.py
  - src/infrastructure/sound_manager.py
  - src/domain/models.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/infrastructure/repositories.py
  - .spectra.yaml
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/overlay_page.py
  - src/domain/services.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/skill_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/pages/monster_page.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/overlay_manager.py
  - src/infrastructure/config_manager.py
  - requirements.txt
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - config.json
  - src/infrastructure/broadcast_manager.py
  - src/ui/sound_manager.py
  - src/ui/updater.py
  - src/ui/pages/broadcast_page.py
  - src/ui/sidebar.py
  - src/infrastructure/__init__.py
  - src/domain/repositories.py
  - src/infrastructure/skill_loader.py
  - src/ui/config_manager.py
  - src/ui/dialogs/update_dialog.py
  - src/infrastructure/helpers.py
  - src/ui/window_manager.py
-->

---
### Requirement: SkillService handles profile serialization and loading

The system SHALL provide `serialize_to_dict() -> dict` that exports the current skill state to the profile JSON format (with keys: hotkeys, permanent, loop, alert_enabled, cooldown_overrides, alert_seconds_overrides, sound_overrides, alert_sound_overrides). The system SHALL also provide `load_from_profile(profile_data: dict)` that replaces the current state with data from a profile dict, and `reset_all_to_defaults()` that clears all overrides and hotkeys back to defaults.

#### Scenario: Serialize current state to profile dict

- **WHEN** `serialize_to_dict()` is called and skill "mapleWarrior" has hotkey="F1", permanent=True, cooldown_override=180
- **THEN** the returned dict contains `{"hotkeys": {"mapleWarrior": "F1", ...}, "permanent": {"mapleWarrior": true, ...}, "cooldown_overrides": {"mapleWarrior": 180, ...}, ...}`

#### Scenario: Load profile replaces all state

- **WHEN** `load_from_profile(data)` is called with a profile dict containing `{"hotkeys": {"mapleWarrior": "F2"}, "permanent": {"mapleWarrior": false}, ...}`
- **THEN** `get_hotkey("mapleWarrior")` returns `"F2"` and `is_permanent("mapleWarrior")` returns `False`


<!-- @trace
source: clean-architecture-phase-3-4
updated: 2026-03-27
code:
  - skill_tracker.spec
  - src/infrastructure/updater.py
  - src/domain/__init__.py
  - src/infrastructure/sound_manager.py
  - src/domain/models.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/infrastructure/repositories.py
  - .spectra.yaml
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/overlay_page.py
  - src/domain/services.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/skill_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/pages/monster_page.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/overlay_manager.py
  - src/infrastructure/config_manager.py
  - requirements.txt
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - config.json
  - src/infrastructure/broadcast_manager.py
  - src/ui/sound_manager.py
  - src/ui/updater.py
  - src/ui/pages/broadcast_page.py
  - src/ui/sidebar.py
  - src/infrastructure/__init__.py
  - src/domain/repositories.py
  - src/infrastructure/skill_loader.py
  - src/ui/config_manager.py
  - src/ui/dialogs/update_dialog.py
  - src/infrastructure/helpers.py
  - src/ui/window_manager.py
-->

---
### Requirement: SkillService has zero Qt dependency

The `SkillService` class SHALL be defined in `src/domain/services.py` and SHALL NOT import any PySide6 or Qt modules. It SHALL depend only on `SkillRepository`, `ProfileRepository`, and domain models.

#### Scenario: Import SkillService without Qt

- **WHEN** `src/domain/services.py` is imported without PySide6 installed
- **THEN** the import succeeds without errors

<!-- @trace
source: clean-architecture-phase-3-4
updated: 2026-03-27
code:
  - skill_tracker.spec
  - src/infrastructure/updater.py
  - src/domain/__init__.py
  - src/infrastructure/sound_manager.py
  - src/domain/models.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/infrastructure/repositories.py
  - .spectra.yaml
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/overlay_page.py
  - src/domain/services.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/skill_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/pages/monster_page.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/overlay_manager.py
  - src/infrastructure/config_manager.py
  - requirements.txt
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - config.json
  - src/infrastructure/broadcast_manager.py
  - src/ui/sound_manager.py
  - src/ui/updater.py
  - src/ui/pages/broadcast_page.py
  - src/ui/sidebar.py
  - src/infrastructure/__init__.py
  - src/domain/repositories.py
  - src/infrastructure/skill_loader.py
  - src/ui/config_manager.py
  - src/ui/dialogs/update_dialog.py
  - src/infrastructure/helpers.py
  - src/ui/window_manager.py
-->