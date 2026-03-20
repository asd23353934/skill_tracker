# Data Format

## Purpose

Defines the three data partition boundaries in `config.json` and `profiles/`,
specifying which fields belong in each zone and forbidden field rules.

---

## ADDED Requirements

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
