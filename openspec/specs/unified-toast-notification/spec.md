# Spec: Unified Toast Notification

## Capability: unified-toast-notification

The application displays all non-blocking messages via the `ToastManager` system, replacing modal `QMessageBox` dialogs for informational, warning, and error feedback. Confirmation dialogs and pre-initialization errors remain as modal dialogs.

---

### Requirement: All non-blocking messages displayed via Toast

The application SHALL display all informational, warning, and error messages using the `ToastManager` system (`app.toast.show()`) in the bottom-left corner, rather than modal `QMessageBox` dialogs.

#### Scenario: Informational message shown as toast

- **WHEN** an operation produces an informational message (previously `QMessageBox.information`)
- **THEN** the system SHALL call `app.toast.show(message, "info")` and display a blue toast in the bottom-left corner

#### Scenario: Warning message shown as toast

- **WHEN** an operation produces a warning message (previously `QMessageBox.warning`)
- **THEN** the system SHALL call `app.toast.show(message, "info")` and display a blue toast in the bottom-left corner

#### Scenario: Error message shown as toast

- **WHEN** an operation fails and produces an error message (previously `QMessageBox.critical`)
- **THEN** the system SHALL call `app.toast.show(message, "error")` and display a red toast in the bottom-left corner


<!-- @trace
source: all-messages-to-toast
updated: 2026-03-20
code:
  - src/ui/dialogs/settings_dialog.py
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
  - src/ui/pages/mapleworld_page.py
  - src/ui/dialogs/skill_detail_dialog.py
  - src/ui/sidebar.py
  - src/ui/pages/overlay_page.py
  - docs/DATA_FORMAT.md
  - src/ui/dialogs/potion_save_dialog.py
  - src/ui/pages/potion_cost_page.py
  - CLAUDE.md
  - config.json
  - src/ui/dialogs/profile_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/skill_manager.py
  - src/ui/pages/roja_page.py
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
-->

---

### Requirement: Confirmation dialogs remain as modal dialogs

The application SHALL preserve `QMessageBox.question()` confirmation dialogs (e.g., delete confirmation, overwrite confirmation) as modal blocking dialogs, because they require user input before proceeding.

#### Scenario: Delete confirmation remains modal

- **WHEN** the user initiates a destructive action (e.g., delete profile, delete image)
- **THEN** the system SHALL display a `QMessageBox.question()` dialog and wait for user confirmation before proceeding


<!-- @trace
source: all-messages-to-toast
updated: 2026-03-20
code:
  - src/ui/dialogs/settings_dialog.py
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
  - src/ui/pages/mapleworld_page.py
  - src/ui/dialogs/skill_detail_dialog.py
  - src/ui/sidebar.py
  - src/ui/pages/overlay_page.py
  - docs/DATA_FORMAT.md
  - src/ui/dialogs/potion_save_dialog.py
  - src/ui/pages/potion_cost_page.py
  - CLAUDE.md
  - config.json
  - src/ui/dialogs/profile_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/skill_manager.py
  - src/ui/pages/roja_page.py
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
-->

---

### Requirement: Pre-initialization errors remain as modal dialogs

The application SHALL preserve the startup `QMessageBox.critical(None, ...)` call that fires before the `App` instance (and thus `ToastManager`) is initialized.

#### Scenario: App initialization failure remains modal

- **WHEN** the application fails to initialize before `App.__init__` completes
- **THEN** the system SHALL display a `QMessageBox.critical(None, ...)` dialog, as `app.toast` is not yet available

## Requirements


<!-- @trace
source: all-messages-to-toast
updated: 2026-03-20
code:
  - src/ui/dialogs/settings_dialog.py
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
  - src/ui/pages/mapleworld_page.py
  - src/ui/dialogs/skill_detail_dialog.py
  - src/ui/sidebar.py
  - src/ui/pages/overlay_page.py
  - docs/DATA_FORMAT.md
  - src/ui/dialogs/potion_save_dialog.py
  - src/ui/pages/potion_cost_page.py
  - CLAUDE.md
  - config.json
  - src/ui/dialogs/profile_dialog.py
  - src/ui/pages/__init__.py
  - src/ui/skill_manager.py
  - src/ui/pages/roja_page.py
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
-->

### Requirement: All non-blocking messages displayed via Toast

The application SHALL display all informational, warning, and error messages using the `ToastManager` system (`app.toast.show()`) in the bottom-left corner, rather than modal `QMessageBox` dialogs.

#### Scenario: Informational message shown as toast

- **WHEN** an operation produces an informational message (previously `QMessageBox.information`)
- **THEN** the system SHALL call `app.toast.show(message, "info")` and display a blue toast in the bottom-left corner

#### Scenario: Warning message shown as toast

- **WHEN** an operation produces a warning message (previously `QMessageBox.warning`)
- **THEN** the system SHALL call `app.toast.show(message, "info")` and display a blue toast in the bottom-left corner

#### Scenario: Error message shown as toast

- **WHEN** an operation fails and produces an error message (previously `QMessageBox.critical`)
- **THEN** the system SHALL call `app.toast.show(message, "error")` and display a red toast in the bottom-left corner

---
### Requirement: Confirmation dialogs remain as modal dialogs

The application SHALL preserve `QMessageBox.question()` confirmation dialogs (e.g., delete confirmation, overwrite confirmation) as modal blocking dialogs, because they require user input before proceeding.

#### Scenario: Delete confirmation remains modal

- **WHEN** the user initiates a destructive action (e.g., delete profile, delete image)
- **THEN** the system SHALL display a `QMessageBox.question()` dialog and wait for user confirmation before proceeding

---
### Requirement: Pre-initialization errors remain as modal dialogs

The application SHALL preserve the startup `QMessageBox.critical(None, ...)` call that fires before the `App` instance (and thus `ToastManager`) is initialized.

#### Scenario: App initialization failure remains modal

- **WHEN** the application fails to initialize before `App.__init__` completes
- **THEN** the system SHALL display a `QMessageBox.critical(None, ...)` dialog, as `app.toast` is not yet available