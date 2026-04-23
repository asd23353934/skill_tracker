## ADDED Requirements

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

### Requirement: Release ZIP ships sanitized config.json

The system SHALL provide a release-time strip script `scripts/strip_config_for_release.py` that, before PyInstaller build, replaces personal `settings` values in `config.json` with documented defaults and clears `monsters` / `overlays` to empty lists. The script SHALL preserve `skills` and `items` arrays unchanged, and SHALL back up the original `config.json` to `config.json.dev_backup` so developer workflow can restore after build.

The scrubbed `config.json` SHALL contain a top-level marker `"_user_data_stripped": true` so ConfigManager can detect the stripped state and skip migration that would overwrite user data with defaults.

#### Scenario: Strip script clears mutable zone

- **WHEN** `python scripts/strip_config_for_release.py` runs against a `config.json` containing personalized settings
- **THEN** the resulting `config.json` has `settings` reset to documented defaults, `monsters == []`, `overlays == []`, `_user_data_stripped == true`, and `skills` / `items` arrays untouched

#### Scenario: Restore developer backup after build

- **WHEN** the developer runs the strip script's restore command (e.g. `python scripts/strip_config_for_release.py --restore`)
- **THEN** `config.json.dev_backup` is moved back to `config.json` and the backup file is deleted

### Requirement: ConfigManager skips migration when config.json marked stripped

The system SHALL NOT migrate `settings` / `monsters` / `overlays` from `config.json` to a new `config_user.json` if the bundled `config.json` carries `_user_data_stripped: true`. Instead, ConfigManager SHALL create an empty `config_user.json` (with default settings only) and proceed.

This prevents the upgrade path "user has stripped config.json + no prior config_user.json" from reading dev defaults as if they were the user's own.

#### Scenario: Upgrade-with-stripped path does not poison user state

- **GIVEN** a user upgrade where ZIP brought `config.json` with `_user_data_stripped: true` and no prior `config_user.json` exists
- **WHEN** the application starts
- **THEN** ConfigManager creates a fresh `config_user.json` containing only the documented default `settings` (NOT the stripped placeholder values from `config.json`), and `monsters` / `overlays` are `[]`
