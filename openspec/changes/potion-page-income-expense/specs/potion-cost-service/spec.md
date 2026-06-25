## ADDED Requirements

### Requirement: PotionService computes item-acquisition income total

The system SHALL provide `PotionService.calc_items_total(rows)` that returns the summed value of item-acquisition rows, computed as the sum over each row of `max(0, qty) * max(0, unit_price)`. Missing or non-numeric `qty`/`unit_price` SHALL be treated as zero. An empty or missing list SHALL return 0.

#### Scenario: Sum item rows

- **WHEN** `calc_items_total` is called with rows `[{qty: 3, unit_price: 1000}, {qty: 5, unit_price: 200}]`
- **THEN** the result is 4000

##### Example: guards and empties

| Rows | Result | Notes |
| ---- | ------ | ----- |
| [] | 0 | empty list |
| [{qty: 2, unit_price: -50}] | 0 | negative price clamped |
| [{qty: 0, unit_price: 999}] | 0 | zero quantity |
| [{name: "緞帶", qty: 4, unit_price: 25}] | 100 | name ignored in math |

## MODIFIED Requirements

### Requirement: PotionService computes full summary

The system SHALL provide `PotionService.calc_summary(form)` that returns a dict with the following keys, computed from a `PotionFormData`:

- `income`: `max(0, mesos_end - mesos_start) + max(0, shop_after - shop_before) + calc_items_total(item_rows)`
- `expense`: sum of `calc_section_subtotal` over `hp_potions + mp_potions + combined_potions`
- `net`: `income - expense`
- `net_10`: `int(net / max(1, duration_minutes) * 10)`
- `net_60`: `int(net / max(1, duration_minutes) * 60)`

The summary SHALL NOT include any experience metric. The minutes denominator SHALL use `max(1, duration_minutes)` to avoid divide-by-zero. Missing dict keys SHALL default to zero.

#### Scenario: Hourly extrapolation guards against zero minutes

- **WHEN** `calc_summary` is called with `duration_minutes = 0` and a net of 6000
- **THEN** `net_60` equals 360000 (computed as `int(6000 / 1 * 60)`)

#### Scenario: Summary omits experience keys

- **WHEN** `calc_summary` is called with any form
- **THEN** the returned dict has no `exp_total`, `exp_10`, or `exp_60` key

##### Example: standard 30-minute hunt with item income

- **GIVEN** form with `mesos_start=10000, mesos_end=50000, shop_before=0, shop_after=20000, item_rows=[{qty:3, unit_price:1000}], duration_minutes=30`, plus HP rows summing to 5000 expense
- **WHEN** `calc_summary(form)` is called
- **THEN** the result is `{income: 63000, expense: 5000, net: 58000, net_10: 19333, net_60: 116000}`

### Requirement: PotionService serializes and deserializes records

The system SHALL provide `PotionService.serialize(form, *, with_timestamp=True)` and `PotionService.deserialize(data)` for the save/load record dialogs. Serialize SHALL include the keys: `saved_at`, `duration_minutes`, `hp_potions`, `mp_potions`, `combined_potions`, `mesos_start`, `mesos_end`, `shop_before`, `shop_after`, `item_rows`, `summary`. Serialize SHALL NOT write `exp_start` or `exp_end`. The `summary` block SHALL be computed via `calc_summary`. When `with_timestamp=False`, `saved_at` SHALL be omitted. Deserialize SHALL accept this shape and SHALL also accept legacy records: it SHALL ignore any `exp_start`/`exp_end` keys and SHALL default a missing `item_rows` to an empty list, returning a `PotionFormData` usable by the page without error.

#### Scenario: Serialize includes item rows and omits experience

- **WHEN** `serialize(form)` is called on a form with `item_rows`
- **THEN** the output dict contains `item_rows` and `summary`
- **AND** the output dict contains neither `exp_start` nor `exp_end`

#### Scenario: Deserialize a legacy record containing experience fields

- **WHEN** `deserialize(data)` is called on a legacy dict that has `exp_start`, `exp_end`, and no `item_rows`
- **THEN** the returned form omits the experience fields
- **AND** the returned form has `item_rows` equal to an empty list
