# hotkey-binding Specification

## Purpose

TBD - created by archiving change 'hotkey-binding-spec'. Update Purpose after archive.

## Requirements

### Requirement: Global keyboard listener

The system SHALL start a `pynput.keyboard.Listener` as a daemon thread on application launch.
The listener SHALL remain active for the entire lifetime of the application.

#### Scenario: Listener starts on launch

- **WHEN** the application initializes
- **THEN** `HotkeyManager.start()` is called and the daemon listener begins


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Hotkey namespaces are isolated

The system SHALL maintain two independent hotkey namespaces: **skill** and **monster**.
The same key MAY be bound to one skill AND one monster simultaneously without conflict.
Conflict resolution SHALL operate within each namespace independently.

#### Scenario: Same key bound to skill and monster

- **WHEN** key "F1" is assigned to a skill and the user binds "F1" to a monster
- **THEN** both bindings coexist; pressing F1 triggers the skill first, then the monster

#### Scenario: Duplicate key within skill namespace

- **WHEN** key "F1" is already bound to skill A and the user binds "F1" to skill B
- **THEN** skill A's hotkey SHALL be cleared; skill B SHALL be assigned "F1"

#### Scenario: Duplicate key within monster namespace

- **WHEN** key "F1" is already bound to monster A and the user binds "F1" to monster B
- **THEN** monster A's hotkey SHALL be cleared; monster B SHALL be assigned "F1"


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Hotkey capture mode

The system SHALL enter capture mode when `HotkeyManager.begin_capture(skill_id, skill_name)` is called.
While in capture mode, normal hotkey triggering SHALL be suspended (`enabled = False`).
Capture mode SHALL exit after a key is successfully captured or an error occurs.

#### Scenario: Enter capture mode

- **WHEN** the user initiates hotkey assignment for a skill or monster
- **THEN** `HotkeyManager.begin_capture()` is called, `waiting_for` is set, and `enabled` becomes `False`
- **THEN** the header bar SHALL display a hint message in `AppTheme.ACCENT_YELLOW`

#### Scenario: Successful capture

- **WHEN** a key press is received while in capture mode
- **THEN** the key is normalized to uppercase and assigned to the waiting skill or monster
- **THEN** `waiting_for` is cleared, `enabled` returns to `True`
- **THEN** the header bar SHALL display a confirmation message in `AppTheme.ACCENT_GREEN` for 2 seconds

#### Scenario: Capture failure

- **WHEN** an exception occurs during key capture
- **THEN** `waiting_for` is cleared, `enabled` returns to `True`
- **THEN** the header bar SHALL display an error message in `AppTheme.ACCENT_RED` for 3 seconds


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Key normalization

All hotkey values SHALL be stored and compared as uppercase strings.
Special keys SHALL use the `pynput` key name (e.g., `"f1"`, `"space"`, `"ctrl_l"`), uppercased.
Character keys SHALL use their character value, uppercased.

#### Scenario: Character key normalization

- **WHEN** the user presses the "a" key during capture
- **THEN** the stored hotkey value SHALL be `"A"`

#### Scenario: Special key normalization

- **WHEN** the user presses F5 during capture
- **THEN** the stored hotkey value SHALL be `"F5"`


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Skill hotkey storage

Skill hotkeys SHALL be stored in `profiles/{name}.json` under the `hotkeys` object, keyed by skill ID.
Skill hotkeys SHALL NOT be stored in `config.json → skills[].hotkey`.

#### Scenario: Skill hotkey persisted on assignment

- **WHEN** a hotkey is successfully captured for a skill
- **THEN** `app.auto_save_current_profile()` is called to persist the updated `hotkeys` map


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Monster hotkey storage

Monster hotkeys SHALL be stored in `config.json → monsters[].hotkey` as an uppercase string.
Monster hotkeys SHALL be saved immediately after assignment via `app.save_monsters()`.

#### Scenario: Monster hotkey persisted on assignment

- **WHEN** a hotkey is successfully captured for a monster
- **THEN** `app.save_monsters()` is called immediately


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Hotkey trigger dispatch

On a key press outside capture mode, the system SHALL:
1. Check the skill namespace first via `skill_manager.get_skill_by_hotkey(key_name)`
2. If a skill matches, dispatch `window_manager.trigger_skill(skill_id)` on the main thread
3. Otherwise, check the monster namespace via `app.get_monster_by_hotkey(key_name)`
4. If a monster matches, dispatch `window_manager.trigger_monster(monster_id)` on the main thread

#### Scenario: Skill trigger on key press

- **WHEN** the user presses a key bound to a skill
- **THEN** `app.after(0, lambda: window_manager.trigger_skill(skill_id))` is called

#### Scenario: Monster trigger on key press

- **WHEN** the user presses a key bound to a monster (and no skill matches)
- **THEN** `app.after(0, lambda: window_manager.trigger_monster(monster_id))` is called

#### Scenario: No match

- **WHEN** the user presses a key not bound to any skill or monster
- **THEN** no action is taken; no error is raised


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Thread safety for UI updates

All UI operations triggered by key events SHALL be dispatched to the main thread via `app.after(0, func)`.
The pynput listener thread SHALL NOT directly manipulate any Qt widget.

#### Scenario: Cross-thread UI update

- **WHEN** a hotkey event triggers a UI change (trigger skill window, update display)
- **THEN** the change is enqueued via `app.after(0, ...)` and executed on the Qt main thread

<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Window-scoped hotkey triggering

The system SHALL provide a global toggle that, when enabled, restricts skill and monster hotkey triggering to only when a configured target program is the foreground window. The target SHALL be matched by the foreground window's executable name. When the toggle is disabled (the default), hotkeys SHALL trigger regardless of the foreground window.

The foreground-window check SHALL be performed only after a key press has already matched a registered skill or monster hotkey, so that key presses unrelated to any hotkey incur no additional cost. Hotkey capture mode SHALL NOT be subject to this filter.

The foreground-window check SHALL use only OS calls that are safe to run on the pynput daemon thread and SHALL NOT touch any Qt widget.

#### Scenario: Hotkey suppressed when target not foreground

- **WHEN** the filter is enabled, the target program is not the foreground window, and the user presses a key bound to a skill
- **THEN** the skill SHALL NOT be triggered

#### Scenario: Hotkey allowed when target is foreground

- **WHEN** the filter is enabled, the target program is the foreground window, and the user presses a key bound to a skill
- **THEN** the skill SHALL be triggered as normal

#### Scenario: Filter disabled triggers everywhere

- **WHEN** the filter is disabled and the user presses a key bound to a skill
- **THEN** the skill SHALL be triggered regardless of the foreground window

#### Scenario: Capture mode ignores filter

- **WHEN** the filter is enabled and the user is assigning a hotkey in capture mode
- **THEN** the key SHALL be captured normally without any foreground-window check


<!-- @trace
source: sound-mute-and-window-scoped-hotkeys
updated: 2026-06-01
code:
  - .release_notes_v4.3.6.md
  - debug_chip.png
  - .release_notes_v4.3.5.md
-->

---
### Requirement: Target window selection via thumbnail picker

The system SHALL provide a picker that lists currently open top-level windows, each shown with a visual thumbnail of the window's content and its title, so the user can identify the target window visually. Selecting a window SHALL store that window's executable name as the hotkey filter target. The picker SHALL provide a refresh action to re-enumerate windows and re-capture thumbnails.

Thumbnails SHALL be captured using a per-window render that is independent of window stacking order, so the picker being frontmost does not obscure the captured content. For a minimized window whose content cannot be rendered, the picker SHALL fall back to showing the program icon and title.

#### Scenario: Select target from picker

- **WHEN** the user opens the picker, clicks a window card, and confirms
- **THEN** that window's executable name SHALL be stored as the filter target
- **THEN** the settings entry SHALL display the chosen window's title

#### Scenario: Minimized window fallback

- **WHEN** the picker lists a minimized window whose content cannot be captured
- **THEN** that window's card SHALL show the program icon and title instead of a content thumbnail

#### Scenario: Refresh re-captures windows

- **WHEN** the user clicks refresh in the picker
- **THEN** the window list and thumbnails SHALL be regenerated from the current desktop state

<!-- @trace
source: sound-mute-and-window-scoped-hotkeys
updated: 2026-06-01
code:
  - .release_notes_v4.3.6.md
  - debug_chip.png
  - .release_notes_v4.3.5.md
-->