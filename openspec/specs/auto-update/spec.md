# auto-update Specification

## Purpose

TBD - created by archiving change 'auto-update'. Update Purpose after archive.

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
  - src/ui/skill_manager.py
  - docs/CODE_STYLE.md
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
  - docs/PROJECT.md
  - CLAUDE.md
  - config.json
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
  - src/ui/skill_manager.py
  - docs/CODE_STYLE.md
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
  - docs/PROJECT.md
  - CLAUDE.md
  - config.json
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
  - src/ui/skill_manager.py
  - docs/CODE_STYLE.md
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
  - docs/PROJECT.md
  - CLAUDE.md
  - config.json
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
  - src/ui/skill_manager.py
  - docs/CODE_STYLE.md
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
  - docs/PROJECT.md
  - CLAUDE.md
  - config.json
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
  - src/ui/skill_manager.py
  - docs/CODE_STYLE.md
  - src/ui/app.py
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/RELEASE.md
  - src/ui/hotkey_manager.py
  - docs/PROJECT.md
  - CLAUDE.md
  - config.json
-->