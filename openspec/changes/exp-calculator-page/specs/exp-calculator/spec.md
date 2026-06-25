## ADDED Requirements

### Requirement: Classic EXP table data

The system SHALL provide `src/domain/exp_table.py` exposing a mapping `EXP_TO_NEXT` from character level L (1 through 199) to the EXP required to advance from L to L+1, using the classic pre-Big-Bang MapleStory values (the curve Artale uses). The module SHALL expose `MAX_LEVEL = 200`, and level 200 SHALL have no next-level entry. The table values SHALL match the canonical classic table.

#### Scenario: Known anchor values are present

- **WHEN** `EXP_TO_NEXT` is read
- **THEN** it contains entries for every level 1 through 199
- **AND** `EXP_TO_NEXT[1]` is 15, `EXP_TO_NEXT[2]` is 34, `EXP_TO_NEXT[3]` is 57, and `EXP_TO_NEXT[10]` is 1716

#### Scenario: Max level exposed and capped

- **WHEN** `MAX_LEVEL` is read
- **THEN** it is 200
- **AND** `EXP_TO_NEXT` has no entry for level 200

### Requirement: Compute remaining EXP to a target level

The system SHALL provide `exp_service.exp_remaining(level, pct, target)` returning the EXP still required to reach `target` from the current `level` at `pct` percent into the current level. When `target <= level` the result SHALL be 0. Otherwise the result SHALL be `round(EXP_TO_NEXT[level] * (1 - pct/100))` plus the sum of `EXP_TO_NEXT[L]` for L from `level+1` to `target-1`. `pct` SHALL be clamped to the range [0, 100] and `level`/`target` to [1, MAX_LEVEL]. Non-numeric inputs SHALL be coerced (level/target → 1, pct → 0) rather than raising.

#### Scenario: Remaining EXP across a partial level and a full level

- **WHEN** `exp_remaining(10, 50, 12)` is called
- **THEN** the result is 3218

##### Example: computation breakdown

- **GIVEN** `EXP_TO_NEXT[10]=1716`, `EXP_TO_NEXT[11]=2360`
- **WHEN** `exp_remaining(10, 50, 12)` is evaluated
- **THEN** remaining-in-current is `round(1716 * 0.5) = 858`
- **AND** full-levels is `EXP_TO_NEXT[11] = 2360`
- **AND** total is `858 + 2360 = 3218`

#### Scenario: Target at or below current level needs no EXP

- **WHEN** `exp_remaining(50, 0, 50)` is called
- **THEN** the result is 0

### Requirement: Compute remaining EXP within the current level

The system SHALL provide `exp_service.exp_remaining_in_level(level, pct)` returning the EXP still required to finish the current level, computed as `round(EXP_TO_NEXT[level] * (1 - pct/100))`. When the level has no next-level entry (e.g. level 200) the result SHALL be 0.

#### Scenario: Remaining-in-level for a partial level

- **WHEN** `exp_remaining_in_level(10, 50)` is called
- **THEN** the result is 858

#### Scenario: Capped level has no remaining-in-level

- **WHEN** `exp_remaining_in_level(200, 0)` is called
- **THEN** the result is 0

### Requirement: Derive hourly EXP rate from an interval sample

The system SHALL provide `exp_service.hourly_rate(exp_per_interval, minutes)` returning the per-hour EXP rate derived from an EXP amount earned over a given interval, computed as `exp_per_interval * 60 / minutes`. When `exp_per_interval <= 0`, `minutes <= 0`, or either input is non-numeric, the result SHALL be 0.

#### Scenario: Ten-minute sample scales to one hour

- **WHEN** `hourly_rate(10000, 10)` is called
- **THEN** the result is 60000

#### Scenario: One-hour sample is unchanged

- **WHEN** `hourly_rate(60000, 60)` is called
- **THEN** the result is 60000

#### Scenario: Zero EXP yields zero rate

- **WHEN** `hourly_rate(0, 10)` is called
- **THEN** the result is 0

### Requirement: Estimate time and format as HH:MM:SS

The system SHALL provide `exp_service.time_hours(total_exp, exp_per_hour)` returning `total_exp / exp_per_hour` (in hours) when `exp_per_hour > 0`, otherwise None. The system SHALL provide `exp_service.format_duration(hours)` returning the duration formatted as zero-padded `HH:MM:SS`, and returning `"—"` when given None.

#### Scenario: Time estimate from EXP per hour

- **WHEN** `time_hours(120000, 60000)` is called
- **THEN** the result is 2.0

#### Scenario: Zero rate yields no time estimate

- **WHEN** `time_hours(1000, 0)` is called
- **THEN** the result is None

#### Scenario: Hours format as HH:MM:SS

- **WHEN** `format_duration(1.5)` is called
- **THEN** the result is "01:30:00"

#### Scenario: No estimate renders as an em dash

- **WHEN** `format_duration(None)` is called
- **THEN** the result is "—"

### Requirement: EXP calculator page renders inputs and results

The system SHALL provide `src/ui_v2/pages/exp_calculator_page_v2.py` rendering an input area and a result area. The input area SHALL contain the current level, the current EXP percent, the target level, and a single training-rate input consisting of one EXP amount plus an interval dropdown offering `10 分鐘 / 30 分鐘 / 1 小時` (defaulting to 10 minutes); the per-hour rate is derived via `exp_service.hourly_rate`. The result area SHALL show exactly three outputs: total remaining EXP (`還需總經驗`), EXP remaining in the current level (`距下一級還需`), and the estimated time (`預估時間`, formatted HH:MM:SS). Results SHALL update whenever any input changes. The page SHALL follow V2Theme styling and use lucide icons via lucide_pixmap.

#### Scenario: Results update from inputs

- **WHEN** the user sets current level 10, current EXP 50 percent, target level 12, and enters 60000 EXP per the 1-小時 interval
- **THEN** the total remaining EXP shows 3,218
- **AND** the estimated time recomputes from the derived hourly rate

#### Scenario: Interval dropdown scales the entered EXP

- **WHEN** the user enters 10000 EXP and selects the 10-分鐘 interval
- **THEN** the derived per-hour rate used for the time estimate is 60000

### Requirement: Sidebar navigation entry for EXP calculator

The system SHALL register the EXP calculator page in the shared V2 page registry `src/ui_v2/page_registry.py` (the single source consumed by both `main_v2.py` and `src/ui_v2/sidebar_v2.py`), with key `exp` and a lucide icon loaded via lucide_pixmap. Selecting the entry SHALL switch the main view to the EXP calculator page.

#### Scenario: Navigate to the EXP calculator page

- **WHEN** the user clicks the EXP calculator entry in the sidebar
- **THEN** the main view switches to the EXP calculator page

### Requirement: EXP service and table remain free of Qt dependencies

`src/domain/exp_service.py` and `src/domain/exp_table.py` SHALL NOT import any PySide6/Qt module, so the calculation layer stays unit-verifiable without a GUI.

#### Scenario: Importing the service pulls in no Qt

- **WHEN** `src/domain/exp_service.py` is imported in a plain Python process
- **THEN** no PySide6 module is imported as a side effect

### Requirement: Calculator inputs are not persisted

The EXP calculator SHALL NOT persist its inputs. It SHALL NOT read from or write to `profiles/` or `config_user.json`. The page constructor accepts an `app` argument for signature parity with other pages but does not use it for state.

#### Scenario: Inputs reset on reopen

- **WHEN** the user enters values, navigates away, and returns to the EXP calculator page
- **THEN** no previously entered values are restored from disk
