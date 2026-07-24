## MODIFIED Requirements

### Requirement: Hotkey trigger dispatch

On a key press outside capture mode, the system SHALL check all three hotkey namespaces for a match on the pressed key:
1. Skill namespace via `skill_manager.get_skill_by_hotkey(key_name)`
2. Monster namespace via `app.get_monster_by_hotkey(key_name)`
3. Command namespace via `config_manager.get_command_hotkey_target(key_name)`, checked only when `app.command_page` exists and `config_manager.get_command_hotkeys_enabled()` is true

A match in one namespace SHALL NOT prevent checking or triggering the other namespaces. When two or more namespaces match the same key, the system SHALL dispatch a trigger for every matching namespace, each on the main thread via `app.after(0, ...)`. When the window-scoped hotkey filter (see Window-scoped hotkey triggering) is enabled and the target window is not foreground, the filter check SHALL be evaluated once for the key press as a whole — only when at least one namespace matched — and if it blocks, it SHALL suppress every matching namespace's trigger together rather than being checked once per namespace. When no namespace matches, no action SHALL be taken and no error SHALL be raised.

#### Scenario: Skill trigger on key press

- **WHEN** the user presses a key bound to a skill only
- **THEN** `app.after(0, lambda: window_manager.trigger_skill(skill_id))` is called

#### Scenario: Monster trigger on key press

- **WHEN** the user presses a key bound to a monster only
- **THEN** `app.after(0, lambda: window_manager.trigger_monster(monster_id))` is called

#### Scenario: Skill and command both bound to the same key

- **WHEN** the same key is bound to both a skill and a command, and the user presses that key
- **THEN** both the skill trigger and the command trigger are dispatched — the skill match SHALL NOT prevent the command from also triggering

#### Scenario: Skill, monster, and command all bound to the same key

- **WHEN** the same key is bound to a skill, a monster, and a command simultaneously, and the user presses that key
- **THEN** all three triggers are dispatched: `trigger_skill`, `trigger_monster`, and the command's copy action

#### Scenario: No match

- **WHEN** the user presses a key not bound to any skill, monster, or command
- **THEN** no action is taken; no error is raised


<!-- @trace
source: hotkey-binding-spec
updated: 2026-03-20
code:
  - docs/CODE_STYLE.md
  - docs/DATA_FORMAT.md
  - src/ui/hotkey_manager.py
  - docs/ARCHITECTURE.md
  - docs/RELEASE.md
  - docs/PROJECT.md
  - CLAUDE.md
-->

---
### Requirement: Window-scoped hotkey triggering

The system SHALL provide a global toggle that, when enabled, restricts skill and monster hotkey triggering to only when a configured target program is the foreground window. The target SHALL be matched by the foreground window's executable name. When the toggle is disabled (the default), hotkeys SHALL trigger regardless of the foreground window.

The foreground-window check SHALL be performed only after a key press has already matched a registered skill or monster hotkey, so that key presses unrelated to any hotkey incur no additional cost. Hotkey capture mode SHALL NOT be subject to this filter.

The foreground-window check SHALL use only OS calls that are safe to run on the pynput daemon thread and SHALL NOT touch any Qt widget.

When the filter is enabled, the target program is not the foreground window, and a key press matches a registered skill, monster, or command hotkey, the system SHALL show a toast (dispatched to the main thread via `app.after(0, ...)`) informing the user that the current window is not the target window and the hotkey was not triggered, in addition to suppressing the trigger.

#### Scenario: Hotkey suppressed when target not foreground

- **WHEN** the filter is enabled, the target program is not the foreground window, and the user presses a key bound to a skill
- **THEN** the skill SHALL NOT be triggered
- **AND** a toast SHALL inform the user that the hotkey was not triggered because the target window is not foreground

#### Scenario: Hotkey allowed when target is foreground

- **WHEN** the filter is enabled, the target program is the foreground window, and the user presses a key bound to a skill
- **THEN** the skill SHALL be triggered as normal
- **AND** no suppression toast SHALL be shown

#### Scenario: Filter disabled triggers everywhere

- **WHEN** the filter is disabled and the user presses a key bound to a skill
- **THEN** the skill SHALL be triggered regardless of the foreground window

#### Scenario: Capture mode ignores filter

- **WHEN** the filter is enabled and the user is assigning a hotkey in capture mode
- **THEN** the key SHALL be captured normally without any foreground-window check

#### Scenario: Suppressed command hotkey also shows the toast

- **WHEN** the filter is enabled, the target program is not the foreground window, and the user presses a key bound to a command (quick-copy)
- **THEN** the command SHALL NOT be copied to the clipboard
- **AND** a toast SHALL inform the user that the hotkey was not triggered because the target window is not foreground

#### Scenario: Filter blocks all matching namespaces together

- **WHEN** the filter is enabled, the target program is not the foreground window, and the same key is bound to both a skill and a command
- **THEN** neither the skill nor the command triggers
- **AND** only one suppression toast is shown for the key press, not one per namespace

## ADDED Requirements

### Requirement: Settings dialog explains the window-scoped hotkey filter

The settings dialog's "快捷鍵限定" row SHALL display a short explanatory line describing that enabling the filter restricts hotkey triggering to when the selected target window is the foreground window.

#### Scenario: Explanation text is visible

- **WHEN** the user opens the settings dialog
- **THEN** the "快捷鍵限定" row shows an explanatory line describing the filter's purpose, in addition to the checkbox, target label, and window-picker button
