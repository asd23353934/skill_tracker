## MODIFIED Requirements

### Requirement: Parameterized commands substitute a player name

Commands whose needs_name flag is true SHALL render a row of clickable name chips plus a single add-name input field, instead of an editable combo box. Each chip SHALL display one saved player name. Clicking a chip SHALL substitute that name into the command template `{name}` placeholder, copy the result to the system clipboard, and show a confirming toast. Submitting a non-empty trimmed value in the add-name input SHALL copy the command with that name substituted AND save the name to the command's name list. Submitting an empty value SHALL copy the command keyword followed by a single trailing space and SHALL NOT add a chip.

#### Scenario: Copy by clicking a saved name chip

- **WHEN** the "/交換" card has a chip "Apple#aSqOX" and the user clicks that chip
- **THEN** the system clipboard contains exactly "/交換 Apple#aSqOX"
- **AND** a toast confirms the command was copied

#### Scenario: Add a new name copies and saves it

- **WHEN** the user types "Bob#1a2b3" into the add-name input of the "/密語" card and submits
- **THEN** the system clipboard contains exactly "/密語 Bob#1a2b3"
- **AND** a chip "Bob#1a2b3" appears on the "/密語" card

#### Scenario: Submitting an empty name copies the bare command

- **WHEN** the add-name input of the "/交換" card is empty and the user submits
- **THEN** the system clipboard contains the command keyword followed by one trailing space ("/交換 ")
- **AND** no chip is added

### Requirement: Remember used player names

The system SHALL persist each parameterized command's player names as a per-command list under a `command_names` map in the `settings` section of `config_user.json`, keyed by the command's key. Each list SHALL keep the most-recently-used entry first, SHALL contain no duplicates, and SHALL be capped at 20 entries. Names SHALL be stored verbatim including any "#" suffix. Each command's chips SHALL reflect only that command's own list. Each chip SHALL carry a delete control (×) and an in-place rename control (✎); entering rename SHALL show an inline editor where Enter confirms, while Esc or loss of focus cancels without changing the name. The system SHALL support adding a name, deleting a single name, and renaming a name in place; each operation SHALL persist immediately and re-render the chips.

#### Scenario: Names are isolated per command

- **WHEN** the user adds "Carol#9z9z9" on the "/交換" card
- **THEN** "Carol#9z9z9" appears as a chip on the "/交換" card
- **AND** "Carol#9z9z9" does NOT appear on the "/密語" card

#### Scenario: Delete a name chip

- **WHEN** the user clicks the delete control (×) on the chip "Bob#1a2b3" of the "/密語" card
- **THEN** "Bob#1a2b3" is removed from the "/密語" command's name list in config_user.json
- **AND** the chip no longer renders

#### Scenario: Edit a name chip in place

- **WHEN** the user clicks the chip's rename control (✎) for "Bob#1a2b3" on the "/密語" card and confirms "Bob#4c5d6" with Enter
- **THEN** the "/密語" command's name list contains "Bob#4c5d6" and not "Bob#1a2b3"
- **AND** the renamed entry keeps its previous position in the list

##### Example: promotion, insertion, and cap (per command list)

| Existing list (front to back) | Added name | Resulting list (front to back) |
| ----------------------------- | ---------- | ------------------------------ |
| [A, B, C]                     | B          | [B, A, C]                      |
| [A, B, C]                     | D          | [D, A, B, C]                   |
| [20 distinct names]           | new        | [new, first 19 of old]         |

### Requirement: Backward-compatible recent-names storage

When `config_user.json` has no `command_names` map, the system SHALL fall back to reading the legacy shared `command_recent_names` list (if present) as the read-only initial set of chips for every parameterized command, and SHALL NOT modify the legacy key. When neither field is present, the system SHALL treat each command's name list as empty and SHALL NOT raise an error. Any add/edit/delete SHALL write to the `command_names` map under that command's key.

#### Scenario: Upgrade with only the legacy shared list

- **WHEN** the app loads a config_user.json that has `command_recent_names` but no `command_names`
- **THEN** every parameterized command's chips are seeded from the legacy list
- **AND** the legacy `command_recent_names` key is left unchanged

#### Scenario: Upgrade with neither field

- **WHEN** the app loads a config_user.json that lacks both `command_names` and `command_recent_names`
- **THEN** each command's name list is empty and the page loads without error
