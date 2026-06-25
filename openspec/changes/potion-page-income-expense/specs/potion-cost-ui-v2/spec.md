## ADDED Requirements

### Requirement: V2 potion page provides item-acquisition income with map presets

The V2 potion page SHALL provide an "物品取得" income area on the income (right) side. The area SHALL render item rows whose shape is: an editable item-name field, an editable quantity field, an editable unit-price field, a read-only per-row income equal to `quantity * unit_price`, and a delete control. The area SHALL provide an add control that appends a blank editable row. The area SHALL provide a training-map selector populated from `src/domain/training_maps.py`; selecting a map SHALL append one row per drop item of that map, prefilling the item name and its known shop price (defaulting the unit price to 0 when unknown). Rows appended from a preset SHALL be freely editable and deletable. Item rows SHALL feed `PotionService.calc_items_total` into the income summary.

#### Scenario: Add a manual item row

- **WHEN** the user clicks the add control in the 物品取得 area
- **THEN** a new blank item row appears with editable name, quantity, and unit-price fields

#### Scenario: Select a training map populates editable drop rows

- **WHEN** the user picks a map from the training-map selector
- **THEN** one item row appears per drop item of that map, with the item name prefilled
- **AND** each row's unit price is the map's known shop price or 0 when unknown
- **AND** the user can edit or delete any appended row

#### Scenario: Item row income contributes to total income

- **WHEN** an item row has quantity 3 and unit price 1000
- **THEN** that row shows 3000 as its per-row income
- **AND** the summary income increases by 3000

## MODIFIED Requirements

### Requirement: V2 potion page starts with empty sections

The V2 potion page (`src/ui_v2/pages/potion_page_v2.py`) SHALL lay out expenses on the left and income on the right, with a summary spanning the bottom. The left (expense) side SHALL hold three empty potion sections (HP, MP, combined) in that order. The right (income) side SHALL hold the mesos before/after row, the shop before/after row, and an empty 物品取得 area. The page SHALL NOT auto-populate any potion or item rows from any catalog at construction time, and SHALL NOT hold a hardcoded demo list. The page SHALL NOT render any experience input. Rows are added only by the user or restored from autosave / saved records.

#### Scenario: Page initialization shows empty expense and income sides

- **WHEN** `PotionPageV2` is instantiated and no autosave file exists
- **THEN** the HP, MP, and combined potion sections each contain zero rows
- **AND** the 物品取得 area contains zero rows
- **AND** the page renders no experience input field
- **AND** the bottom summary shows zeros for all metrics

### Requirement: V2 potion page recomputes summary on every input change

The V2 page SHALL update the bottom summary card whenever any input field changes. The summary metrics SHALL be computed by `PotionService.calc_summary` using a form dict assembled from current widget values. The displayed metrics SHALL be exactly: income, expense, net, net_10, net_60. The page SHALL NOT display any experience metric.

#### Scenario: Editing a potion row updates summary

- **WHEN** the user edits the `after` count of any potion row
- **THEN** the summary expense line updates within the same event loop turn
- **AND** the net line updates to `income - expense`

#### Scenario: Editing an item row updates income

- **WHEN** the user edits the quantity or unit price of an item row
- **THEN** the summary income line recomputes to include the item rows total

#### Scenario: Editing duration updates hourly rate

- **WHEN** the user changes the duration (minutes) input
- **THEN** the summary net_60 line recomputes using `PotionService.calc_summary`

##### Example: per-10-minute projection

- **GIVEN** a form with mesos_start=10000, mesos_end=50000, duration_minutes=30, no other income/expense, no potions, no items
- **WHEN** the user changes duration_minutes from 30 to 20
- **THEN** net_10 displays as 20000 (computed as int(40000 / 20 * 10))
