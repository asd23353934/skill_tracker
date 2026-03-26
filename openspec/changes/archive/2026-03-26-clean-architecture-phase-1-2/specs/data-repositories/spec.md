## ADDED Requirements

### Requirement: SkillRepository provides read-only skill metadata access

The system SHALL provide a `SkillRepository` class that wraps `ConfigManager` and returns `SkillMetadata` domain models. It SHALL provide: `get_all() -> dict[str, SkillMetadata]` returning all skills and items keyed by id, `get(skill_id: str) -> SkillMetadata | None` returning a single skill by id, and `get_by_category(category: str) -> list[SkillMetadata]` returning skills filtered by category. The repository SHALL combine `initial_skills` and `initial_items` from ConfigManager into a unified collection.

#### Scenario: Get all skills returns SkillMetadata instances

- **WHEN** `get_all()` is called on a `SkillRepository` initialized with a ConfigManager that has 3 skills and 2 items
- **THEN** a dict with 5 entries is returned, each value being a `SkillMetadata` instance

#### Scenario: Get skill by id returns matching SkillMetadata

- **WHEN** `get("mapleWarrior")` is called and the skill exists
- **THEN** a `SkillMetadata` instance with `id="mapleWarrior"` and `name="楓葉祝福"` is returned

#### Scenario: Get skill by nonexistent id returns None

- **WHEN** `get("nonexistent")` is called and no skill with that id exists
- **THEN** `None` is returned

### Requirement: ProfileRepository provides typed profile CRUD

The system SHALL provide a `ProfileRepository` class that wraps `ConfigManager` and converts between profile JSON dicts and `Profile` domain models. It SHALL provide: `load(name: str) -> Profile | None`, `save(profile: Profile) -> bool`, `list_all() -> list[str]`, `delete(name: str) -> bool`, `rename(old_name: str, new_name: str) -> bool`, and `ensure_default(all_skill_ids: list[str]) -> None`.

#### Scenario: Load profile converts JSON dict to Profile model

- **WHEN** `load("預設配置")` is called and the profile JSON contains `{"hotkeys": {"mapleWarrior": "F1"}, "permanent": {"mapleWarrior": true}, "loop": {}, "alert_enabled": {}, "cooldown_overrides": {}}`
- **THEN** a `Profile` instance is returned with `name="預設配置"`, and `get_state("mapleWarrior")` returns a `SkillState` with `hotkey="F1"` and `permanent=True`

#### Scenario: Load nonexistent profile returns None

- **WHEN** `load("nonexistent")` is called and no such profile file exists
- **THEN** `None` is returned

#### Scenario: Save profile converts Profile model back to JSON dict

- **WHEN** `save(profile)` is called with a `Profile` containing a `SkillState` with `hotkey="F2"` and `permanent=True` for skill_id `"sharpEyes"`
- **THEN** ConfigManager's `save_profile()` is called with a dict containing `{"hotkeys": {"sharpEyes": "F2"}, "permanent": {"sharpEyes": true}, ...}` and the method returns `True`

#### Scenario: List all profiles delegates to ConfigManager

- **WHEN** `list_all()` is called
- **THEN** the result matches `ConfigManager.list_profiles()`

### Requirement: MonsterRepository provides typed monster data access

The system SHALL provide a `MonsterRepository` class that wraps `ConfigManager` and returns `MonsterData` domain models. It SHALL provide: `get_all() -> list[MonsterData]`, `get(monster_id: str) -> MonsterData | None`, `get_by_hotkey(key: str) -> MonsterData | None`, `save_all(monsters: list[MonsterData]) -> bool`, and `get_original_respawn_time(monster_id: str) -> int | None`.

#### Scenario: Get all monsters returns MonsterData instances

- **WHEN** `get_all()` is called and config.json contains 3 monster entries
- **THEN** a list of 3 `MonsterData` instances is returned

#### Scenario: Get monster by hotkey returns matching MonsterData

- **WHEN** `get_by_hotkey("F5")` is called and one monster has `hotkey="F5"`
- **THEN** the matching `MonsterData` instance is returned

#### Scenario: Save all monsters converts MonsterData back to dicts

- **WHEN** `save_all(monsters)` is called with a list of `MonsterData` instances
- **THEN** `ConfigManager.config["monsters"]` is updated with the equivalent dict representations and `ConfigManager.save()` is called

### Requirement: OverlayRepository provides typed overlay data access

The system SHALL provide an `OverlayRepository` class that wraps `ConfigManager` and returns `OverlayData` domain models. It SHALL provide: `get_all() -> list[OverlayData]` and `save_all(overlays: list[OverlayData]) -> bool`.

#### Scenario: Get all overlays returns OverlayData instances

- **WHEN** `get_all()` is called and config.json contains 2 overlay entries
- **THEN** a list of 2 `OverlayData` instances is returned

#### Scenario: Save all overlays persists to config.json

- **WHEN** `save_all(overlays)` is called with a list of `OverlayData` instances
- **THEN** `ConfigManager.config["overlays"]` is updated and `ConfigManager.save()` is called

### Requirement: SettingsRepository provides typed global settings access

The system SHALL provide a `SettingsRepository` class that wraps `ConfigManager` and returns a `GlobalSettings` domain model. It SHALL provide: `load() -> GlobalSettings` and `save(settings: GlobalSettings) -> bool`.

#### Scenario: Load settings converts config.json settings to GlobalSettings

- **WHEN** `load()` is called and config.json has `settings.player_name = "玩家1"` and `settings.enable_sound = true`
- **THEN** a `GlobalSettings` instance is returned with `player_name="玩家1"` and `enable_sound=True`

#### Scenario: Save settings writes GlobalSettings back to config.json

- **WHEN** `save(settings)` is called with a `GlobalSettings` instance where `enable_sound=False`
- **THEN** `ConfigManager.config["settings"]["enable_sound"]` is set to `False` and `ConfigManager.save()` is called

### Requirement: Repositories have zero Qt dependency

All repository classes SHALL be defined in `src/domain/repositories.py` and SHALL NOT import any PySide6 or Qt modules. They SHALL depend only on `ConfigManager` and domain models.

#### Scenario: Import repositories without Qt installed

- **WHEN** `src/domain/repositories.py` is imported with `ConfigManager` available but PySide6 not installed
- **THEN** the import succeeds without errors
