# Overlay Window Lifecycle

## Purpose

Defines the behavior of floating image overlay windows, including lifecycle management,
persistence rules, image format constraints, initial sizing, and user data path strategy.

---

## ADDED Requirements

### Requirement: Toggle opens or closes a window

`OverlayManager.toggle(overlay_id)` SHALL open the window if it is not currently active,
or close it if it is already open.

#### Scenario: Toggle opens closed window

- **WHEN** `toggle("ov_abc")` is called and no window exists for `"ov_abc"`
- **THEN** `open_window("ov_abc")` SHALL be called and a floating window SHALL appear

#### Scenario: Toggle closes open window

- **WHEN** `toggle("ov_abc")` is called and a window is already open for `"ov_abc"`
- **THEN** `close_window("ov_abc")` SHALL be called and the window SHALL disappear

---

### Requirement: Open window requires existing image file

`open_window(overlay_id)` SHALL open a floating window only if:
1. The overlay data exists in `config.json → overlays[]`
2. The image file exists at `overlays/{data.file}` (user data directory)

If either condition is not met, the method SHALL return without opening a window.

#### Scenario: Image file missing

- **WHEN** `open_window("ov_abc")` is called but the image file does not exist on disk
- **THEN** no window SHALL be created and no error SHALL be raised

---

### Requirement: Alpha update is immediate and persisted

`OverlayManager.set_alpha(overlay_id, alpha)` SHALL:
1. Immediately update the alpha of the active window (if open)
2. Store the rounded value (`round(alpha, 2)`) in overlay data
3. Call `config_manager.save()` to persist

#### Scenario: Alpha change is visible immediately

- **WHEN** `set_alpha("ov_abc", 0.5)` is called while the window is open
- **THEN** the window opacity SHALL change immediately to 0.5
- **THEN** `config.json → overlays[ov_abc].alpha` SHALL be saved as `0.5`

---

### Requirement: Position is persisted on drag end

When the user drags an overlay window to a new position,
`OverlayManager._on_position_change(overlay_id, x, y)` SHALL update
`overlay.x` and `overlay.y` in memory and call `config_manager.save()`.

#### Scenario: Drag end persists position

- **WHEN** the user finishes dragging overlay "ov_abc" to position (300, 400)
- **THEN** `config.json → overlays[ov_abc].x` SHALL be 300 and `.y` SHALL be 400

---

### Requirement: Size change uses close-reopen strategy

`OverlayManager.resize_window(overlay_id, w, h)` SHALL:
1. Enforce minimum dimensions: `w = max(10, w)`, `h = max(10, h)`
2. If the window is open, save its current position before closing
3. Update `overlay.width` and `overlay.height` and call `config_manager.save()`
4. If the window was open, close it and reopen it after 50ms (via `app.after(50, ...)`)

#### Scenario: Resize triggers reopen

- **WHEN** `resize_window("ov_abc", 400, 300)` is called while the window is open
- **THEN** the window SHALL close and reopen after 50ms with the new dimensions
- **THEN** `config.json → overlays[ov_abc].width` SHALL be 400 and `.height` SHALL be 300

---

### Requirement: Image format is validated on add

`OverlayManager.add_overlay(src_path, name)` SHALL accept only files with extensions:
`.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.webp` (case-insensitive).
Files with other extensions SHALL be rejected and the method SHALL return `None`.

#### Scenario: Unsupported format rejected

- **WHEN** `add_overlay("/path/to/image.tiff", "test")` is called
- **THEN** the method SHALL return `None` and no file SHALL be copied

#### Scenario: Supported format accepted

- **WHEN** `add_overlay("/path/to/image.png", "test")` is called
- **THEN** the file SHALL be copied to `overlays/` with a UUID-based filename
- **THEN** the overlay data SHALL be appended to `config.json → overlays[]`

---

### Requirement: Initial size is constrained to 600px on longest edge

When adding a new overlay, the system SHALL calculate an initial display size such that
the longest edge does not exceed 600px, preserving the original aspect ratio.
If image dimensions cannot be determined, the fallback size SHALL be 200×200 px.

#### Scenario: Large image is scaled down

- **WHEN** an image with original size 1200×800 is added
- **THEN** the initial display size SHALL be 600×400 (scaled to longest edge = 600)

#### Scenario: Small image is not scaled up

- **WHEN** an image with original size 200×150 is added
- **THEN** the initial display size SHALL be 200×150 (no upscaling)

---

### Requirement: User data paths use exe-relative directory

All user-writable data (overlays/, sounds/, profiles/) SHALL be resolved using `_user_path()`:
- In packaged mode (`sys.frozen`): relative to `sys.executable` directory
- In development mode: relative to the project root (current working directory)

Bundled read-only assets SHALL use `resource_path()` (NOT `_user_path()`).

#### Scenario: Overlay file path in packaged mode

- **WHEN** the application runs as a packaged exe at `C:\Tools\skill_tracker.exe`
- **THEN** `_user_path("overlays/abc.png")` SHALL resolve to `C:\Tools\overlays\abc.png`

---

### Requirement: Delete overlay closes window and removes file

`OverlayManager.delete_overlay(overlay_id, delete_file)` SHALL:
1. Close the active window if open
2. Remove the overlay entry from `config.json → overlays[]`
3. If `delete_file=True`, also delete the image file from disk

#### Scenario: Delete with file removal

- **WHEN** `delete_overlay("ov_abc", delete_file=True)` is called
- **THEN** the window SHALL be closed
- **THEN** the overlay entry SHALL be removed from config
- **THEN** the image file SHALL be deleted from `overlays/`
