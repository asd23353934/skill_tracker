# monster-respawn-timer Specification

## Purpose

TBD - created by archiving change 'monster-respawn-timer'. Update Purpose after archive.

## Requirements

### Requirement: Timer is triggered by hotkey

Pressing a key bound to a monster SHALL call `WindowManager.trigger_monster(monster_id)`.
If the monster already has an active timer window, the trigger SHALL be ignored (no duplicate windows).

#### Scenario: Hotkey triggers timer

- **WHEN** the user presses a key bound to monster "鱷魚怪"
- **THEN** `WindowManager.trigger_monster("鱷魚怪_id")` SHALL be called via `app.after(0, ...)`
- **THEN** a floating timer window SHALL appear

#### Scenario: Duplicate trigger is ignored

- **WHEN** monster "鱷魚怪" already has an active timer window
- **THEN** pressing its hotkey again SHALL NOT create a second window


<!-- @trace
source: monster-respawn-timer
updated: 2026-03-20
code:
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - CLAUDE.md
  - docs/RELEASE.md
  - src/ui/skill_manager.py
  - config.json
  - src/ui/app.py
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
-->

---
### Requirement: Timer counts upward from zero

The monster respawn timer SHALL count from `0` upward toward `respawn_time` (in seconds).
This is opposite to the skill cooldown direction (which counts down).

#### Scenario: Timer direction is forward

- **WHEN** a monster timer starts with `respawn_time = 60`
- **THEN** the displayed elapsed time SHALL increase from 0 toward 60
- **THEN** the timer SHALL complete when elapsed time reaches 60 seconds


<!-- @trace
source: monster-respawn-timer
updated: 2026-03-20
code:
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - CLAUDE.md
  - docs/RELEASE.md
  - src/ui/skill_manager.py
  - config.json
  - src/ui/app.py
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
-->

---
### Requirement: loop mode auto-restarts the timer

When `monster.loop` is `True`, the timer SHALL automatically restart from 0
immediately after reaching `respawn_time`, without user intervention.

When `monster.loop` is `False`, the timer SHALL stop and the window SHALL close after completion.

#### Scenario: Loop restarts automatically

- **WHEN** a monster with `loop: true` reaches its `respawn_time`
- **THEN** the timer SHALL reset to 0 and begin counting again
- **THEN** the window SHALL remain open

#### Scenario: Non-loop closes on completion

- **WHEN** a monster with `loop: false` reaches its `respawn_time`
- **THEN** the timer window SHALL close


<!-- @trace
source: monster-respawn-timer
updated: 2026-03-20
code:
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - CLAUDE.md
  - docs/RELEASE.md
  - src/ui/skill_manager.py
  - config.json
  - src/ui/app.py
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
-->

---
### Requirement: permanent mode creates always-on window

When `monster.permanent` is `True`, `WindowManager.create_permanent_monster_window(monster_id)`
SHALL be called on application startup with `idle_start=True`, creating a window in idle state.
After the timer completes, the window SHALL NOT close — it SHALL reset to idle state instead.

When `monster.permanent` is `False`, the window is created only when triggered by hotkey.

#### Scenario: Permanent window exists on startup

- **WHEN** a monster has `permanent: true`
- **THEN** its timer window SHALL exist on application startup (idle state, not counting)

#### Scenario: Permanent window resets after completion

- **WHEN** a permanent monster timer reaches `respawn_time`
- **THEN** the window SHALL reset to idle state (not close)
- **THEN** the user can re-trigger by pressing the hotkey


<!-- @trace
source: monster-respawn-timer
updated: 2026-03-20
code:
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - CLAUDE.md
  - docs/RELEASE.md
  - src/ui/skill_manager.py
  - config.json
  - src/ui/app.py
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
-->

---
### Requirement: alert_before triggers advance sound

When `monster.alert_before > 0`, the system SHALL play `monster.alert_sound`
once when the elapsed time first reaches `respawn_time - alert_before` seconds.
The alert sound SHALL NOT repeat within the same timer cycle.

When `monster.alert_before == 0`, no advance alert SHALL be triggered.

#### Scenario: Alert plays at correct time

- **WHEN** a monster has `respawn_time: 60` and `alert_before: 10`
- **THEN** `alert_sound` SHALL be played once when elapsed time reaches 50 seconds
- **THEN** the alert SHALL NOT play again during the same cycle

#### Scenario: Zero alert_before disables alert

- **WHEN** `monster.alert_before == 0`
- **THEN** no advance alert sound SHALL be played during the timer


<!-- @trace
source: monster-respawn-timer
updated: 2026-03-20
code:
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - CLAUDE.md
  - docs/RELEASE.md
  - src/ui/skill_manager.py
  - config.json
  - src/ui/app.py
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
-->

---
### Requirement: End sound plays on timer completion

When `monster.sound` is set and the timer reaches `respawn_time`,
the system SHALL play `monster.sound` once.

#### Scenario: End sound plays on completion

- **WHEN** a monster timer reaches `respawn_time` and `monster.sound` is non-empty
- **THEN** `SoundManager.play(monster.sound)` SHALL be called once


<!-- @trace
source: monster-respawn-timer
updated: 2026-03-20
code:
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - CLAUDE.md
  - docs/RELEASE.md
  - src/ui/skill_manager.py
  - config.json
  - src/ui/app.py
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
-->

---
### Requirement: Respawn time is editable and resettable

The user SHALL be able to modify `monster.respawn_time` via the card UI.
The original respawn time (from `config.json` at startup) SHALL be preserved in
`ConfigManager.initial_monsters` for reset purposes.

#### Scenario: Edit respawn time

- **WHEN** the user clicks the respawn time button and enters a new value
- **THEN** `monster.respawn_time` SHALL be updated and persisted via `app.save_monsters()`

#### Scenario: Reset respawn time

- **WHEN** the user clicks the reset button
- **THEN** `monster.respawn_time` SHALL revert to the original value from `ConfigManager.initial_monsters`
- **THEN** the change SHALL be persisted via `app.save_monsters()`

<!-- @trace
source: monster-respawn-timer
updated: 2026-03-20
code:
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - CLAUDE.md
  - docs/RELEASE.md
  - src/ui/skill_manager.py
  - config.json
  - src/ui/app.py
  - docs/PROJECT.md
  - docs/CODE_STYLE.md
-->