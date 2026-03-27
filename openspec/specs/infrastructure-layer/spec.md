# infrastructure-layer Specification

## Purpose

TBD - created by archiving change 'clean-architecture-phase-5'. Update Purpose after archive.

## Requirements

### Requirement: Infrastructure layer directory exists at src/infrastructure/

The system SHALL have a `src/infrastructure/` directory containing an `__init__.py` module. This directory SHALL serve as the infrastructure layer, holding modules responsible for file I/O, data persistence, network communication, audio playback, and utility functions. The `__init__.py` SHALL export the public API classes: `ConfigManager`, `SkillLoader`, `SoundManager`, `BroadcastManager`, and utility functions `resource_path` and `user_data_path`.

#### Scenario: Infrastructure package is importable

- **WHEN** `import src.infrastructure` is executed
- **THEN** the import succeeds and the module exposes `ConfigManager`, `SkillLoader`, `SoundManager`, `BroadcastManager`, `resource_path`, and `user_data_path`


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: Infrastructure modules have zero Qt dependency

All modules in `src/infrastructure/` SHALL NOT import any PySide6 or Qt modules, either at runtime or in TYPE_CHECKING blocks. They SHALL depend only on Python standard library, domain models, and third-party non-Qt packages (requests, pynput, winsound, scapy).

#### Scenario: Import infrastructure without Qt installed

- **WHEN** `src/infrastructure/config_manager.py`, `src/infrastructure/helpers.py`, `src/infrastructure/sound_manager.py`, `src/infrastructure/updater.py`, and `src/infrastructure/broadcast_manager.py` are imported in an environment without PySide6
- **THEN** all imports succeed without errors


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: ConfigManager resides in src/infrastructure/config_manager.py

The system SHALL provide `ConfigManager` at `src/infrastructure/config_manager.py`. All modules that previously imported from `src.ui.config_manager` SHALL import from `src.infrastructure.config_manager` instead. The class interface SHALL remain unchanged.

#### Scenario: App imports ConfigManager from infrastructure

- **WHEN** `src/ui/app.py` imports `ConfigManager`
- **THEN** the import path is `from src.infrastructure.config_manager import ConfigManager`


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: SkillLoader provides pure-Python skill data access

The system SHALL provide a `SkillLoader` class at `src/infrastructure/skill_loader.py` that loads skill and item data from `ConfigManager`, merges them into a unified dict, and provides query methods: `get_skill(skill_id) -> dict | None`, `get_all_skills() -> dict[str, dict]`, and `get_skill_by_hotkey(key_name) -> str | None`. `SkillLoader` SHALL NOT import any Qt modules. The existing `src/ui/skill_manager.py` Qt-specific pixmap caching logic SHALL be extracted to `src/ui/skill_pixmap_cache.py`.

#### Scenario: SkillLoader loads skills without Qt

- **WHEN** `SkillLoader` is constructed with a `ConfigManager` containing 3 skills and 2 items
- **THEN** `get_all_skills()` returns a dict with 5 entries, and no Qt module is imported

#### Scenario: SkillPixmapCache wraps SkillLoader for Qt image caching

- **WHEN** `src/ui/skill_pixmap_cache.py` is constructed with a `SkillLoader` instance
- **THEN** it provides `get_skill_pixmap(skill_id)` and `get_card_pixmap(skill_id)` methods returning `QPixmap` instances


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: helpers module resides in src/infrastructure/helpers.py

The system SHALL provide utility functions `resource_path()` and `user_data_path()` at `src/infrastructure/helpers.py`. The `user_data_path()` function SHALL replace all duplicate `_user_path()` definitions across the codebase. All modules that previously imported from `src.ui.helpers` SHALL import from `src.infrastructure.helpers` instead.

#### Scenario: resource_path resolves PyInstaller bundled paths

- **WHEN** `resource_path("config.json")` is called in a PyInstaller-bundled environment
- **THEN** the returned path points to the `_MEIPASS` temporary directory

#### Scenario: user_data_path resolves exe-relative paths

- **WHEN** `user_data_path("sounds/alert.wav")` is called
- **THEN** the returned path is relative to the executable's directory (not the bundled temp directory)


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: SoundManager resides in src/infrastructure/sound_manager.py

The system SHALL provide `SoundManager` at `src/infrastructure/sound_manager.py`. The class SHALL use `user_data_path()` from `src.infrastructure.helpers` instead of `overlay_manager._user_path()`. All modules that previously imported from `src.ui.sound_manager` SHALL import from `src.infrastructure.sound_manager` instead.

#### Scenario: SoundManager uses unified user_data_path

- **WHEN** `SoundManager` resolves a sound file path
- **THEN** it calls `user_data_path()` from `src.infrastructure.helpers`, not a local `_user_path()` duplicate


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: Updater resides in src/infrastructure/updater.py

The system SHALL provide `Updater` at `src/infrastructure/updater.py`. All modules that previously imported from `src.ui.updater` SHALL import from `src.infrastructure.updater` instead.

#### Scenario: App imports Updater from infrastructure

- **WHEN** `src/ui/app.py` imports `Updater`
- **THEN** the import path is `from src.infrastructure.updater import Updater`


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: BroadcastManager resides in src/infrastructure/broadcast_manager.py

The system SHALL provide `BroadcastManager` at `src/infrastructure/broadcast_manager.py`. All modules that previously imported from `src.ui.broadcast_manager` SHALL import from `src.infrastructure.broadcast_manager` instead.

#### Scenario: App imports BroadcastManager from infrastructure

- **WHEN** `src/ui/app.py` imports `BroadcastManager`
- **THEN** the import path is `from src.infrastructure.broadcast_manager import BroadcastManager`


<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->

---
### Requirement: Dependency direction enforced across layers

The dependency direction SHALL be: `src/ui/` → `src/domain/` and `src/infrastructure/`, `src/infrastructure/` → `src/domain/`, `src/domain/` → nothing external. No module in `src/domain/` SHALL import from `src/ui/` or `src/infrastructure/`, not even under `TYPE_CHECKING`.

#### Scenario: domain layer has no outward imports

- **WHEN** all `.py` files in `src/domain/` are scanned for import statements
- **THEN** no import references `src.ui` or `src.infrastructure` (including TYPE_CHECKING blocks)

<!-- @trace
source: clean-architecture-phase-5
updated: 2026-03-27
code:
  - src/domain/__init__.py
  - src/infrastructure/updater.py
  - src/infrastructure/sound_manager.py
  - src/ui/sound_manager.py
  - src/ui/dialogs/base_dialog.py
  - src/infrastructure/skill_loader.py
  - src/ui/skill_manager.py
  - src/infrastructure/config_manager.py
  - src/infrastructure/__init__.py
  - src/ui/app.py
  - src/ui/broadcast_manager.py
  - src/ui/helpers.py
  - src/ui/pages/mapleworld_page.py
  - src/domain/services.py
  - src/ui/window_manager.py
  - src/domain/repositories.py
  - src/ui/pages/monster_page.py
  - src/infrastructure/broadcast_manager.py
  - src/infrastructure/repositories.py
  - src/ui/config_manager.py
  - src/infrastructure/helpers.py
  - src/ui/dialogs/update_dialog.py
  - src/ui/pages/overlay_page.py
  - src/ui/overlay_manager.py
  - src/ui/skill_pixmap_cache.py
  - src/ui/updater.py
-->