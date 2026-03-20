## ADDED Requirements

### Requirement: Cooldown Trigger via Hotkey

When a skill's hotkey is pressed, the system SHALL start a cooldown countdown for that skill.
The hotkey listener runs in a daemon thread and MUST dispatch the trigger to the main thread via `_Dispatcher.schedule()` before performing any UI operation.

#### Scenario: First press starts countdown

- **WHEN** user presses a skill's assigned hotkey and no cooldown window is active for that skill
- **THEN** system creates a SkillWindow with the skill's effective cooldown duration and starts the countdown

#### Scenario: Press during active cooldown (normal skill)

- **WHEN** user presses a skill's hotkey while a cooldown window is already active and the skill is neither permanent nor loop
- **THEN** system closes the active window without restarting the countdown

#### Scenario: Press during active cooldown (permanent or loop skill)

- **WHEN** user presses a skill's hotkey while a cooldown window is already active and the skill is permanent or loop
- **THEN** system restarts the countdown from the full cooldown duration


<!-- @trace
source: skill-cooldown-spec
updated: 2026-03-19
code:
  - CLAUDE.md
  - docs/PROJECT.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - docs/RELEASE.md
-->

### Requirement: Countdown Timer Accuracy

The cooldown countdown SHALL use `time.perf_counter()` to measure elapsed time and SHALL NOT rely solely on QTimer tick counts to determine remaining time.

#### Scenario: Timer tick updates display

- **WHEN** QTimer fires (every 100ms, or 50ms when remaining < 1 second)
- **THEN** system calculates `remaining = end_time - perf_counter()` and updates the display

#### Scenario: Fast-second phase switches interval

- **WHEN** remaining time drops below 1 second
- **THEN** QTimer interval switches from 100ms to 50ms for smoother display


<!-- @trace
source: skill-cooldown-spec
updated: 2026-03-19
code:
  - CLAUDE.md
  - docs/PROJECT.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - docs/RELEASE.md
-->

### Requirement: Skill States

Each skill SHALL independently support the following states: idle, active-cooldown, permanent, loop, and alert-enabled.
States permanent, loop, and alert-enabled are boolean flags stored in `App` instance dictionaries keyed by `skill_id`.

#### Scenario: Permanent skill keeps window after cooldown ends

- **WHEN** cooldown reaches zero and the skill is permanent
- **THEN** system resets the overlay to idle state and keeps the SkillWindow open

#### Scenario: Loop skill auto-restarts cooldown

- **WHEN** cooldown reaches zero and the skill is loop
- **THEN** system restarts the countdown after a random delay between 50ms and 500ms

#### Scenario: Normal skill closes after cooldown ends

- **WHEN** cooldown reaches zero and the skill is neither permanent nor loop
- **THEN** system closes the SkillWindow after a 2-second delay


<!-- @trace
source: skill-cooldown-spec
updated: 2026-03-19
code:
  - CLAUDE.md
  - docs/PROJECT.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - docs/RELEASE.md
-->

### Requirement: Cooldown Duration Override

Users SHALL be able to override the base cooldown duration for any skill on a per-profile basis.
Overrides MUST be stored in `profiles/{name}.json` under `cooldown_overrides` and MUST NOT modify `config.json` skills/items data.

#### Scenario: Override applied when window is created

- **WHEN** a cooldown window is created for a skill that has an active cooldown override in the current profile
- **THEN** the window SHALL use the override duration instead of the base duration from `config.json`

#### Scenario: Override reset restores base duration

- **WHEN** user resets a skill's cooldown override
- **THEN** system removes the entry from `cooldown_overrides` and subsequent windows use the base duration


<!-- @trace
source: skill-cooldown-spec
updated: 2026-03-19
code:
  - CLAUDE.md
  - docs/PROJECT.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - docs/RELEASE.md
-->

### Requirement: Alert System

When alert is enabled for a skill, the system SHALL trigger a visual flash and optional sound effect when the remaining cooldown reaches the configured alert threshold.
The alert MUST fire at most once per cooldown cycle.

#### Scenario: Alert fires at threshold

- **WHEN** remaining time drops to or below `alert_before_seconds` for a skill with `alert_enabled = true`
- **THEN** system flashes the SkillWindow border (6 flashes at 120ms interval) and plays the configured alert sound if sound is enabled

#### Scenario: Alert does not repeat

- **WHEN** the alert has already fired in the current cooldown cycle
- **THEN** system MUST NOT trigger the alert again even if the timer continues ticking

#### Scenario: Per-skill alert seconds override

- **WHEN** a skill has an entry in `alert_seconds_overrides` in the current profile
- **THEN** that value SHALL be used as the alert threshold instead of the global `alert_before_seconds`


<!-- @trace
source: skill-cooldown-spec
updated: 2026-03-19
code:
  - CLAUDE.md
  - docs/PROJECT.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - docs/RELEASE.md
-->

### Requirement: Overlay Progress Visualization

The SkillWindow SHALL display a gray overlay mask that covers the skill icon proportionally to the **elapsed** cooldown fraction (`elapsed / total`), filling from bottom upward.
At cooldown start the mask is absent (0%); at cooldown end the mask is full (100%), signalling completion.

#### Scenario: Overlay at start of cooldown

- **WHEN** cooldown starts
- **THEN** overlay mask has 0% coverage (icon fully visible)

#### Scenario: Overlay during countdown

- **WHEN** cooldown has elapsed fraction `f = elapsed / total`
- **THEN** overlay mask covers `f * window_size` pixels from the bottom of the icon

#### Scenario: Overlay at end of cooldown

- **WHEN** cooldown reaches zero
- **THEN** overlay mask covers the full icon height (100% coverage), then the window closes or resets

## Requirements


<!-- @trace
source: skill-cooldown-spec
updated: 2026-03-19
code:
  - CLAUDE.md
  - docs/PROJECT.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - docs/RELEASE.md
-->

### Requirement: Cooldown Trigger via Hotkey

When a skill's hotkey is pressed, the system SHALL start a cooldown countdown for that skill.
The hotkey listener runs in a daemon thread and MUST dispatch the trigger to the main thread via `_Dispatcher.schedule()` before performing any UI operation.

#### Scenario: First press starts countdown

- **WHEN** user presses a skill's assigned hotkey and no cooldown window is active for that skill
- **THEN** system creates a SkillWindow with the skill's effective cooldown duration and starts the countdown

#### Scenario: Press during active cooldown (normal skill)

- **WHEN** user presses a skill's hotkey while a cooldown window is already active and the skill is neither permanent nor loop
- **THEN** system closes the active window without restarting the countdown

#### Scenario: Press during active cooldown (permanent or loop skill)

- **WHEN** user presses a skill's hotkey while a cooldown window is already active and the skill is permanent or loop
- **THEN** system restarts the countdown from the full cooldown duration

---
### Requirement: Countdown Timer Accuracy

The cooldown countdown SHALL use `time.perf_counter()` to measure elapsed time and SHALL NOT rely solely on QTimer tick counts to determine remaining time.

#### Scenario: Timer tick updates display

- **WHEN** QTimer fires (every 100ms, or 50ms when remaining < 1 second)
- **THEN** system calculates `remaining = end_time - perf_counter()` and updates the display

#### Scenario: Fast-second phase switches interval

- **WHEN** remaining time drops below 1 second
- **THEN** QTimer interval switches from 100ms to 50ms for smoother display

---
### Requirement: Skill States

Each skill SHALL independently support the following states: idle, active-cooldown, permanent, loop, and alert-enabled.
States permanent, loop, and alert-enabled are boolean flags stored in `App` instance dictionaries keyed by `skill_id`.

#### Scenario: Permanent skill keeps window after cooldown ends

- **WHEN** cooldown reaches zero and the skill is permanent
- **THEN** system resets the overlay to idle state and keeps the SkillWindow open

#### Scenario: Loop skill auto-restarts cooldown

- **WHEN** cooldown reaches zero and the skill is loop
- **THEN** system restarts the countdown after a random delay between 50ms and 500ms

#### Scenario: Normal skill closes after cooldown ends

- **WHEN** cooldown reaches zero and the skill is neither permanent nor loop
- **THEN** system closes the SkillWindow after a 2-second delay

---
### Requirement: Cooldown Duration Override

Users SHALL be able to override the base cooldown duration for any skill on a per-profile basis.
Overrides MUST be stored in `profiles/{name}.json` under `cooldown_overrides` and MUST NOT modify `config.json` skills/items data.

#### Scenario: Override applied when window is created

- **WHEN** a cooldown window is created for a skill that has an active cooldown override in the current profile
- **THEN** the window SHALL use the override duration instead of the base duration from `config.json`

#### Scenario: Override reset restores base duration

- **WHEN** user resets a skill's cooldown override
- **THEN** system removes the entry from `cooldown_overrides` and subsequent windows use the base duration

---
### Requirement: Alert System

When alert is enabled for a skill, the system SHALL trigger a visual flash and optional sound effect when the remaining cooldown reaches the configured alert threshold.
The alert MUST fire at most once per cooldown cycle.

#### Scenario: Alert fires at threshold

- **WHEN** remaining time drops to or below `alert_before_seconds` for a skill with `alert_enabled = true`
- **THEN** system flashes the SkillWindow border (6 flashes at 120ms interval) and plays the configured alert sound if sound is enabled

#### Scenario: Alert does not repeat

- **WHEN** the alert has already fired in the current cooldown cycle
- **THEN** system MUST NOT trigger the alert again even if the timer continues ticking

#### Scenario: Per-skill alert seconds override

- **WHEN** a skill has an entry in `alert_seconds_overrides` in the current profile
- **THEN** that value SHALL be used as the alert threshold instead of the global `alert_before_seconds`

---
### Requirement: Overlay Progress Visualization

The SkillWindow SHALL display a gray overlay mask that covers the skill icon proportionally to the **elapsed** cooldown fraction (`elapsed / total`), filling from bottom upward.
At cooldown start the mask is absent (0%); at cooldown end the mask is full (100%), signalling completion.

#### Scenario: Overlay at start of cooldown

- **WHEN** cooldown starts
- **THEN** overlay mask has 0% coverage (icon fully visible)

#### Scenario: Overlay during countdown

- **WHEN** cooldown has elapsed fraction `f = elapsed / total`
- **THEN** overlay mask covers `f * window_size` pixels from the bottom of the icon

#### Scenario: Overlay at end of cooldown

- **WHEN** cooldown reaches zero
- **THEN** overlay mask covers the full icon height (100% coverage), then the window closes or resets