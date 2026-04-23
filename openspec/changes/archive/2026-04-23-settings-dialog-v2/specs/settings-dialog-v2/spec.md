## ADDED Requirements

### Requirement: AppCoreMixin SHALL provide apply_settings(result)

The system SHALL add `apply_settings(result: dict) -> None` to `src/ui/app_core.py` (`AppCoreMixin`). The method SHALL:

1. Read these keys from `result` (with documented defaults if missing):
   - `x` (int) → `self.skill_start_x`
   - `y` (int) → `self.skill_start_y`
   - `sound` (bool) → `self.enable_sound`
   - `alert_before_seconds` (int) → `self.alert_before_seconds`
   - `window_size` (int) → `self.window_size`
   - `global_sound` (str, default "") → `self.global_sound`
   - `global_alert_sound` (str, default "") → `self.global_alert_sound`
   - `sound_volume` (int 0-100, default 100) → `self.sound_volume`
2. Update `self.sound_manager.set_volume(self.sound_volume / 100.0)`
3. Sync to `self.skill_service`: `alert_before_seconds`, `global_sound`, `global_alert_sound`
4. Persist all 8 keys via `self.config_manager.set_settings(...)` then `self.config_manager.save()`
5. Update display of `self.alert_seconds_buttons[skill_id]` for skills WITHOUT per-skill override (text becomes `f"{alert_before_seconds}s"`)
6. If `window_size` changed (compared to pre-apply value): `self.window_manager.close_all()` + `self.window_manager.initialize_persistent_skills()`. Otherwise: iterate `self.window_manager.active_windows` to refresh `enable_sound` and call `refresh_window_sound_params(sid)`; if `(x, y)` changed, also call `self.window_manager.reposition_all()`.
7. Emit toast: `self.toast.show("設定已保存並套用", "success")` (skip silently if `self.toast` is None or missing).

V1 `App.show_settings` SHALL be refactored: the entire `if result:` body (currently lines ~292-337 of `src/ui/app.py`) SHALL be replaced by a single `self.apply_settings(result)` call. Behavior MUST be identical.

#### Scenario: V1 show_settings still saves identically

- **GIVEN** V1 App with current settings sound_volume=50
- **WHEN** SettingsDialog is opened, sound_volume changed to 75, OK clicked
- **THEN** `app.sound_volume == 75`, `config_manager.config["settings"]["sound_volume"] == 75`, sound_manager volume reflects 0.75, and a success toast was shown — same as pre-refactor behavior

#### Scenario: window_size change rebuilds windows

- **GIVEN** App with one permanent skill window at window_size=64
- **WHEN** apply_settings is called with `window_size=80` (other fields unchanged)
- **THEN** `window_manager.close_all()` was called once and `initialize_persistent_skills()` was called once

#### Scenario: window_size unchanged but position changed → reposition only

- **GIVEN** App with skill_start_x=100
- **WHEN** apply_settings called with `x=200` (window_size unchanged)
- **THEN** `window_manager.close_all` is NOT called and `window_manager.reposition_all` IS called

### Requirement: SettingsDialogV2 SHALL expose all 8 V1 settings fields

The system SHALL implement `SettingsDialogV2(parent, app)` in `src/ui_v2/dialogs/settings_dialog_v2.py` extending `BaseDialogV2`. The dialog SHALL render 8 input widgets bound to current values from `app`:

- `x`, `y`: two `QSpinBox`, range 0..9999, initial = `app.skill_start_x` / `app.skill_start_y`
- `sound`: `QCheckBox` "啟用聲音", initial = `app.enable_sound`
- `alert_before_seconds`: `QSpinBox` 0..99, initial = `app.alert_before_seconds`
- `window_size`: `QSpinBox` 32..128, initial = `app.window_size`
- `global_sound`: `QComboBox` populated from `app.sound_manager.list_sounds()` + `"— 無 —"` first option (maps to ""); current selection from `app.global_sound`
- `global_alert_sound`: same pattern as `global_sound`, initial from `app.global_alert_sound`
- `sound_volume`: `QSlider` 0..100, initial = `app.sound_volume`; live percentage label

Each sound combo SHALL have a 試聽 (preview) button that calls `app.sound_manager.play(filename)` for the currently-selected option (skip if filename empty).

The dialog SHALL provide 取消 and 確認 buttons. 確認 SHALL build a result dict matching V1 `SettingsDialog.result` structure exactly:

```
{"x": int, "y": int, "sound": bool, "alert_before_seconds": int,
 "window_size": int, "global_sound": str, "global_alert_sound": str,
 "sound_volume": int}
```

Then call `self.app.apply_settings(result)` and `self.accept()`. 取消 SHALL call `self.reject()` without applying.

#### Scenario: Initial values from app

- **GIVEN** app with skill_start_x=300, sound_volume=80, enable_sound=False
- **WHEN** `SettingsDialogV2(parent, app)` is constructed
- **THEN** the X spinbox shows 300, volume slider shows 80, sound checkbox is unchecked

#### Scenario: 確認 builds correct result dict and calls apply_settings

- **GIVEN** dialog with default V1 values
- **WHEN** user clicks 確認 without changing any field
- **THEN** `app.apply_settings` is called once with a dict containing all 8 expected keys and values matching app's initial state

#### Scenario: 取消 does not apply

- **WHEN** user clicks 取消 after changing volume to 50
- **THEN** `app.apply_settings` is NOT called and `app.sound_volume` remains unchanged

### Requirement: SidebarV2 settings gear SHALL open SettingsDialogV2

The system SHALL change `SidebarV2.__init__` in `src/ui_v2/sidebar_v2.py` to accept a new optional callback parameter `on_settings_click=None`. When the bottom gear button is clicked, if the callback is provided, it SHALL be invoked; otherwise the click is a no-op (avoids breaking standalone preview that has no app).

`main_v2.py` SHALL pass a lambda to `SidebarV2(...)` that calls `SettingsDialogV2(window, app_ctx).exec()` to open the dialog modally.

#### Scenario: Gear click opens dialog

- **GIVEN** PreviewWindow with wired V2AppContext
- **WHEN** user clicks the sidebar gear button
- **THEN** a `SettingsDialogV2` instance is created and its `.exec()` is invoked

#### Scenario: Standalone sidebar without callback is safe

- **WHEN** `SidebarV2(parent, on_page_change_cb)` is constructed without `on_settings_click`
- **THEN** clicking the gear is a silent no-op (no AttributeError)
