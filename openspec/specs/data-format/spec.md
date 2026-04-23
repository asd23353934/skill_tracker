# data-format Specification

## Purpose

TBD - created by archiving change 'data-format-cleanup'. Update Purpose after archive.

## Requirements

### Requirement: Static zone is read-only metadata

The `config.json → skills[]` and `config.json → items[]` arrays SHALL contain only immutable metadata fields:
`id`, `name`, `icon`, `cooldown`, `category`, `subcategory`.

No user-state field (hotkey, permanent, loop, alert_enabled, or any override) SHALL appear in the static zone.
`ConfigManager` SHALL protect static zone integrity by saving `initial_skills` / `initial_items` snapshots
(captured at startup) rather than the runtime-modified arrays.

#### Scenario: Static zone survives runtime mutations

- **WHEN** `SkillManager.update_hotkey()` modifies an in-memory skill dict
- **THEN** the `hotkey` value SHALL NOT be written to `config.json → skills[]` on disk

#### Scenario: Static zone fields are enumerated

- **WHEN** a new skill entry is added to `config.json`
- **THEN** the entry SHALL contain only `id`, `name`, `icon`, `cooldown`, `category`, `subcategory`
- **THEN** adding a `hotkey` field to the entry SHALL be treated as a data error


<!-- @trace
source: data-format-cleanup
updated: 2026-03-20
code:
  - docs/DATA_FORMAT.md
  - CLAUDE.md
  - src/ui/app.py
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
  - docs/ARCHITECTURE.md
  - config.json
  - src/ui/skill_manager.py
-->

---
### Requirement: Global mutable zone stores cross-profile state

The `config.json → settings` object SHALL store only cross-profile, global settings
(e.g., `player_name`, `skill_start_x`, `skill_start_y`, `current_profile`, UI preferences).

User skill state (`permanent`, `loop`, `alert_enabled`, hotkeys, overrides) SHALL NOT appear in `settings`.

#### Scenario: settings does not contain skill_permanent

- **WHEN** `config.json` is saved by `ConfigManager.save()`
- **THEN** the resulting JSON SHALL NOT contain `settings.skill_permanent`

#### Scenario: global settings persist across profile switches

- **WHEN** the user switches to a different profile
- **THEN** `settings.current_profile` SHALL be updated and saved
- **THEN** all other `settings` keys SHALL remain unchanged


<!-- @trace
source: data-format-cleanup
updated: 2026-03-20
code:
  - docs/DATA_FORMAT.md
  - CLAUDE.md
  - src/ui/app.py
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
  - docs/ARCHITECTURE.md
  - config.json
  - src/ui/skill_manager.py
-->

---
### Requirement: Profile zone stores all per-profile user state

The `profiles/{name}.json` file SHALL be the sole storage location for:
`hotkeys`, `permanent`, `loop`, `alert_enabled`, `cooldown_overrides`,
`alert_seconds_overrides`, `sound_overrides`, `alert_sound_overrides`.

No duplicate copy of these fields SHALL exist in `config.json`.

#### Scenario: Skill hotkey is read from profile only

- **WHEN** the application loads or switches profiles
- **THEN** skill hotkeys SHALL be read exclusively from `profiles/{name}.json → hotkeys`
- **THEN** any `hotkey` field in `config.json → skills[]` SHALL be ignored

#### Scenario: Profile fields are complete on load

- **WHEN** `ConfigManager.load_profile()` loads a profile missing a required key
- **THEN** the missing key SHALL be filled with an empty dict `{}`
- **THEN** the application SHALL continue normally without error


<!-- @trace
source: data-format-cleanup
updated: 2026-03-20
code:
  - docs/DATA_FORMAT.md
  - CLAUDE.md
  - src/ui/app.py
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
  - docs/ARCHITECTURE.md
  - config.json
  - src/ui/skill_manager.py
-->

---
### Requirement: SkillManager.update_hotkey does not write to static zone

`SkillManager.update_hotkey(skill_id, hotkey)` SHALL update only the in-memory
`self.skills[skill_id]["hotkey"]` value.
It SHALL NOT write to `config_manager.config["skills"]` or any on-disk static zone representation.

#### Scenario: update_hotkey scope is memory-only

- **WHEN** `SkillManager.update_hotkey("skill_001", "F1")` is called
- **THEN** `self.skills["skill_001"]["hotkey"]` SHALL equal `"F1"`
- **THEN** `config_manager.config["skills"]` SHALL NOT be modified
- **THEN** `config_manager.save()` SHALL NOT persist `"hotkey": "F1"` in the skills array

<!-- @trace
source: data-format-cleanup
updated: 2026-03-20
code:
  - docs/DATA_FORMAT.md
  - CLAUDE.md
  - src/ui/app.py
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
  - docs/ARCHITECTURE.md
  - config.json
  - src/ui/skill_manager.py
-->

---
### Requirement: Global mutable zone stored in separate config_user.json

The system SHALL persist the global mutable zone (`settings`, `monsters`, `overlays`) in a separate file `config_user.json` adjacent to `config.json`. The bundled `config.json` (shipped in the release ZIP) SHALL contain the static zone (`skills`, `items`) plus a minimal default `settings` block and empty `monsters: []` / `overlays: []`. ConfigManager SHALL load both files at startup and merge them in memory; `set_settings` and other mutators SHALL write back to `config_user.json` only.

#### Scenario: First launch with no config_user.json migrates from existing config.json

- **GIVEN** an existing user install where `config.json` contains personalized `settings` (e.g. `sound_volume: 50`) but `config_user.json` does not yet exist
- **WHEN** the application starts
- **THEN** ConfigManager creates `config_user.json` containing the `settings`, `monsters`, `overlays` lifted from `config.json`, and subsequent reads return the migrated personalized values

#### Scenario: Mutator writes only touch config_user.json

- **GIVEN** a running app with both files present
- **WHEN** `config_manager.set_settings("sound_volume", 75)` and `config_manager.save()` are called
- **THEN** `config.json` on disk is unchanged AND `config_user.json` reflects the new value

#### Scenario: Static zone refreshed from bundled config on every load

- **GIVEN** ZIP install brings a new `config.json` with an extra entry in `skills` (a newly-released skill)
- **WHEN** the user launches the upgraded app
- **THEN** `config_manager.config["skills"]` contains the new skill entry from the bundled file (not the prior version's `skills`), AND user's `settings` / `monsters` / `overlays` from `config_user.json` are preserved


<!-- @trace
source: config-static-merge
updated: 2026-04-23
code:
  - src/infrastructure/config_manager.py
  - docs/DATA_FORMAT.md
  - README.md
  - docs/RELEASE.md
  - verify_config_migration.py
  - docs/PROJECT.md
  - scripts/strip_config_for_release.py
-->

---
### Requirement: Release ZIP ships sanitized config.json

The system SHALL provide a release-time strip script `scripts/strip_config_for_release.py` that, before PyInstaller build, replaces personal `settings` values in `config.json` with documented defaults and clears `monsters` / `overlays` to empty lists. The script SHALL preserve `skills` and `items` arrays unchanged, and SHALL back up the original `config.json` to `config.json.dev_backup` so developer workflow can restore after build.

The scrubbed `config.json` SHALL contain a top-level marker `"_user_data_stripped": true` so ConfigManager can detect the stripped state and skip migration that would overwrite user data with defaults.

#### Scenario: Strip script clears mutable zone

- **WHEN** `python scripts/strip_config_for_release.py` runs against a `config.json` containing personalized settings
- **THEN** the resulting `config.json` has `settings` reset to documented defaults, `monsters == []`, `overlays == []`, `_user_data_stripped == true`, and `skills` / `items` arrays untouched

#### Scenario: Restore developer backup after build

- **WHEN** the developer runs the strip script's restore command (e.g. `python scripts/strip_config_for_release.py --restore`)
- **THEN** `config.json.dev_backup` is moved back to `config.json` and the backup file is deleted


<!-- @trace
source: config-static-merge
updated: 2026-04-23
code:
  - src/infrastructure/config_manager.py
  - docs/DATA_FORMAT.md
  - README.md
  - docs/RELEASE.md
  - verify_config_migration.py
  - docs/PROJECT.md
  - scripts/strip_config_for_release.py
-->

---
### Requirement: ConfigManager skips migration when config.json marked stripped

The system SHALL NOT migrate `settings` / `monsters` / `overlays` from `config.json` to a new `config_user.json` if the bundled `config.json` carries `_user_data_stripped: true`. Instead, ConfigManager SHALL create an empty `config_user.json` (with default settings only) and proceed.

This prevents the upgrade path "user has stripped config.json + no prior config_user.json" from reading dev defaults as if they were the user's own.

#### Scenario: Upgrade-with-stripped path does not poison user state

- **GIVEN** a user upgrade where ZIP brought `config.json` with `_user_data_stripped: true` and no prior `config_user.json` exists
- **WHEN** the application starts
- **THEN** ConfigManager creates a fresh `config_user.json` containing only the documented default `settings` (NOT the stripped placeholder values from `config.json`), and `monsters` / `overlays` are `[]`

<!-- @trace
source: config-static-merge
updated: 2026-04-23
code:
  - src/infrastructure/config_manager.py
  - docs/DATA_FORMAT.md
  - README.md
  - docs/RELEASE.md
  - verify_config_migration.py
  - docs/PROJECT.md
  - scripts/strip_config_for_release.py
-->