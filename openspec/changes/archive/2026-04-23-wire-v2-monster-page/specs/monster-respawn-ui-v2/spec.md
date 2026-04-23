## ADDED Requirements

### Requirement: AppCoreMixin exposes 8 monster interaction methods

The system SHALL move the following 8 methods from `src/ui/app.py` (V1 App class body) to `src/ui/app_core.py` (`AppCoreMixin`), preserving their exact signatures and behavior so V1 App and V2AppContext access an identical implementation:

- `edit_respawn_time(monster_id)`
- `reset_respawn_time(monster_id)`
- `reset_monster_hotkey(monster_id)`
- `edit_monster_alert_before(monster_id)`
- `update_monster_alert_sound(monster_id, filename)`
- `update_monster_end_sound(monster_id, filename)`
- `update_monster_loop(monster_id, loop_value)`
- `update_monster_permanent(monster_id, permanent_value)`

After the move, `App.edit_respawn_time.__qualname__` SHALL start with `"AppCoreMixin."`. The 8 method bodies in `App` SHALL be removed (no leftover stubs or `pass` placeholders).

#### Scenario: V2AppContext can call moved methods directly

- **WHEN** a `V2AppContext` instance calls `edit_respawn_time("nonexistent_id")`
- **THEN** the call resolves through `AppCoreMixin` without `AttributeError`, and the method returns without side effects (consistent with V1 behavior on unknown id)

#### Scenario: V1 App qualname check

- **WHEN** `python -c "from src.ui.app import App; assert App.edit_respawn_time.__qualname__.startswith('AppCoreMixin.')"` runs
- **THEN** the assertion passes

### Requirement: V2 monster page lists current profile monsters

The system SHALL replace `DEMO_MONSTERS` in `src/ui_v2/pages/monster_page_v2.py` with a dynamic list sourced from `app.get_all_monsters()`. The page SHALL render one `MonsterCard` per monster on first `showEvent` (cached on a `_loaded` flag), iterating in the order returned by `MonsterService.get_all()`. When `app` is `None` (preview-only mode without backing), the page SHALL show no cards rather than fall back to demo data.

#### Scenario: First showEvent triggers load

- **WHEN** the monster page is shown for the first time with a wired `V2AppContext`
- **THEN** the page contains exactly `len(app.get_all_monsters())` `MonsterCard` instances and `_loaded` is `True`

#### Scenario: Subsequent showEvent does not re-render

- **WHEN** the user switches to another page and back
- **THEN** no additional cards are created (the `_loaded` flag short-circuits)

### Requirement: MonsterCard wires interactions to App methods

The system SHALL change the `MonsterCard.__init__` signature in `src/ui_v2/pages/monster_page_v2.py` to `(parent, app, monster_id)`. Internally the card SHALL read its current state from `app.monster_service.get(monster_id)` and connect its widgets as follows:

- Respawn-time chip click → `app.edit_respawn_time(monster_id)`; reset → `app.reset_respawn_time(monster_id)`
- Hotkey chip click → `app.hotkey_manager.begin_capture(monster_id, monster["name"])`; reset → `app.reset_monster_hotkey(monster_id)`
- Alert-seconds pill click → `app.edit_monster_alert_before(monster_id)`
- Loop checkbox toggled → `app.update_monster_loop(monster_id, value)`
- Permanent checkbox toggled → `app.update_monster_permanent(monster_id, value)`
- End-sound combo changed → `app.update_monster_end_sound(monster_id, filename)`
- Alert-sound combo changed → `app.update_monster_alert_sound(monster_id, filename)`

The card SHALL register its respawn button into `app.monster_respawn_buttons[monster_id]` and its alert pill into `app.monster_alert_before_buttons[monster_id]` so V1 update helpers (e.g. `app._apply_btn_style`) can mutate them. The card SHALL expose a public method `set_hotkey_text(text, has_hotkey)` so HotkeyManager callbacks can update display after capture.

#### Scenario: Cooldown chip click forwards to app

- **GIVEN** an `app` with a mock `edit_respawn_time` recording calls
- **WHEN** the user clicks the respawn-time chip on a `MonsterCard("时间魔方")`
- **THEN** `app.edit_respawn_time` was called exactly once with `"时间魔方"` (using the actual monster id)

#### Scenario: Permanent checkbox toggle persists

- **GIVEN** a `MonsterCard` with `permanent=False`
- **WHEN** the user checks the permanent checkbox
- **THEN** `app.update_monster_permanent(monster_id, True)` is called and `monster_service.get(monster_id)["permanent"]` returns `True` afterward

### Requirement: HotkeyManager callback updates V1 or V2 monster card

The system SHALL update `src/ui/hotkey_manager.py` so the post-capture display update for monsters routes through a method-detection pattern: if the registered card object exposes `set_hotkey_text(text, has_hotkey)`, it SHALL be called; otherwise the V1 path `update_hotkey_display(text, has_hotkey)` SHALL be called. The dispatch SHALL go through `app.after(0, …)` (existing thread-safe pattern), preserving V1 behavior unchanged.

#### Scenario: V2 card receives hotkey update

- **GIVEN** a V2 `MonsterCard` registered via `hotkey_manager._monster_card = card_v2`
- **WHEN** pynput captures `F5` and the manager callback fires
- **THEN** `card_v2.set_hotkey_text("F5", True)` is called on the main thread

#### Scenario: V1 card path still works

- **GIVEN** a V1 `_MonsterCard` registered via the same attribute
- **WHEN** pynput captures `F6`
- **THEN** the V1 card's `update_hotkey_display("F6", True)` is called (V1 had no `set_hotkey_text` method)

### Requirement: V2 monster page removes the add-monster button

The system SHALL remove the `add_btn` (新增怪物) widget from `MonsterPageV2._build` in `src/ui_v2/pages/monster_page_v2.py`. V1 has no add-monster UI and the curated monster list comes from `config.json`. The page header SHALL retain only the title (怪物重生) and the hint label.

#### Scenario: Header has no add button

- **WHEN** `MonsterPageV2` is rendered
- **THEN** scanning all `QPushButton` children of the header bar finds zero buttons whose text equals "新增怪物"
