## ADDED Requirements

### Requirement: V2 potion page quantity inputs use stack-based entry

Every quantity input on the V2 potion page — potion before/after counts and item-acquisition quantities — SHALL use a stack-based input control (`_StackQty`) shaped as `[組數] × [組大小▼] ＋ [餘數]`, where the resulting quantity is `組數 × 組大小 + 餘數`. The 組大小 (stack-size) dropdown SHALL offer exactly two choices: `3000` and `9900`. The default stack size SHALL be 3000 for potion rows and scroll-type item rows, and 9900 for general item rows. Setting a quantity from a stored total SHALL decompose it back into 組數 / 餘數 via integer division by the current stack size.

#### Scenario: Quantity computed from groups, stack size, and remainder

- **WHEN** a `_StackQty` has 組數 `2`, 組大小 `3000`, and 餘數 `150`
- **THEN** its quantity is 6150

#### Scenario: Stack-size dropdown offers only 3000 and 9900

- **WHEN** the user opens any 組大小 dropdown
- **THEN** the only selectable values are 3000 and 9900

### Requirement: V2 potion page provides item-acquisition income with map presets

The V2 potion page SHALL provide a "物品取得" income area on the income (right) side. The area SHALL render item rows whose shape is: a per-item icon (loaded from `images/item_icons/<item_id>.png`, falling back to a generic package badge when the icon file is missing or `item_id` is 0), an editable item-name field, an editable quantity field (a `_StackQty`), an editable unit-price field, a read-only per-row income equal to `quantity * unit_price`, and a delete control. The area SHALL provide a "新增道具" control that appends a blank editable row.

The area SHALL provide a training-map selector populated from `src/domain/training_maps.py` (each entry labelled with its level). Selecting a map SHALL first clear any existing item rows and then append one row per drop item of that map, prefilling the item name and item icon. The unit price SHALL be prefilled from the map data's preset unit price for that drop item when one exists, and SHALL default to 0 otherwise. The same drop item appearing in multiple maps SHALL prefill the identical preset price (price alignment keyed by item id). The map dropdown SHALL retain the chosen map after populating. A "清除全部" control SHALL clear all item rows and reset the map dropdown back to its placeholder. Rows appended from a preset SHALL be freely editable and deletable. Item rows SHALL feed `PotionService.calc_items_total` into the income summary.

#### Scenario: Add a manual item row

- **WHEN** the user clicks the 新增道具 control in the 物品取得 area
- **THEN** a new blank item row appears with editable name, quantity, and unit-price fields

#### Scenario: Select a training map clears then populates editable drop rows

- **WHEN** the user picks a map from the training-map selector
- **THEN** any pre-existing item rows are removed first
- **AND** one item row appears per drop item of that map, with the item name prefilled and the unit price set to that item's preset price (0 when the item has no preset)
- **AND** the map dropdown still shows the chosen map
- **AND** the user can edit or delete any appended row

#### Scenario: Drop items with a preset price prefill that price

- **WHEN** the user picks a map whose drops include items that have a preset unit price (e.g. 神木村 dragon-nest materials)
- **THEN** each such item's row prefills its unit price with the preset value rather than 0
- **AND** the same drop item selected from a different map prefills the identical preset price

#### Scenario: Clear all resets the item area and the map dropdown

- **WHEN** the user clicks 清除全部 in the 物品取得 area
- **THEN** all item rows are removed
- **AND** the map dropdown returns to its placeholder entry

#### Scenario: Item row income contributes to total income

- **WHEN** an item row has quantity 3 and unit price 1000
- **THEN** that row shows 3000 as its per-row income
- **AND** the summary income increases by 3000

## MODIFIED Requirements

### Requirement: V2 potion page lays out expense, income, and summary

The V2 potion page (`src/ui_v2/pages/potion_page_v2.py`) SHALL lay out the body as a top `QHBoxLayout` with expenses on the left and income on the right (each column independently scrollable), and a summary card spanning the full width below them. The left (expense) column SHALL hold three potion sections — HP, MP, combined — in that order, each starting empty. The right (income) column SHALL hold a 楓幣 ・ 商店 card (撿取楓幣 before/after row and 商店收益 before/after row) followed by the 物品取得 area. A toolbar above the body SHALL provide 清除 / 全部重置 / 載入紀錄 / 儲存 actions and the page title (收支-oriented, e.g. 「練功收支」).

The page SHALL NOT render any experience input. The page SHALL NOT render any practice-time / timer / duration input, and SHALL NOT show any hourly or per-interval rate. The page SHALL NOT auto-populate any potion or item rows from any catalog at construction time, and SHALL NOT hold a hardcoded demo list. Potion rows are added by the user via each section's 「＋ 新增藥水…」 dropdown (drawn from `PotionService.DEFAULTS`) or restored from autosave / saved records; item rows are added manually, via a map preset, or restored.

#### Scenario: Page initialization shows empty expense and income sides

- **WHEN** `PotionPageV2` is instantiated and no autosave file exists
- **THEN** the HP, MP, and combined potion sections each contain zero rows
- **AND** the 物品取得 area contains zero rows
- **AND** the page renders no experience input field
- **AND** the page renders no time / timer / duration input field
- **AND** the bottom summary shows zeros for all metrics

### Requirement: V2 potion page recomputes summary on every input change

The V2 page SHALL update the bottom summary card whenever any input field changes, routing every change through a single `_on_input_changed` entry point that recomputes and schedules a debounced autosave. The summary metrics SHALL be computed by `PotionService.calc_summary` using a form dict assembled from current widget values. The displayed metrics SHALL be exactly three: 總支出 (expense, shown with a leading `-`), 總收入 (income, shown with a leading `+`), and 淨收益 (net, shown signed). The page SHALL NOT display any experience metric and SHALL NOT display any hourly / per-interval rate metric.

#### Scenario: Editing a potion row updates summary

- **WHEN** the user edits the `after` count of any potion row
- **THEN** the summary 總支出 line updates within the same event loop turn
- **AND** the 淨收益 line updates to `income - expense`

#### Scenario: Editing an item row updates income

- **WHEN** the user edits the quantity or unit price of an item row
- **THEN** the summary 總收入 line recomputes to include the item-rows total

#### Scenario: Mesos and shop before/after contribute only non-negative gains

- **WHEN** a 撿取楓幣 or 商店收益 row has its 後 value below its 前 value
- **THEN** that row's read-only gain shows `+0`
- **AND** the summary 總收入 is not reduced by that row
