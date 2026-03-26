# domain-models Specification

## Purpose

TBD - created by archiving change 'clean-architecture-phase-1-2'. Update Purpose after archive.

## Requirements

### Requirement: SkillMetadata is an immutable data model

The system SHALL provide a `SkillMetadata` dataclass representing read-only skill/item metadata with the fields: `id` (str), `name` (str), `icon` (str), `cooldown` (int, seconds), `category` (str), and `subcategory` (str). All fields SHALL be set at construction time and SHALL NOT be modified afterward.

#### Scenario: Construct SkillMetadata from config.json skill entry

- **WHEN** a skill entry dict `{"id": "mapleWarrior", "name": "楓葉祝福", "icon": "mapleWarrior.png", "cooldown": 270, "category": "player", "subcategory": "共通"}` is provided
- **THEN** a `SkillMetadata` instance is created with all six fields matching the dict values

#### Scenario: SkillMetadata includes items with category "item"

- **WHEN** an item entry dict with `"category": "item"` is provided
- **THEN** a `SkillMetadata` instance is created using the same class, with `category` set to `"item"`


<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->

---
### Requirement: SkillState encapsulates per-profile mutable skill state

The system SHALL provide a `SkillState` dataclass with the fields: `hotkey` (str, default ""), `permanent` (bool, default False), `loop` (bool, default False), `alert_enabled` (bool, default False), `cooldown_override` (int or None, default None), `alert_seconds_override` (int or None, default None), `sound_override` (str, default ""), and `alert_sound_override` (str, default "").

#### Scenario: Default SkillState has all defaults

- **WHEN** a `SkillState` is constructed with no arguments
- **THEN** `hotkey` is `""`, `permanent` is `False`, `loop` is `False`, `alert_enabled` is `False`, `cooldown_override` is `None`, `alert_seconds_override` is `None`, `sound_override` is `""`, `alert_sound_override` is `""`


<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->

---
### Requirement: SkillState enforces permanent and loop mutual exclusion

The system SHALL provide `set_permanent(value: bool)` and `set_loop(value: bool)` methods on `SkillState`. When `set_permanent(True)` is called, `loop` SHALL be set to `False`. When `set_loop(True)` is called, `permanent` SHALL be set to `False`. Setting either to `False` SHALL NOT affect the other field.

#### Scenario: Enabling permanent disables loop

- **WHEN** a `SkillState` has `loop=True` and `set_permanent(True)` is called
- **THEN** `permanent` is `True` and `loop` is `False`

#### Scenario: Enabling loop disables permanent

- **WHEN** a `SkillState` has `permanent=True` and `set_loop(True)` is called
- **THEN** `loop` is `True` and `permanent` is `False`

#### Scenario: Disabling permanent does not affect loop

- **WHEN** a `SkillState` has `permanent=True` and `loop=False`, and `set_permanent(False)` is called
- **THEN** `permanent` is `False` and `loop` remains `False`


<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->

---
### Requirement: Profile aggregates SkillState by skill ID

The system SHALL provide a `Profile` dataclass with fields: `name` (str) and `skill_states` (dict mapping skill_id str to SkillState). The `Profile` SHALL provide a `get_state(skill_id: str) -> SkillState` method that returns the existing `SkillState` for the given skill_id, or creates and stores a new default `SkillState` if the skill_id is not yet present.

#### Scenario: Get existing skill state

- **WHEN** a `Profile` has a `SkillState` for skill_id `"mapleWarrior"`
- **THEN** `get_state("mapleWarrior")` returns that existing `SkillState` instance

#### Scenario: Get state for unknown skill creates default

- **WHEN** a `Profile` has no entry for skill_id `"newSkill"` and `get_state("newSkill")` is called
- **THEN** a new default `SkillState` is stored under `"newSkill"` and returned


<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->

---
### Requirement: MonsterData represents monster respawn configuration

The system SHALL provide a `MonsterData` dataclass with fields: `id` (str), `name` (str), `icon` (str), `respawn_time` (int, seconds), `hotkey` (str, default ""), `alert_before` (int, default 0), `loop` (bool, default False), `permanent` (bool, default False), `sound` (str, default ""), and `alert_sound` (str, default "").

#### Scenario: Construct MonsterData from config.json monster entry

- **WHEN** a monster entry dict `{"id": "fish_house", "name": "魚屋", "icon": "刺鰭魚之屋.png", "respawn_time": 30, "hotkey": "", "alert_before": 10, "alert_sound": "alert_double.wav", "loop": true, "permanent": false}` is provided
- **THEN** a `MonsterData` instance is created with all fields matching the dict values, and `sound` defaults to `""`


<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->

---
### Requirement: OverlayData represents overlay image configuration

The system SHALL provide an `OverlayData` dataclass with fields: `id` (str), `name` (str), `file` (str), `alpha` (float, default 1.0), `x` (int, default 0), `y` (int, default 0), `width` (int, default 0), and `height` (int, default 0).

#### Scenario: Construct OverlayData with position and transparency

- **WHEN** an overlay entry dict `{"id": "o1", "name": "Map", "file": "map.png", "alpha": 0.8, "x": 100, "y": 200, "width": 300, "height": 400}` is provided
- **THEN** an `OverlayData` instance is created with all fields matching the dict values


<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->

---
### Requirement: GlobalSettings represents cross-profile application settings

The system SHALL provide a `GlobalSettings` dataclass with fields: `player_name` (str, default "玩家1"), `skill_start_x` (int, default 0), `skill_start_y` (int, default 0), `enable_sound` (bool, default True), `window_size` (int, default 64), `alert_before_seconds` (int, default 0), `global_sound` (str, default ""), `global_alert_sound` (str, default ""), and `current_profile` (str, default "預設配置").

#### Scenario: Construct GlobalSettings from config.json settings

- **WHEN** a settings dict `{"player_name": "玩家1", "skill_start_x": 423, "skill_start_y": 107, "enable_sound": true, "window_size": 96, "alert_before_seconds": 10, "global_sound": "alert_urgent.wav", "global_alert_sound": "alert_urgent.wav", "current_profile": "預設配置"}` is provided
- **THEN** a `GlobalSettings` instance is created with all fields matching the dict values


<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->

---
### Requirement: Domain models have zero Qt dependency

All domain model classes (`SkillMetadata`, `SkillState`, `Profile`, `MonsterData`, `OverlayData`, `GlobalSettings`) SHALL be defined in `src/domain/models.py` and SHALL NOT import any PySide6 or Qt modules. They SHALL use only Python standard library types.

#### Scenario: Import domain models without Qt installed

- **WHEN** `src/domain/models.py` is imported in an environment without PySide6
- **THEN** the import succeeds without errors

<!-- @trace
source: clean-architecture-phase-1-2
updated: 2026-03-26
code:
  - src/ui/pages/broadcast_page.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/models.py
  - src/ui/dialogs/base_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/app.py
  - src/domain/__init__.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - requirements.txt
  - src/ui/broadcast_manager.py
  - src/ui/sidebar.py
  - src/domain/repositories.py
  - skill_tracker.spec
  - config.json
  - .spectra.yaml
  - src/ui/dialogs/broadcast_blacklist_dialog.py
-->