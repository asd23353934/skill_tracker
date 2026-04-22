## ADDED Requirements

### Requirement: V2 potion page starts with empty sections

The V2 potion page (`src/ui_v2/pages/potion_page_v2.py`) SHALL start with three empty sections (HP, MP, combined) at page construction time — the page SHALL NOT auto-populate any rows from `PotionService.DEFAULTS` or any other catalog. The page SHALL NOT hold its own hardcoded demo potion list. Section display order SHALL be: HP potions first, MP potions second, combined potions last. Rows are added only by the user via each section add-potion button or restored from autosave / saved records.

#### Scenario: Page initialization shows three empty sections

- **WHEN** `PotionPageV2` is instantiated and no autosave file exists
- **THEN** the HP section contains zero rows
- **AND** the MP section contains zero rows
- **AND** the combined section contains zero rows
- **AND** the summary card shows zeros for all metrics

### Requirement: V2 potion page recomputes summary on every input change

The V2 page SHALL update the right-side summary card whenever any input field changes. The eight summary metrics SHALL be computed by `PotionService.calc_summary` using a form dict assembled from current widget values. The eight displayed metrics SHALL include: income, expense, net, exp_total, net_10, exp_10, net_60, exp_60.

#### Scenario: Editing a potion row updates summary

- **WHEN** the user edits the `after` count of any potion row
- **THEN** the summary card expense line updates within the same event loop turn
- **AND** the net line updates to `income - expense`

#### Scenario: Editing duration updates hourly rates

- **WHEN** the user changes the duration (minutes) input
- **THEN** the summary card net_60 and exp_60 lines recompute using `PotionService.calc_summary`

##### Example: per-10-minute projection

- **GIVEN** a form with mesos_start=10000, mesos_end=50000, duration_minutes=30, no other income/expense, no potions
- **WHEN** the user changes duration_minutes from 30 to 20
- **THEN** net_10 displays as 20000 (computed as int(40000 / 20 * 10))

### Requirement: V2 potion page writes autosave with 500ms debounce

The V2 page SHALL schedule an autosave 500ms after the most recent input change, collapsing rapid successive edits into a single write. The autosave SHALL call `PotionService.save_autosave(form, timer_elapsed=<seconds>)`. The autosave file schema SHALL remain identical to the V1 schema so that V1 and V2 pages can read each other autosave output.

#### Scenario: Rapid edits coalesce into one write

- **WHEN** the user types five characters into a potion row within 200ms
- **THEN** exactly one autosave write occurs 500ms after the last keystroke

#### Scenario: V1 can read V2 autosave

- **WHEN** V2 writes autosave and V1 is subsequently opened
- **THEN** V1 existing autosave-restore path reads the file and restores all fields including `_timer_elapsed`

### Requirement: V2 potion page restores autosave on load

When `PotionPageV2` is constructed, it SHALL call `PotionService.load_autosave()` and, if a record is returned, restore all form fields (potion rows, mesos, shop, exp, duration) and set `_timer_elapsed` from the record `_timer_elapsed` key. The timer SHALL NOT auto-resume — the user must click start to continue counting.

#### Scenario: Autosave present on page load

- **WHEN** the user opens the V2 potion page and an autosave file exists with duration_minutes=45 and _timer_elapsed=2700
- **THEN** the duration input shows 45 and the timer display shows 00:45:00
- **AND** the timer is paused (not counting)

#### Scenario: No autosave present

- **WHEN** the user opens the V2 potion page and no autosave file exists
- **THEN** the page shows three empty potion sections with zero in all numeric fields

### Requirement: V2 potion page supports row add, delete, and section clear

The V2 page SHALL provide per-section add-potion and clear-all buttons, and per-row delete buttons. Adding creates an empty row (name empty string, price 0, before 0, after 0) appended to the section. Deleting removes exactly the target row. Clear-all removes every row in that section. All three operations SHALL trigger the same recalc plus autosave pipeline as input changes.

#### Scenario: Adding a row triggers autosave

- **WHEN** the user clicks add-potion in the HP section
- **THEN** an empty row is appended to the HP section
- **AND** the summary recomputes
- **AND** an autosave is scheduled within 500ms

#### Scenario: Clearing a section does not affect other sections

- **WHEN** the user clicks clear-all in the MP section
- **THEN** all MP rows are removed
- **AND** HP and combined sections remain unchanged

### Requirement: V2 potion page provides save and load record dialogs

The V2 page SHALL provide save-record and load-record buttons that open V2-styled dialogs (`PotionSaveDialogV2`, `PotionLoadDialogV2`) inheriting `BaseDialogV2`. Save SHALL serialize the form via `PotionService.serialize(form)` (including `saved_at` timestamp). Load SHALL deserialize via `PotionService.deserialize(data)` and apply the result to the form fields.

#### Scenario: Save writes a named record

- **WHEN** the user clicks save-record, enters a record name, and confirms
- **THEN** the record is written via `ConfigManager.save_potion_record(name, serialized_dict)`
- **AND** the serialized dict contains `saved_at` as an ISO-8601 string

#### Scenario: Load restores form fields

- **WHEN** the user selects an existing record in the load dialog and confirms
- **THEN** all form fields (rows, mesos, shop, exp, duration) are replaced with the record values
- **AND** the summary recomputes

### Requirement: V2 potion page supports manual and timer duration modes

The V2 page SHALL provide a manual-versus-timer toggle. In manual mode, the duration QSpinBox is editable and no tick is emitted. In timer mode, the duration QSpinBox is read-only and two dedicated controls appear next to the mode chips: a start/stop toggle button and a reset button. Switching to timer mode SHALL NOT automatically start the 1-second QTimer — the user must click start. When running, the QTimer increments `_timer_elapsed` every second and every 60 seconds syncs `_timer_elapsed // 60` into the duration QSpinBox. Toggling modes SHALL NOT reset `_timer_elapsed`. Clicking the reset button SHALL stop the QTimer and reset `_timer_elapsed` to 0 (it does NOT touch potion / mesos / exp inputs). The start/stop button SHALL render "開始" with a play icon when idle and "停止" with a stop icon when running. The start/reset controls SHALL be hidden in manual mode.

#### Scenario: Switching to timer mode does not auto-start

- **WHEN** the user switches from manual to timer mode
- **THEN** the start and reset buttons become visible
- **AND** the 1-second QTimer is NOT running
- **AND** `_timer_elapsed` retains its previous value

#### Scenario: Timer mode increments seconds after start

- **WHEN** the user is in timer mode and clicks start
- **THEN** `_timer_elapsed` increments by 1 every second
- **AND** the timer display (HH:MM:SS) updates every tick
- **AND** the start button label shows "停止"

#### Scenario: Timer mode syncs minutes once per 60 ticks

- **WHEN** `_timer_elapsed` reaches 60 seconds while the timer is running
- **THEN** the duration QSpinBox value updates to 1
- **AND** the summary hourly rates recompute using the new duration

#### Scenario: Reset clears accumulated seconds only

- **WHEN** the user is in timer mode with `_timer_elapsed` > 0 and clicks reset
- **THEN** the 1-second QTimer stops if it was running
- **AND** `_timer_elapsed` becomes 0
- **AND** the timer display shows 00:00:00
- **AND** all potion, mesos, shop, and exp inputs remain unchanged

### Requirement: V2 potion page clear and reset actions purge state

The V2 page SHALL provide two top-bar actions. The clear action SHALL reset all numeric inputs to 0 and remove all potion rows, but SHALL NOT delete the autosave file. The reset-all action SHALL perform everything clear does PLUS call `PotionService.clear_autosave()` to delete the autosave file PLUS reset `_timer_elapsed` to 0. Both actions SHALL show a confirmation dialog before applying.

#### Scenario: Clear keeps autosave

- **WHEN** the user confirms clear
- **THEN** all rows and numeric fields are reset
- **AND** `potion_autosave.json` still exists on disk unchanged

#### Scenario: Reset deletes autosave

- **WHEN** the user confirms reset-all
- **THEN** all rows and numeric fields are reset
- **AND** `_timer_elapsed` is 0
- **AND** `potion_autosave.json` does not exist on disk
