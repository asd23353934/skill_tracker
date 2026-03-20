# Profile Management

## Purpose

Defines the behavior of the profile CRUD system, profile switching, state reset order,
filename security validation, and missing field recovery.

---

## ADDED Requirements

### Requirement: Profile filename security validation

`ConfigManager._validate_filename(name)` SHALL reject names that:
- Are empty strings
- Contain `/`, `\`, or `..` substrings

Valid names SHALL be accepted regardless of character composition (digits, spaces, CJK characters are allowed).
All profile CRUD methods SHALL call `_validate_filename()` before any file operation and return `False` / `None` on failure.

#### Scenario: Path traversal attempt is rejected

- **WHEN** `save_profile("../evil", data)` is called
- **THEN** `_validate_filename("../evil")` SHALL return `False`
- **THEN** the save operation SHALL be aborted and return `False`

#### Scenario: Valid name is accepted

- **WHEN** `save_profile("預設配置", data)` is called
- **THEN** `_validate_filename("預設配置")` SHALL return `True`
- **THEN** the file SHALL be written to `profiles/預設配置.json`

---

### Requirement: Profile CRUD operations

The system SHALL support the following profile operations:
- `list_profiles()`: return sorted list of profile names (without `.json` extension)
- `save_profile(name, data)`: write `data` as JSON to `profiles/{name}.json`
- `load_profile(name)`: read and return data dict from `profiles/{name}.json`
- `delete_profile(name)`: remove `profiles/{name}.json` from disk
- `rename_profile(old_name, new_name)`: rename the profile file atomically

#### Scenario: List profiles returns sorted names

- **WHEN** `profiles/` contains `甲.json`, `乙.json`, `丙.json`
- **THEN** `list_profiles()` SHALL return `["乙", "丙", "甲"]` (sorted)

#### Scenario: Save then load roundtrip

- **WHEN** `save_profile("test", {"hotkeys": {"s1": "F1"}})` is called
- **THEN** `load_profile("test")` SHALL return a dict containing `{"hotkeys": {"s1": "F1"}}`

#### Scenario: Delete removes file

- **WHEN** `delete_profile("test")` is called and `profiles/test.json` exists
- **THEN** the file SHALL be removed from disk
- **THEN** `"test"` SHALL NOT appear in `list_profiles()`

---

### Requirement: Missing profile fields are filled on load

`load_profile()` SHALL ensure the following keys exist in the returned dict,
filling missing keys with empty dicts `{}`:
`hotkeys`, `permanent`, `loop`, `alert_enabled`, `cooldown_overrides`.

#### Scenario: Old profile missing alert_enabled

- **WHEN** `profiles/old.json` contains only `{"hotkeys": {}, "permanent": {}}`
- **THEN** `load_profile("old")` SHALL return a dict also containing `"loop": {}`, `"alert_enabled": {}`, `"cooldown_overrides": {}`

---

### Requirement: Profile switch resets skill state before applying

`App._apply_profile(profile_data)` SHALL execute in this order:
1. Reset every skill's `hotkey` to `""` and `cooldown` to its original value
2. Apply `profile_data["hotkeys"]` to each skill's `hotkey`
3. Apply `profile_data["cooldown_overrides"]` to each skill's `cooldown`
4. Replace in-memory state dicts: `permanent`, `loop`, `alert_enabled`, and override maps

No residual state from the previous profile SHALL remain after step 1.

#### Scenario: Previous hotkey is cleared on switch

- **WHEN** the current profile has `hotkeys: {"s1": "F1"}` and the user switches to a profile with `hotkeys: {}`
- **THEN** after `_apply_profile()`, `skill_manager.get_skill("s1")["hotkey"]` SHALL equal `""`

#### Scenario: New profile hotkeys are applied

- **WHEN** `_apply_profile({"hotkeys": {"s2": "F2"}, ...})` is called
- **THEN** `skill_manager.get_skill("s2")["hotkey"]` SHALL equal `"F2"`

---

### Requirement: current_profile is persisted in settings

`config.json → settings.current_profile` SHALL always reflect the name of the currently active profile.
`ConfigManager.set_current_profile(name)` SHALL update this value and call `save()`.

#### Scenario: Profile switch persists current_profile

- **WHEN** the user switches to profile "戰士配置"
- **THEN** `config.json → settings.current_profile` SHALL be `"戰士配置"` after save

---

### Requirement: Default profile is ensured on startup

`ConfigManager.ensure_default_profile()` SHALL create `profiles/預設配置.json` if it does not exist,
and set `current_profile` to `"預設配置"` if no current profile is set.

#### Scenario: First launch creates default profile

- **WHEN** `profiles/` is empty and `settings.current_profile` is absent
- **THEN** `ensure_default_profile()` SHALL create `profiles/預設配置.json`
- **THEN** `settings.current_profile` SHALL be set to `"預設配置"`
