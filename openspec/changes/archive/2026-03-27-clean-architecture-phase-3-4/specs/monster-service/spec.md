## ADDED Requirements

### Requirement: MonsterService provides monster state queries

The system SHALL provide a `MonsterService` class in `src/domain/services.py` that centralizes all monster state query logic. It SHALL provide: `get(monster_id) -> dict | None` returning the monster data dict, `get_by_hotkey(key_str) -> dict | None` returning the monster with the matching hotkey (case-insensitive), `get_all() -> list[dict]` returning all monster data dicts, and `get_original_respawn_time(monster_id) -> int | None` returning the original respawn time before any user modifications.

#### Scenario: Get monster by id

- **WHEN** `get("fish_house")` is called and a monster with id "fish_house" exists
- **THEN** the monster data dict is returned with `name`, `respawn_time`, `hotkey`, and other fields

#### Scenario: Get monster by hotkey

- **WHEN** `get_by_hotkey("F5")` is called and monster "fish_house" has `hotkey="F5"`
- **THEN** the monster data dict for "fish_house" is returned

#### Scenario: Get monster by nonexistent hotkey returns None

- **WHEN** `get_by_hotkey("F12")` is called and no monster has that hotkey
- **THEN** `None` is returned

### Requirement: MonsterService manages respawn time with reset support

The system SHALL provide `set_respawn_time(monster_id, seconds) -> bool` that updates a monster's respawn time and returns True if the value differs from the original. The system SHALL also provide `reset_respawn_time(monster_id) -> int | None` that restores the respawn time to its original value and returns that value, or returns None if the monster is not found or already at the original value.

#### Scenario: Set respawn time returns modified flag

- **WHEN** `set_respawn_time("fish_house", 60)` is called and the original respawn time is 30
- **THEN** the method returns `True` and the monster's respawn_time is updated to 60

#### Scenario: Reset respawn time restores original

- **WHEN** `reset_respawn_time("fish_house")` is called and the monster's respawn time was modified to 60 (original is 30)
- **THEN** the method returns `30` and the monster's respawn_time is restored to 30

#### Scenario: Reset respawn time when already at original

- **WHEN** `reset_respawn_time("fish_house")` is called and the monster's respawn time is already 30 (original is 30)
- **THEN** the method returns `None` indicating no change was needed

### Requirement: MonsterService manages monster hotkey binding

The system SHALL provide `set_hotkey(monster_id, key_str) -> str | None` that assigns a hotkey to a monster. If another monster already has the same hotkey, the old binding SHALL be cleared and the displaced monster_id SHALL be returned. The system SHALL also provide `clear_hotkey(monster_id)`.

#### Scenario: Set monster hotkey with conflict

- **WHEN** `set_hotkey("fish_house", "F5")` is called and monster "boss_1" already has hotkey "F5"
- **THEN** `"boss_1"` is returned and boss_1's hotkey is cleared

#### Scenario: Clear monster hotkey

- **WHEN** `clear_hotkey("fish_house")` is called and the monster had hotkey "F5"
- **THEN** the monster's hotkey is set to `""`

### Requirement: MonsterService manages loop and permanent state

The system SHALL provide `set_loop(monster_id, value) -> None` and `set_permanent(monster_id, value) -> None` that update the respective flags on a monster. The system SHALL also provide `set_alert_before(monster_id, seconds) -> None`, `set_sound(monster_id, filename) -> None`, and `set_alert_sound(monster_id, filename) -> None`.

#### Scenario: Set monster loop

- **WHEN** `set_loop("fish_house", True)` is called
- **THEN** the monster's loop flag is set to True

#### Scenario: Set monster alert before seconds

- **WHEN** `set_alert_before("fish_house", 15)` is called
- **THEN** the monster's alert_before is set to 15

### Requirement: MonsterService persists changes via ConfigManager

The system SHALL provide `save() -> bool` that persists all monster data changes to config.json via ConfigManager. All mutation methods (`set_respawn_time`, `set_hotkey`, `clear_hotkey`, `set_loop`, `set_permanent`, `set_alert_before`, `set_sound`, `set_alert_sound`) SHALL NOT auto-save; the caller SHALL explicitly call `save()` after mutations.

#### Scenario: Save persists monster changes

- **WHEN** `set_respawn_time("fish_house", 60)` is called followed by `save()`
- **THEN** `ConfigManager.save()` is called and the updated monster data is written to config.json

### Requirement: MonsterService has zero Qt dependency

The `MonsterService` class SHALL be defined in `src/domain/services.py` and SHALL NOT import any PySide6 or Qt modules. It SHALL depend only on `ConfigManager` and domain models.

#### Scenario: Import MonsterService without Qt

- **WHEN** `src/domain/services.py` is imported without PySide6 installed
- **THEN** the import succeeds without errors
