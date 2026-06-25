## ADDED Requirements

### Requirement: PotionService computes item-acquisition income total

The system SHALL provide `PotionService.calc_items_total(rows)` that returns the summed value of item-acquisition (收入「物品取得」) rows. For each row, if the row carries a pre-computed `value`, that value SHALL be used (clamped to a non-negative int); otherwise the row contributes `max(0, qty) * max(0, unit_price)`. Missing or non-numeric `qty` / `unit_price` / `value` SHALL be treated as zero. An empty or missing list SHALL return 0.

#### Scenario: Sum item rows

- **WHEN** `calc_items_total` is called with rows `[{qty: 3, unit_price: 1000}, {qty: 5, unit_price: 200}]`
- **THEN** the result is 4000

#### Scenario: Pre-computed value fast-path

- **WHEN** `calc_items_total` is called with rows `[{value: 777, qty: 1, unit_price: 1}]`
- **THEN** the result is 777 (the `value` field takes precedence over `qty * unit_price`)

##### Example: guards and empties

| Rows | Result | Notes |
| ---- | ------ | ----- |
| [] | 0 | empty list |
| [{qty: 2, unit_price: -50}] | 0 | negative price clamped |
| [{qty: 0, unit_price: 999}] | 0 | zero quantity |
| [{name: "緞帶", qty: 4, unit_price: 25}] | 100 | name ignored in math |

## MODIFIED Requirements

### Requirement: PotionService computes summary

The system SHALL provide `PotionService.calc_summary(form)` that returns a dict with EXACTLY the following three keys, computed from a `PotionFormData`:

- `income`: `max(0, mesos_end - mesos_start) + max(0, shop_after - shop_before) + calc_items_total(item_rows)`
- `expense`: sum of `calc_section_subtotal` over `hp_potions + mp_potions + combined_potions`
- `net`: `income - expense`

The summary SHALL NOT include any experience metric and SHALL NOT include any time-based / hourly-rate metric (no `net_10`, no `net_60`, no division by duration). All inputs SHALL be coerced to non-negative ints; missing dict keys SHALL default to zero, and each before/after difference SHALL be clamped with `max(0, …)` so a negative difference contributes 0.

#### Scenario: Summary has exactly income, expense, net

- **WHEN** `calc_summary` is called with any form
- **THEN** the returned dict keys are exactly `income`, `expense`, `net`
- **AND** the returned dict has no `exp_total`, `exp_10`, `exp_60`, `net_10`, or `net_60` key

#### Scenario: Negative mesos difference clamps income to zero

- **WHEN** `calc_summary` is called with `mesos_start = 5000, mesos_end = 3000` and no other income
- **THEN** `income` is 0

##### Example: standard hunt with item income

- **GIVEN** form with `mesos_start=10000, mesos_end=50000, shop_before=0, shop_after=20000, item_rows=[{qty:63, unit_price:1000}]`, plus an HP row `{price:1000, before:10, after:5}` (5000 expense)
- **WHEN** `calc_summary(form)` is called
- **THEN** the result is `{income: 123000, expense: 5000, net: 118000}` (income = 40000 + 20000 + 63000)

### Requirement: PotionService serializes and deserializes records

The system SHALL provide `PotionService.serialize(form, *, with_timestamp=True)` and `PotionService.deserialize(data)` for the save/load record dialogs and autosave. Serialize SHALL include the keys: `saved_at` (only when `with_timestamp=True`), `duration_minutes`, `hp_potions`, `mp_potions`, `combined_potions`, `mesos_start`, `mesos_end`, `shop_before`, `shop_after`, `item_rows`, `summary`. Serialize SHALL NOT write `exp_start` or `exp_end`. The `summary` block SHALL be computed via `calc_summary` (income/expense/net only). When `with_timestamp=False`, `saved_at` SHALL be omitted.

Deserialize SHALL accept this shape and SHALL also accept legacy records: it SHALL ignore any `exp_start` / `exp_end` keys, SHALL default a missing `item_rows` to an empty list, and SHALL coerce numeric fields safely, returning a `PotionFormData` usable by the page without error. (`duration_minutes` remains part of the persisted/round-tripped schema even though it no longer feeds the summary.)

#### Scenario: Serialize includes item rows and omits experience

- **WHEN** `serialize(form)` is called on a form with `item_rows`
- **THEN** the output dict contains `item_rows` and `summary`
- **AND** the `summary` block has exactly the keys `income`, `expense`, `net`
- **AND** the output dict contains neither `exp_start` nor `exp_end`

#### Scenario: serialize with_timestamp=False omits saved_at

- **WHEN** `serialize(form, with_timestamp=False)` is called
- **THEN** the output dict has no `saved_at` key

#### Scenario: Deserialize a legacy record containing experience fields

- **WHEN** `deserialize(data)` is called on a legacy dict that has `exp_start`, `exp_end`, and no `item_rows`
- **THEN** the returned form omits the experience fields
- **AND** the returned form has `item_rows` equal to an empty list
- **AND** the surviving `mesos_*` / `shop_*` / potion rows are preserved
