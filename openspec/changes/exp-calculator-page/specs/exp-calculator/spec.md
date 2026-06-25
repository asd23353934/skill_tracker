## ADDED Requirements

### Requirement: Classic EXP table data

The system SHALL provide `src/domain/exp_table.py` exposing a mapping `EXP_TO_NEXT` from character level L (1 through 199) to the EXP required to advance from L to L+1, using the classic pre-Big-Bang MapleStory values (the curve Artale uses). Level 200 SHALL have no next-level entry. The table values SHALL match the canonical classic table.

#### Scenario: Known anchor values are present

- **WHEN** `EXP_TO_NEXT` is read
- **THEN** it contains entries for every level 1 through 199
- **AND** `EXP_TO_NEXT[1]` is 15, `EXP_TO_NEXT[2]` is 34, `EXP_TO_NEXT[3]` is 57, and `EXP_TO_NEXT[10]` is 1716

### Requirement: Compute remaining EXP to a target level

The system SHALL provide `exp_service.exp_remaining(level, pct, target)` returning the EXP still required to reach `target` from the current `level` at `pct` percent into the current level. When `target <= level` the result SHALL be 0. Otherwise the result SHALL be `round(EXP_TO_NEXT[level] * (1 - pct/100))` plus the sum of `EXP_TO_NEXT[L]` for L from `level+1` to `target-1`. `pct` SHALL be clamped to the range [0, 100) and `level`/`target` to [1, 200].

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

### Requirement: Compute kills needed and estimated time

The system SHALL provide service functions that, given the total remaining EXP, an optional `exp_per_kill`, and an `exp_per_hour`, return the kills needed and the estimated time. `kills_needed` SHALL be `ceil(total / exp_per_kill)` when `exp_per_kill > 0`, otherwise None. `time_hours` SHALL be `total / exp_per_hour` when `exp_per_hour > 0`, otherwise None. A None time SHALL be presentable as "—".

#### Scenario: Kills needed rounds up

- **WHEN** total remaining is 3218 and `exp_per_kill` is 100
- **THEN** `kills_needed` is 33

#### Scenario: Time estimate from EXP per hour

- **WHEN** total remaining is 120000 and `exp_per_hour` is 60000
- **THEN** `time_hours` is 2.0

#### Scenario: Zero rate yields no time estimate

- **WHEN** `exp_per_hour` is 0
- **THEN** `time_hours` is None

### Requirement: EXP calculator page renders inputs and results

The system SHALL provide `src/ui_v2/pages/exp_calculator_page_v2.py` rendering an input area (current level, current EXP percent, target level, and an EXP-rate source) and a result area (total remaining EXP, EXP remaining in the current level, kills needed, estimated time). The EXP-rate source SHALL support two modes: a direct EXP-per-hour value, or an EXP-per-kill value combined with kills-per-hour (from which EXP-per-hour is derived as their product). Results SHALL update when inputs change. The page SHALL follow V2Theme styling and use lucide icons via lucide_pixmap.

#### Scenario: Results update from inputs

- **WHEN** the user sets current level 10, current EXP 50 percent, target level 12, and EXP-per-hour 60000
- **THEN** the total remaining EXP shows 3218
- **AND** the estimated time recomputes from the entered rate

#### Scenario: Per-kill rate mode derives EXP per hour

- **WHEN** the user selects the per-kill mode with EXP-per-kill 200 and kills-per-hour 300
- **THEN** the derived EXP-per-hour used for the time estimate is 60000

### Requirement: Sidebar navigation entry for EXP calculator

The system SHALL add a navigation entry for the EXP calculator page to the V2 sidebar and the `main_v2.py` PAGES registry, using a lucide icon loaded via lucide_pixmap. Selecting the entry SHALL switch the main view to the EXP calculator page.

#### Scenario: Navigate to the EXP calculator page

- **WHEN** the user clicks the EXP calculator entry in the sidebar
- **THEN** the main view switches to the EXP calculator page

### Requirement: EXP service and table remain free of Qt dependencies

`src/domain/exp_service.py` and `src/domain/exp_table.py` SHALL NOT import any PySide6/Qt module, so the calculation layer stays unit-verifiable without a GUI.

#### Scenario: Importing the service pulls in no Qt

- **WHEN** `src/domain/exp_service.py` is imported in a plain Python process
- **THEN** no PySide6 module is imported as a side effect
