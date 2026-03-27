## MODIFIED Requirements

### Requirement: Domain models have zero Qt dependency

All domain model classes (`SkillMetadata`, `SkillState`, `Profile`, `MonsterData`, `OverlayData`, `GlobalSettings`) SHALL be defined in `src/domain/models.py` and SHALL NOT import any PySide6 or Qt modules. They SHALL use only Python standard library types. No module in `src/domain/` SHALL import from `src.ui` or `src.infrastructure`, not even under `TYPE_CHECKING` blocks. The domain layer SHALL depend only on Python standard library modules.

#### Scenario: Import domain models without Qt installed

- **WHEN** `src/domain/models.py` is imported in an environment without PySide6
- **THEN** the import succeeds without errors

#### Scenario: Domain layer has no outward imports

- **WHEN** all `.py` files in `src/domain/` are scanned for import statements
- **THEN** no import references `src.ui` or `src.infrastructure` (including TYPE_CHECKING blocks)
