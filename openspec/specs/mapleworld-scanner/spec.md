# mapleworld-scanner Specification

## Purpose

TBD - created by archiving change 'extract-mapleworld-scanner'. Update Purpose after archive.

## Requirements

### Requirement: Scanner module has no Qt dependency

The `src/infrastructure/mapleworld_scanner.py` module SHALL NOT import any `PySide6.*` or other Qt symbols. It SHALL depend only on the Python standard library, `PIL`, and `requests`.

#### Scenario: Module import is Qt-free

- **WHEN** a developer imports `src.infrastructure.mapleworld_scanner` in isolation (without any Qt runtime initialized)
- **THEN** the import succeeds with no ImportError and no Qt symbols appear in the module's namespace


<!-- @trace
source: extract-mapleworld-scanner
updated: 2026-04-24
code:
  - src/infrastructure/mapleworld_scanner.py
  - src/ui_v2/pages/monster_page_v2.py
  - version.py
  - src/ui_v2/pages/mapleworld_page_v2.py
  - src/ui_v2/pages/potion_page_v2.py
  - src/ui/pages/mapleworld_page.py
  - src/ui_v2/dialogs/settings_dialog_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/theme_v2.py
-->

---
### Requirement: scan_unity extracts images from .win.mod files

The module SHALL expose `scan_unity(game_path, on_progress, on_done)` which recursively scans `{game_path}/resource_cache/` for `*.win.mod` files, decodes DDS (flipped top-to-bottom) and embedded PNG/JPEG/WebP/GIF payloads, and writes each extracted image as PNG to `images/mapleworld/{uuid}.png` (or `{uuid}_{index}.png` when a single mod yields multiple images).

#### Scenario: Directory missing

- **WHEN** `{game_path}/resource_cache/` does not exist
- **THEN** `on_done` is invoked exactly once with an empty saved list, 0 errors, and a non-null fatal message describing the missing directory

#### Scenario: Successful unity scan

- **WHEN** the cache directory contains N valid `.win.mod` files
- **THEN** PNG files are written under `images/mapleworld/`, `on_progress` is invoked at least once per 500 processed files, and `on_done(saved, errors, None)` is invoked exactly once with `saved` listing each extracted image

#### Scenario: Scanner runs off the calling thread

- **WHEN** a caller invokes `scan_unity(...)` from the main thread
- **THEN** the call returns immediately without blocking, and both `on_progress` and `on_done` callbacks are invoked from a background daemon thread (not the calling thread)


<!-- @trace
source: extract-mapleworld-scanner
updated: 2026-04-24
code:
  - src/infrastructure/mapleworld_scanner.py
  - src/ui_v2/pages/monster_page_v2.py
  - version.py
  - src/ui_v2/pages/mapleworld_page_v2.py
  - src/ui_v2/pages/potion_page_v2.py
  - src/ui/pages/mapleworld_page.py
  - src/ui_v2/dialogs/settings_dialog_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/theme_v2.py
-->

---
### Requirement: scan_web extracts images from Vuplex.WebView cache

The module SHALL expose `scan_web(game_path, on_progress, on_done)` which walks `{game_path}/Vuplex.WebView/` for SimpleCache (`f_*`), Blockfile (`data_*`), and IndexedDB/LocalStorage (`*.ldb`, `*.log`, `*.sst`) files, then runs four phases: (1) direct byte-scan for PNG/WebP/JPEG/GIF magic bytes, (2) gzip-decompress-and-rescan, (3) extract image URLs from text and download via HTTP, (4) decode `data:image/...;base64,...` payloads. Extracted images SHALL be written as PNG to `images/mapleworld/` with filenames prefixed `web_` or `cdn_` so the V2 viewer can bucket them into the "WebView" tab.

#### Scenario: Missing Vuplex directory

- **WHEN** `{game_path}/Vuplex.WebView/` does not exist
- **THEN** `on_done` is invoked exactly once with an empty saved list, 0 errors, and a non-null fatal message describing the missing directory

#### Scenario: Successful web scan

- **WHEN** the Vuplex directory contains cache files with embedded images
- **THEN** PNG files are written under `images/mapleworld/` with filenames beginning with `web_` or `cdn_`, and `on_done(saved, errors, None)` is invoked exactly once


<!-- @trace
source: extract-mapleworld-scanner
updated: 2026-04-24
code:
  - src/infrastructure/mapleworld_scanner.py
  - src/ui_v2/pages/monster_page_v2.py
  - version.py
  - src/ui_v2/pages/mapleworld_page_v2.py
  - src/ui_v2/pages/potion_page_v2.py
  - src/ui/pages/mapleworld_page.py
  - src/ui_v2/dialogs/settings_dialog_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/theme_v2.py
-->

---
### Requirement: Scanner tolerates per-file decode errors

Both `scan_unity` and `scan_web` SHALL isolate per-file exceptions so a single malformed cache file does not abort the entire scan. The scanner SHALL increment an `errors` counter for each per-file failure and report the final count via `on_done(saved, errors, fatal)`.

#### Scenario: One file is corrupt

- **WHEN** one `.win.mod` file raises during decode but the remaining N-1 files succeed
- **THEN** `on_done` is invoked with `saved` containing images from the N-1 successful files, `errors` equal to 1, and a null fatal argument


<!-- @trace
source: extract-mapleworld-scanner
updated: 2026-04-24
code:
  - src/infrastructure/mapleworld_scanner.py
  - src/ui_v2/pages/monster_page_v2.py
  - version.py
  - src/ui_v2/pages/mapleworld_page_v2.py
  - src/ui_v2/pages/potion_page_v2.py
  - src/ui/pages/mapleworld_page.py
  - src/ui_v2/dialogs/settings_dialog_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/theme_v2.py
-->

---
### Requirement: Extraction helpers are module-level and reusable

The helpers `extract_all_dds(raw_bytes)` and `extract_images_from_bytes(raw_bytes)` SHALL be exposed as module-level functions (not class methods). They SHALL accept raw bytes and return (or yield) decoded PIL `Image` objects suitable for `.save(path, "PNG")`.

#### Scenario: Multiple DDS in a single buffer

- **WHEN** `extract_all_dds` receives a byte buffer containing 3 concatenated DDS blocks
- **THEN** the function yields 3 PIL images, each already converted to RGBA and flipped top-to-bottom

##### Example: multi-DDS extraction

- **GIVEN** a buffer `raw = pad + dds_a + pad + dds_b + pad + dds_c` where each `dds_*` is a valid DDS payload
- **WHEN** `list(extract_all_dds(raw))` is evaluated
- **THEN** the result is `[(0, img_a), (1, img_b), (2, img_c)]` in buffer order with each image in RGBA mode


<!-- @trace
source: extract-mapleworld-scanner
updated: 2026-04-24
code:
  - src/infrastructure/mapleworld_scanner.py
  - src/ui_v2/pages/monster_page_v2.py
  - version.py
  - src/ui_v2/pages/mapleworld_page_v2.py
  - src/ui_v2/pages/potion_page_v2.py
  - src/ui/pages/mapleworld_page.py
  - src/ui_v2/dialogs/settings_dialog_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/theme_v2.py
-->

---
### Requirement: UI pages delegate scanning to the scanner module

Both `src/ui/pages/mapleworld_page.py` (V1) and `src/ui_v2/pages/mapleworld_page_v2.py` (V2) SHALL invoke `scan_unity` / `scan_web` from the scanner module rather than re-implementing decode logic. UI pages SHALL dispatch scanner callbacks back to the Qt main thread before mutating widget state (e.g., via `app.after(0, ...)`).

#### Scenario: V1 scan button delegates

- **WHEN** the user clicks the Unity scan button on the V1 page
- **THEN** the page calls `scan_unity` from the scanner module (not a private V1 method), and all subsequent UI updates flow through `on_progress` / `on_done` callbacks dispatched via `app.after(0, ...)`

#### Scenario: V2 scan button delegates

- **WHEN** the user clicks the Unity scan button on the V2 page
- **THEN** the page calls `scan_unity` from the scanner module, shows a progress toast/status label, and on completion re-runs `_scan_dir()` and `_render_grid()` to reflect newly extracted PNG files

<!-- @trace
source: extract-mapleworld-scanner
updated: 2026-04-24
code:
  - src/infrastructure/mapleworld_scanner.py
  - src/ui_v2/pages/monster_page_v2.py
  - version.py
  - src/ui_v2/pages/mapleworld_page_v2.py
  - src/ui_v2/pages/potion_page_v2.py
  - src/ui/pages/mapleworld_page.py
  - src/ui_v2/dialogs/settings_dialog_v2.py
  - src/ui_v2/pages/skill_page_v2.py
  - src/ui_v2/theme_v2.py
-->