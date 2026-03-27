## MODIFIED Requirements

### Requirement: Repositories have zero Qt dependency

All repository classes SHALL be defined in `src/infrastructure/repositories.py` and SHALL NOT import any PySide6 or Qt modules. They SHALL depend only on `ConfigManager` (from `src.infrastructure.config_manager`) and domain models (from `src.domain.models`). The `ConfigManager` type hint SHALL use a direct import, not a TYPE_CHECKING guard referencing `src.ui`.

#### Scenario: Import repositories without Qt installed

- **WHEN** `src/infrastructure/repositories.py` is imported with `ConfigManager` available but PySide6 not installed
- **THEN** the import succeeds without errors

#### Scenario: Repositories import ConfigManager from infrastructure

- **WHEN** `src/infrastructure/repositories.py` is inspected for import statements
- **THEN** the `ConfigManager` reference resolves to `src.infrastructure.config_manager`, not `src.ui.config_manager`
