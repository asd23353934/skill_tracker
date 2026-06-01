## ADDED Requirements

### Requirement: Window-scoped hotkey triggering

The system SHALL provide a global toggle that, when enabled, restricts skill and monster hotkey triggering to only when a configured target program is the foreground window. The target SHALL be matched by the foreground window's executable name. When the toggle is disabled (the default), hotkeys SHALL trigger regardless of the foreground window.

The foreground-window check SHALL be performed only after a key press has already matched a registered skill or monster hotkey, so that key presses unrelated to any hotkey incur no additional cost. Hotkey capture mode SHALL NOT be subject to this filter.

The foreground-window check SHALL use only OS calls that are safe to run on the pynput daemon thread and SHALL NOT touch any Qt widget.

#### Scenario: Hotkey suppressed when target not foreground

- **WHEN** the filter is enabled, the target program is not the foreground window, and the user presses a key bound to a skill
- **THEN** the skill SHALL NOT be triggered

#### Scenario: Hotkey allowed when target is foreground

- **WHEN** the filter is enabled, the target program is the foreground window, and the user presses a key bound to a skill
- **THEN** the skill SHALL be triggered as normal

#### Scenario: Filter disabled triggers everywhere

- **WHEN** the filter is disabled and the user presses a key bound to a skill
- **THEN** the skill SHALL be triggered regardless of the foreground window

#### Scenario: Capture mode ignores filter

- **WHEN** the filter is enabled and the user is assigning a hotkey in capture mode
- **THEN** the key SHALL be captured normally without any foreground-window check

### Requirement: Target window selection via thumbnail picker

The system SHALL provide a picker that lists currently open top-level windows, each shown with a visual thumbnail of the window's content and its title, so the user can identify the target window visually. Selecting a window SHALL store that window's executable name as the hotkey filter target. The picker SHALL provide a refresh action to re-enumerate windows and re-capture thumbnails.

Thumbnails SHALL be captured using a per-window render that is independent of window stacking order, so the picker being frontmost does not obscure the captured content. For a minimized window whose content cannot be rendered, the picker SHALL fall back to showing the program icon and title.

#### Scenario: Select target from picker

- **WHEN** the user opens the picker, clicks a window card, and confirms
- **THEN** that window's executable name SHALL be stored as the filter target
- **THEN** the settings entry SHALL display the chosen window's title

#### Scenario: Minimized window fallback

- **WHEN** the picker lists a minimized window whose content cannot be captured
- **THEN** that window's card SHALL show the program icon and title instead of a content thumbnail

#### Scenario: Refresh re-captures windows

- **WHEN** the user clicks refresh in the picker
- **THEN** the window list and thumbnails SHALL be regenerated from the current desktop state
