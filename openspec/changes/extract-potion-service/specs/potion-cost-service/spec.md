## ADDED Requirements

### Requirement: PotionService provides default potion catalog

The system SHALL expose `PotionService.DEFAULTS` as a class-level constant containing the default potion catalog grouped by section. The catalog SHALL contain three keys: `"hp"`, `"mp"`, and `"combined"`. Each value SHALL be a list of dicts where each dict contains `"name"` (Traditional Chinese string) and `"price"` (positive integer in mesos). The catalog SHALL be the single source of truth consumed by both V1 and V2 potion pages.

#### Scenario: Default catalog is read by both UI versions

- **WHEN** any UI module imports `PotionService.DEFAULTS`
- **THEN** the same catalog dict is returned, identical in name/price values to the V1 `_POTION_DEFAULTS` constant before refactor

##### Example: catalog shape

- **GIVEN** `PotionService.DEFAULTS`
- **WHEN** indexed with `"hp"`
- **THEN** the result is a list whose first element equals `{"name": "馴鹿奶", "price": 5600}`

### Requirement: PotionService computes per-row cost

The system SHALL provide `PotionService.calc_row_cost(row)` that returns the integer cost of one potion row. The cost SHALL equal `max(0, before - after) * price`, where `before`, `after`, `price` are read from the row dict and clamped to non-negative integers. The function MUST NOT raise on missing keys; missing values SHALL be treated as zero.

#### Scenario: Standard row calculation

- **WHEN** `calc_row_cost({"price": 100, "before": 50, "after": 30})` is called
- **THEN** the returned value is 2000

##### Example: edge cases

| Input row                                        | Expected | Notes                          |
| ------------------------------------------------ | -------- | ------------------------------ |
| `{"price": 100, "before": 50, "after": 30}`      | 2000     | normal                         |
| `{"price": 100, "before": 30, "after": 50}`      | 0        | after > before clamps consumed |
| `{"price": 0, "before": 50, "after": 0}`         | 0        | zero price                     |
| `{}`                                             | 0        | all missing                    |
| `{"price": 5600, "before": 200, "after": 200}`   | 0        | nothing consumed               |

### Requirement: PotionService computes section subtotal

The system SHALL provide `PotionService.calc_section_subtotal(rows)` that returns the integer sum of `calc_row_cost` over a list of row dicts. An empty list SHALL return 0.

#### Scenario: Sum multiple rows

- **WHEN** `calc_section_subtotal([{"price":100,"before":10,"after":5},{"price":200,"before":3,"after":1}])` is called
- **THEN** the returned value is `500 + 400 = 900`

### Requirement: PotionService computes full summary

The system SHALL provide `PotionService.calc_summary(form)` that returns a dict with the following keys, computed from a `PotionFormData`:

- `income`: `max(0, mesos_end - mesos_start) + max(0, shop_after - shop_before)`
- `expense`: sum of `calc_section_subtotal` over `hp_potions + mp_potions + combined_potions`
- `net`: `income - expense`
- `exp_total`: `max(0, exp_end - exp_start)`
- `net_10`: `int(net / max(1, duration_minutes) * 10)`
- `exp_10`: `int(exp_total / max(1, duration_minutes) * 10)`
- `net_60`: `int(net / max(1, duration_minutes) * 60)`
- `exp_60`: `int(exp_total / max(1, duration_minutes) * 60)`

The minutes denominator SHALL use `max(1, duration_minutes)` to avoid divide-by-zero. Missing dict keys SHALL default to zero.

#### Scenario: Hourly extrapolation guards against zero minutes

- **WHEN** `calc_summary` is called with `duration_minutes = 0` and `net = 6000`
- **THEN** `net_60` equals 360000 (computed as `int(6000 / 1 * 60)`)

##### Example: standard 30-minute hunt

- **GIVEN** form with `mesos_start=10000, mesos_end=50000, shop_before=0, shop_after=20000, exp_start=1000, exp_end=4000, duration_minutes=30`, plus HP rows summing to 5000 expense
- **WHEN** `calc_summary(form)` is called
- **THEN** the result is `{income: 60000, expense: 5000, net: 55000, exp_total: 3000, net_10: 18333, exp_10: 1000, net_60: 110000, exp_60: 6000}`

### Requirement: PotionService persists autosave via injected ConfigManager

The system SHALL provide `PotionService(config_manager)` that wraps autosave operations. Instance methods SHALL be:

- `save_autosave(form: PotionFormData, *, timer_elapsed: int = 0) -> bool`: delegates to `config_manager.save_potion_autosave(...)` without modifying the input form. The `timer_elapsed` keyword is a UI-only pass-through (seconds accumulated on the page timer); the service composes a new dict with key `_timer_elapsed` before writing, so the page does NOT mutate its own form. Returns the ConfigManager write result (False when no ConfigManager is injected).
- `load_autosave() -> PotionFormData | None`: returns the dict from `config_manager.load_potion_autosave()` (or None)
- `clear_autosave() -> bool`: delegates to `config_manager.delete_potion_autosave()`; returns False when no ConfigManager is injected

The service MUST NOT perform throttling, dirty tracking, or call `save_autosave` automatically — those concerns SHALL remain in the page layer.

#### Scenario: Save then load round-trip

- **WHEN** `service.save_autosave(form)` is called and `service.load_autosave()` is called immediately after
- **THEN** the returned dict equals the input `form` (same JSON shape after round-trip through ConfigManager)

### Requirement: PotionService serializes and deserializes records

The system SHALL provide `PotionService.serialize(form, *, with_timestamp=True)` and `PotionService.deserialize(data)` for the save/load record dialogs. Serialize SHALL include all keys present in the V1 `get_form_data()` output (`saved_at`, `duration_minutes`, `hp_potions`, `mp_potions`, `combined_potions`, `mesos_start`, `mesos_end`, `shop_before`, `shop_after`, `exp_start`, `exp_end`, `summary`). The `summary` block SHALL be computed via `calc_summary`. When `with_timestamp=False`, `saved_at` SHALL be omitted (used by autosave to keep the file compact). Deserialize SHALL accept the same shape and return a `PotionFormData` usable by `load_form_data` in the page.

#### Scenario: Serialize includes timestamp by default

- **WHEN** `serialize(form)` is called
- **THEN** the returned dict contains an ISO-8601 `saved_at` string truncated to seconds

#### Scenario: Round-trip preserves all user data

- **WHEN** `deserialize(serialize(form))` is computed
- **THEN** every user-entered field (rows, mesos, shop, exp, duration) equals the original `form`

### Requirement: PotionService remains free of Qt dependencies

The system SHALL place `PotionService` in `src/domain/potion_service.py` and SHALL NOT import any module from `PySide6`, `src/ui/`, or `src/ui_v2/`. The service MUST be importable in a context with no QApplication instance.

#### Scenario: Import without Qt

- **WHEN** a Python interpreter without PySide6 imports `from src.domain.potion_service import PotionService`
- **THEN** the import succeeds and `PotionService.DEFAULTS` is accessible
