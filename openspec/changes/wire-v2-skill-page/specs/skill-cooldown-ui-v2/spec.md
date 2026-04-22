## ADDED Requirements

### Requirement: Renders real skill data from SkillManager

The V2 skill page SHALL populate its three columns (Player / Boss / Item) from `app.skill_manager.get_skills()` and `app.skill_manager.get_items()`, grouped by `category` then `subcategory`. It SHALL NOT use hard-coded demo data.

#### Scenario: Column populated from manager

- **WHEN** `SkillPageV2` is built with a fully-initialized App
- **THEN** each column displays the set of skills whose `category` matches the column, grouped into sub-sections by `subcategory`, and the header chip count equals the number of cards shown

#### Scenario: Empty category

- **WHEN** a category has zero matching skills
- **THEN** the column renders with a "0" header chip and no sub-section rows

### Requirement: Skill card displays per-skill state

Each `SkillCardV2` SHALL reflect the current App state for its `skill_id`:

- Cooldown chip: shows `app.skill_cooldown_overrides[id]` when set, otherwise the original `cooldown` from metadata; chip background signals "modified" when an override is active.
- Hotkey chip: shows `app.skill_hotkeys[id]` when non-empty, otherwise the literal `未設`; chip background signals "assigned" when a hotkey exists.
- Permanent / Loop / Alert checkboxes: each reflects `app.skill_permanent[id]` / `app.skill_loop[id]` / `app.skill_alert_enabled[id]`.
- Alert-seconds pill: shows `app.skill_alert_seconds_overrides[id]` when set, otherwise the global `app.alert_before_seconds`.

#### Scenario: Card with cooldown override

- **WHEN** `skill_cooldown_overrides["fireball"]` is 12 and metadata cooldown is 20
- **THEN** the fireball card's cooldown chip reads `12秒` with modified-state background

#### Scenario: Card with no hotkey assigned

- **WHEN** `skill_hotkeys["heal"]` is the empty string
- **THEN** the heal card's hotkey chip reads `未設` with muted background

##### Example: card state matrix

| State source | Value | Chip text | Chip style |
| ------------ | ----- | --------- | ---------- |
| `skill_cooldown_overrides["x"]` | 12 | `12秒` | modified |
| `skill_cooldown_overrides["x"]` | unset (metadata cooldown=20) | `20秒` | default |
| `skill_hotkeys["x"]` | `"F1"` | `F1` | assigned |
| `skill_hotkeys["x"]` | `""` | `未設` | muted |
| `skill_alert_seconds_overrides["x"]` | 5 | `5s` | modified |
| `skill_alert_seconds_overrides["x"]` | unset (global=3) | `3s` | default |

### Requirement: Card controls delegate to App methods

`SkillCardV2` user interactions SHALL delegate to existing App methods rather than writing profile state directly:

- Cooldown chip click → `app.edit_cooldown(skill_id)`; reset → `app.reset_cooldown(skill_id)`.
- Hotkey chip click → `app.hotkey_manager.begin_capture(skill_id, skill_name)`; reset → `app.reset_hotkey(skill_id)`.
- Permanent / Loop checkbox toggled → `app.update_skill_setting_exclusive(skill_id, key, checkbox)`.
- Alert checkbox toggled → `app.update_alert_setting(skill_id, checkbox)`.
- Alert-seconds pill click → `app.edit_alert_seconds(skill_id)`.
- `⋮` detail button click → `app.show_skill_detail(skill_id)` which opens `SkillDetailDialogV2`.

#### Scenario: Toggling permanent routes through App

- **WHEN** user checks the `常` checkbox on a card
- **THEN** `app.update_skill_setting_exclusive(skill_id, "permanent", checkbox)` is invoked exactly once, and the card does NOT write to `app.skill_permanent` directly

#### Scenario: Cooldown reset clears override

- **WHEN** user clicks the cooldown reset button
- **THEN** `app.reset_cooldown(skill_id)` is invoked, which removes the key from `skill_cooldown_overrides` and triggers a `save_profile` call

### Requirement: Card registers into App widget dictionaries

To stay compatible with existing App refresh paths, each `SkillCardV2` SHALL register its interactive controls into the App dictionaries used by V1:

- `app.cooldown_buttons[skill_id]` → the cooldown chip's value button.
- `app.hotkey_buttons[skill_id]` → the hotkey chip's value button.
- `app.alert_seconds_buttons[skill_id]` → the alert-seconds pill.
- `app.permanent_vars[skill_id]` / `app.loop_vars[skill_id]` / `app.alert_enabled_vars[skill_id]` → each respective checkbox.

When the page is rebuilt (e.g. on profile switch), the new cards SHALL overwrite the previous dictionary entries.

#### Scenario: Registration after build

- **WHEN** `SkillPageV2` finishes building its cards
- **THEN** for every `skill_id` rendered, all six dictionaries contain the card's widget references

#### Scenario: Registration after profile switch rebuild

- **WHEN** the page rebuilds in response to `app.profile_changed`
- **THEN** the dictionary entries are replaced by references from the new cards (old references are overwritten, not appended)

### Requirement: Card exposes a refresh method

`SkillCardV2` SHALL provide a public `refresh()` method that re-reads App state for its `skill_id` and updates chip texts, chip styles, checkbox checked states, and pill text, without rebuilding the widget tree. Checkbox state writes MUST suppress signals (`blockSignals`) to avoid retriggering App callbacks.

#### Scenario: Refresh after state change

- **WHEN** `app.skill_cooldown_overrides["fireball"]` changes from unset to 15 and `card.refresh()` is called
- **THEN** the cooldown chip text updates to `15秒` and the chip adopts modified-state background

#### Scenario: Refresh does not retrigger callbacks

- **WHEN** `card.refresh()` sets a checkbox to checked
- **THEN** `app.update_skill_setting_exclusive` is NOT invoked as a side effect of the refresh

### Requirement: Page rebuilds on first show and profile switch

`SkillPageV2` SHALL rebuild its full widget tree when:

- The page is first shown (`showEvent`), so initial metadata fetch is deferred until after App construction completes.
- `app.profile_changed` fires, so cards reflect the newly active profile.

Single-card state changes (driven by user interaction or App callbacks) SHALL NOT trigger a full rebuild; they SHALL instead invoke `refresh()` on the affected card.

#### Scenario: First show rebuild

- **WHEN** the page becomes visible for the first time
- **THEN** the three columns populate from `skill_manager` and the total card count equals `len(get_skills()) + len(get_items())`

#### Scenario: Profile switch rebuild

- **WHEN** `app.profile_changed` signal fires
- **THEN** the page rebuilds and new cards reflect state from the newly selected profile's JSON

#### Scenario: Checkbox toggle does not rebuild

- **WHEN** user toggles a checkbox on one card
- **THEN** the page widget tree is not rebuilt; only that card's refresh path runs

### Requirement: Header quick-toggle chips call toggle_all

The page header SHALL expose three chips labeled `常駐` / `循環` / `提醒`. Clicking a chip SHALL invoke `app.toggle_all('permanent' | 'loop' | 'alert')` with no confirmation dialog. After the call completes, every affected card's `refresh()` SHALL run so checkbox states update.

#### Scenario: Toggle-all permanent on

- **WHEN** user clicks the `常駐` chip and `skill_permanent` previously had zero true entries
- **THEN** `app.toggle_all('permanent')` is invoked, all `skill_permanent` entries become true, and every card's `常` checkbox becomes checked

### Requirement: Hotkey capture dispatches to main thread

When `hotkey_manager` fires a hotkey trigger from its pynput daemon thread, any subsequent UI work (card highlight, chip text update) SHALL be dispatched to the main thread via `app.after(0, func)` before touching V2 widgets.

#### Scenario: Hotkey-triggered refresh

- **WHEN** pynput daemon thread invokes the hotkey callback chain
- **THEN** the V2 card's `refresh()` is not called directly from the daemon thread; it runs only after the dispatcher has scheduled it onto the main thread

### Requirement: SkillDetailDialogV2 reads and writes sound overrides

`SkillDetailDialogV2` SHALL provide, for a given `skill_id`:

- End-sound dropdown bound to `app.skill_sound_overrides[id]` (unset entry maps to "default").
- Alert-sound dropdown bound to `app.skill_alert_sound_overrides[id]`.
- A 試聽 button next to each dropdown that invokes `app.sound_manager.play(path)` without closing the dialog.
- A "從清單移除" button that removes the skill from the current profile (not from `config.json` static metadata) and closes the dialog.

On accept, changes SHALL be persisted via `app.config_manager.save_profile(current_name, snapshot)`.

#### Scenario: Change end-sound and accept

- **WHEN** user picks `alarm_01.wav` in the end-sound dropdown and clicks accept
- **THEN** `app.skill_sound_overrides[skill_id]` equals `alarm_01.wav` and `save_profile` has been invoked with the updated snapshot

#### Scenario: Preview without accepting

- **WHEN** user picks a sound and clicks 試聽, then clicks cancel
- **THEN** `sound_manager.play` was invoked for the previewed file but `skill_sound_overrides[skill_id]` is unchanged on dialog cancel
