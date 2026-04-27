# auto-update Specification

## Purpose

定義 Skill Tracker 的自動更新機制：包含 GitHub Release API 版本檢查、檔案下載、
以及 V2 預覽 shell 啟動時的背景檢查與更新對話框流程。
所有實作集中於 `src/infrastructure/updater.py`（網路 / 檔案 I/O）與
`src/ui_v2/dialogs/update_dialog_v2.py`（UI），由 `main_v2.py` 啟動時排程觸發。

## Requirements

### Requirement: Version check queries GitHub Release API

`Updater.check_for_updates()` SHALL send a GET request to the GitHub Release API
with a timeout of 5 seconds.

If `requests` is not installed (`HAS_REQUESTS = False`), the method SHALL return
`{"available": False, "error": "requests module not installed"}` immediately without making a network request.

If the request fails for any reason (network error, HTTP error, parse error),
the method SHALL return `{"available": False, "error": <message>}`.

#### Scenario: requests not installed

- **WHEN** `requests` is not importable
- **THEN** `check_for_updates()` SHALL return `{"available": False, "error": "requests module not installed"}`
- **THEN** no network request SHALL be made

#### Scenario: API returns latest release

- **WHEN** the GitHub API returns a valid release JSON
- **THEN** the `tag_name` field SHALL be parsed (stripping the leading `"v"`) as the latest version


<!-- @trace
source: auto-update
updated: 2026-03-20
code:
  - src/infrastructure/updater.py
-->

---
### Requirement: Version comparison uses packaging with numeric fallback

`Updater._compare_versions(latest, current)` SHALL:
1. First attempt comparison using `packaging.version.parse()` if `HAS_PACKAGING` is `True`
2. Fall back to integer list comparison (`[int(x) for x in ver.split('.')]`) if packaging is unavailable
3. Return `True` if `latest` is strictly greater than `current`, otherwise `False`
4. Return `False` if any comparison raises an exception

#### Scenario: Newer version detected via packaging

- **WHEN** `latest = "2.0.0"` and `current = "1.5.3"` and packaging is available
- **THEN** `_compare_versions("2.0.0", "1.5.3")` SHALL return `True`

#### Scenario: Same version is not an update

- **WHEN** `latest = "1.5.3"` and `current = "1.5.3"`
- **THEN** `_compare_versions("1.5.3", "1.5.3")` SHALL return `False`


<!-- @trace
source: auto-update
updated: 2026-03-20
code:
  - src/infrastructure/updater.py
-->

---
### Requirement: Download asset is selected by priority

When `check_for_updates()` finds a newer version, the download URL SHALL be selected in this order:
1. First `.exe` asset found in `release.assets`
2. First `.7z`, `.zip`, or `.tar.gz` asset found in `release.assets`
3. Fallback URL: `https://github.com/.../releases/download/v{version}/skill_tracker_v{version}.zip`

#### Scenario: EXE asset preferred over archive

- **WHEN** release assets contain both `skill_tracker.exe` and `skill_tracker.zip`
- **THEN** `download_url` SHALL point to the `.exe` asset

#### Scenario: Fallback URL used when no assets

- **WHEN** `release.assets` is empty
- **THEN** `download_url` SHALL be the hardcoded fallback URL containing the version number


<!-- @trace
source: auto-update
updated: 2026-03-20
code:
  - src/infrastructure/updater.py
-->

---
### Requirement: Download streams with progress callback

`Updater.download_update(url, dest_path, progress_callback)` SHALL:
1. Stream the file in 8192-byte chunks
2. Call `progress_callback(downloaded_bytes, total_bytes)` after each chunk if provided
3. Return `True` on success, `False` on failure
4. On failure, delete any partially downloaded file at `dest_path`

#### Scenario: Progress callback is called per chunk

- **WHEN** `download_update(url, path, callback)` downloads a 100KB file
- **THEN** `callback` SHALL be called multiple times with increasing `downloaded_bytes`
- **THEN** `callback` SHALL be called at least once with `total_bytes > 0` if `Content-Length` header is present

#### Scenario: Failed download is cleaned up

- **WHEN** a network error occurs mid-download
- **THEN** `download_update()` SHALL delete the partial file at `dest_path`
- **THEN** the method SHALL return `False`


<!-- @trace
source: auto-update
updated: 2026-03-20
code:
  - src/infrastructure/updater.py
-->

---
### Requirement: Update launcher path uses resource_path

`Updater.get_launcher_path()` SHALL return the path to `update_launcher.bat`
resolved via `helpers.resource_path()`, supporting both development and packaged modes.

#### Scenario: Launcher path resolves correctly

- **WHEN** `get_launcher_path()` is called
- **THEN** the returned path SHALL point to `update_launcher.bat` relative to the application root

<!-- @trace
source: auto-update
updated: 2026-03-20
code:
  - src/infrastructure/updater.py
-->

---
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


<!-- @trace
source: wire-v2-update-checker
updated: 2026-04-26
code:
  - main_v2.py
  - src/ui_v2/dialogs/update_dialog_v2.py
  - verify_v2_update_checker.py
-->

---
### Requirement: V2 update dialog is shown only when a newer version is available

When the V2 update check completes on the main thread, the result handler SHALL
open `UpdateDialog` (from `src/ui_v2/dialogs/update_dialog_v2.py`) ONLY when
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

<!-- @trace
source: wire-v2-update-checker
updated: 2026-04-26
code:
  - main_v2.py
  - src/ui_v2/dialogs/update_dialog_v2.py
  - verify_v2_update_checker.py
-->