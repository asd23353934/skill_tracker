## ADDED Requirements

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

### Requirement: Confirmation dialogs remain as modal dialogs

The application SHALL preserve `QMessageBox.question()` confirmation dialogs (e.g., delete confirmation, overwrite confirmation) as modal blocking dialogs, because they require user input before proceeding.

#### Scenario: Delete confirmation remains modal

- **WHEN** the user initiates a destructive action (e.g., delete profile, delete image)
- **THEN** the system SHALL display a `QMessageBox.question()` dialog and wait for user confirmation before proceeding

### Requirement: Pre-initialization errors remain as modal dialogs

The application SHALL preserve the startup `QMessageBox.critical(None, ...)` call that fires before the `App` instance (and thus `ToastManager`) is initialized.

#### Scenario: App initialization failure remains modal

- **WHEN** the application fails to initialize before `App.__init__` completes
- **THEN** the system SHALL display a `QMessageBox.critical(None, ...)` dialog, as `app.toast` is not yet available
