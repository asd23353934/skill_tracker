## ADDED Requirements

### Requirement: V2 preview shell schedules update check on startup

The V2 preview shell (`PreviewWindow` in `main_v2.py`) SHALL schedule an
asynchronous update check 1000 milliseconds after the window is constructed,
mirroring the behavior of V1's `App._check_for_updates`.

The scheduling SHALL use `QTimer.singleShot(1000, ...)` so the network call
runs off the main event loop and does not block window creation.

The actual `Updater.check_for_updates()` invocation SHALL run inside a daemon
thread (`threading.Thread(daemon=True)`), and the result SHALL be marshalled
back to the main thread via `app_ctx.after(0, ...)` (the V2 dispatcher) before
any UI is touched.

If the V2 preview shell is launched during automated tests (detected via the
`SKILL_TRACKER_DISABLE_UPDATE_CHECK` environment variable being set to `"1"`),
the scheduling SHALL be skipped entirely so test runs do not hit the network.

#### Scenario: PreviewWindow schedules update check after construction

- **WHEN** `PreviewWindow.__init__` finishes
- **THEN** a `QTimer.singleShot` call with delay `1000` SHALL be registered
- **THEN** no network request SHALL be made synchronously during construction

#### Scenario: Update check runs off main thread

- **WHEN** the scheduled callback fires
- **THEN** `Updater.check_for_updates()` SHALL be invoked inside a daemon thread
- **THEN** the result SHALL be passed back to the main thread via `app_ctx.after(0, ...)`

#### Scenario: Test mode skips update check

- **WHEN** `SKILL_TRACKER_DISABLE_UPDATE_CHECK=1` is set in the environment
- **THEN** `PreviewWindow.__init__` SHALL NOT register the `QTimer.singleShot` for the update check
- **THEN** no daemon thread SHALL be spawned for `Updater.check_for_updates`

---

### Requirement: V2 update dialog is shown only when a newer version is available

When the V2 update check completes on the main thread, the result handler SHALL
open `UpdateDialog` (from `src/ui/dialogs/update_dialog.py`) ONLY when
`update_info.get("available")` is truthy. (The `Updater.check_for_updates()`
contract guarantees that when `available` is `True`, the keys `current`,
`latest`, and `download_url` are present and populated, so no further key
validation is required.)

The dialog SHALL be constructed with the active `PreviewWindow` instance as its
parent so it inherits modal behavior and z-order against the V2 main window.

If `update_info` indicates no update (`available is False`), an error
(`update_info.get("error")` is non-empty), or the result is `None`, the handler
SHALL NOT open any dialog and SHALL NOT raise. The error (if any) SHALL be
written to console via `print(...)` only — no toast and no message box.

If constructing or opening `UpdateDialog` raises an exception, the handler
SHALL catch the exception, write a one-line error to console, and return
without crashing the V2 shell.

#### Scenario: Newer version available opens dialog

- **WHEN** the update check returns `{"available": True, "current": "1.0.0", "latest": "9.9.9", "download_url": "https://example/x.exe"}`
- **THEN** `UpdateDialog(preview_window, update_info)` SHALL be instantiated
- **THEN** the dialog's `exec()` or `show()` SHALL be called

#### Scenario: No update available does not open dialog

- **WHEN** the update check returns `{"available": False}`
- **THEN** no `UpdateDialog` SHALL be constructed
- **THEN** no exception SHALL be raised

#### Scenario: Network failure does not crash V2 shell

- **WHEN** the update check returns `{"available": False, "error": "network unreachable"}`
- **THEN** no `UpdateDialog` SHALL be constructed
- **THEN** the error string SHALL be written to console via `print(...)`
- **THEN** no toast or message box SHALL be shown to the user

#### Scenario: Dialog construction error is swallowed

- **WHEN** instantiating `UpdateDialog` raises an unexpected exception (for example, a missing icon file)
- **THEN** the handler SHALL catch the exception
- **THEN** the V2 shell SHALL continue running
- **THEN** an error line containing the exception type SHALL be written to console
