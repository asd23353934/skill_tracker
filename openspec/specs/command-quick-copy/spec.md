# command-quick-copy Specification

## Purpose

TBD - created by archiving change 'command-quick-copy'. Update Purpose after archive.

## Requirements

### Requirement: Command quick-copy page

The system SHALL provide a "指令" commands page under `src/ui_v2/pages/` that lists a data-driven catalog of Artale in-game chat commands. The catalog SHALL be defined as a module-level constant where each entry has a key, display label, command template, description, and a needs_name flag. Each command SHALL render as a card showing the command text, its description, and a copy button.

#### Scenario: Page renders the command catalog

- **WHEN** the user opens the 指令 page
- **THEN** the page renders one card per command in the catalog, each showing the command text, description, and a copy button


<!-- @trace
source: command-quick-copy
updated: 2026-06-17
code:
  - version.py
  - src/ui_v2/sidebar_v2.py
  - main_v2.py
  - debug_chip.png
  - src/ui_v2/pages/command_page_v2.py
  - docs/DATA_FORMAT.md
  - README.md
  - .release_notes_v4.3.5.md
  - docs/PROJECT.md
  - src/infrastructure/config_manager.py
  - .release_notes_v4.3.6.md
tests:
  - tests/test_command_recent_names.py
-->

---
### Requirement: Copy command to system clipboard

Each command card's copy button SHALL write the resulting command string to the system clipboard via the Qt clipboard. The system SHALL NOT inject keystrokes into the game or any other application. The system SHALL show a toast confirming the copy.

#### Scenario: Copy a no-argument command

- **WHEN** the user clicks the copy button on the "/箭頭" command card
- **THEN** the system clipboard contains exactly "/箭頭"
- **AND** a toast confirms the command was copied


<!-- @trace
source: command-quick-copy
updated: 2026-06-17
code:
  - version.py
  - src/ui_v2/sidebar_v2.py
  - main_v2.py
  - debug_chip.png
  - src/ui_v2/pages/command_page_v2.py
  - docs/DATA_FORMAT.md
  - README.md
  - .release_notes_v4.3.5.md
  - docs/PROJECT.md
  - src/infrastructure/config_manager.py
  - .release_notes_v4.3.6.md
tests:
  - tests/test_command_recent_names.py
-->

---
### Requirement: Parameterized commands substitute a player name

Commands whose needs_name flag is true SHALL render an editable name field (a combo box that accepts typed input and lists remembered names). When the user copies such a command, the system SHALL substitute the trimmed field value into the command template `{name}` placeholder. When the field is empty, the system SHALL copy the command keyword followed by a single trailing space.

#### Scenario: Copy a parameterized command with a name

- **WHEN** the user types "Apple#aSqOX" into the name field of the "/交換" card and clicks copy
- **THEN** the system clipboard contains exactly "/交換 Apple#aSqOX"

#### Scenario: Copy a parameterized command with an empty name

- **WHEN** the name field of the "/交換" card is empty and the user clicks copy
- **THEN** the system clipboard contains the command keyword followed by one trailing space ("/交換 ")


<!-- @trace
source: command-quick-copy
updated: 2026-06-17
code:
  - version.py
  - src/ui_v2/sidebar_v2.py
  - main_v2.py
  - debug_chip.png
  - src/ui_v2/pages/command_page_v2.py
  - docs/DATA_FORMAT.md
  - README.md
  - .release_notes_v4.3.5.md
  - docs/PROJECT.md
  - src/infrastructure/config_manager.py
  - .release_notes_v4.3.6.md
tests:
  - tests/test_command_recent_names.py
-->

---
### Requirement: Remember used player names

When the user copies a parameterized command with a non-empty trimmed name, the system SHALL record that name in a recent-names list persisted in the `settings` section of `config_user.json`. The list SHALL keep the most-recently-used entry first, SHALL contain no duplicates, and SHALL be capped at 20 entries. Names SHALL be stored verbatim including any "#" suffix. The recent-names dropdown of every parameterized command SHALL offer this list.

#### Scenario: A copied name is remembered and offered next time

- **WHEN** the user copies "/密語" with name "Bob#1a2b3"
- **THEN** "Bob#1a2b3" is saved to the recent-names list in config_user.json
- **AND** "Bob#1a2b3" appears in the name dropdown of parameterized command cards

#### Scenario: Re-using a name promotes it without duplicating

- **WHEN** the user copies a command with a name already present in the recent-names list
- **THEN** that name moves to the front of the list and appears only once

##### Example: promotion, insertion, and cap

| Existing list (front to back) | Copied name | Resulting list (front to back) |
| ----------------------------- | ----------- | ------------------------------ |
| [A, B, C]                     | B           | [B, A, C]                      |
| [A, B, C]                     | D           | [D, A, B, C]                   |
| [20 distinct names]           | new         | [new, first 19 of old]         |


<!-- @trace
source: command-quick-copy
updated: 2026-06-17
code:
  - version.py
  - src/ui_v2/sidebar_v2.py
  - main_v2.py
  - debug_chip.png
  - src/ui_v2/pages/command_page_v2.py
  - docs/DATA_FORMAT.md
  - README.md
  - .release_notes_v4.3.5.md
  - docs/PROJECT.md
  - src/infrastructure/config_manager.py
  - .release_notes_v4.3.6.md
tests:
  - tests/test_command_recent_names.py
-->

---
### Requirement: Backward-compatible recent-names storage

When `config_user.json` has no recent-names field (existing installs upgrading to this version), the system SHALL treat the recent-names list as empty and SHALL NOT raise an error.

#### Scenario: Upgrade with no existing field

- **WHEN** the app loads a config_user.json that lacks the recent-names field
- **THEN** the recent-names list is empty and the page loads without error


<!-- @trace
source: command-quick-copy
updated: 2026-06-17
code:
  - version.py
  - src/ui_v2/sidebar_v2.py
  - main_v2.py
  - debug_chip.png
  - src/ui_v2/pages/command_page_v2.py
  - docs/DATA_FORMAT.md
  - README.md
  - .release_notes_v4.3.5.md
  - docs/PROJECT.md
  - src/infrastructure/config_manager.py
  - .release_notes_v4.3.6.md
tests:
  - tests/test_command_recent_names.py
-->

---
### Requirement: Sidebar navigation entry

The system SHALL add a navigation entry for the 指令 page to the V2 sidebar, using a lucide icon loaded via lucide_pixmap. Selecting the entry SHALL switch the main view to the 指令 page.

#### Scenario: Navigate to the commands page

- **WHEN** the user clicks the 指令 entry in the sidebar
- **THEN** the main view switches to the 指令 page


<!-- @trace
source: command-quick-copy
updated: 2026-06-17
code:
  - version.py
  - src/ui_v2/sidebar_v2.py
  - main_v2.py
  - debug_chip.png
  - src/ui_v2/pages/command_page_v2.py
  - docs/DATA_FORMAT.md
  - README.md
  - .release_notes_v4.3.5.md
  - docs/PROJECT.md
  - src/infrastructure/config_manager.py
  - .release_notes_v4.3.6.md
tests:
  - tests/test_command_recent_names.py
-->

---
### Requirement: Seed command catalog

The initial command catalog SHALL include these Artale commands as no-argument commands: "/箭頭" (head marker), "/r" (reply last whisper), "/關閉" (hide other players' skill effects), "/放煙火" (fireworks), "/mute" (mute other players' effects), and "/desummon" (recall summon); and these as name-parameterized commands: "/交換 {name}" (trade) and "/密語 {name}" (whisper). The catalog is data-driven so that more commands can be appended without code structure changes.

#### Scenario: Seed commands are present with correct name fields

- **WHEN** the 指令 page loads with the default catalog
- **THEN** cards for "/箭頭", "/r", "/關閉", "/放煙火", "/mute", "/desummon", "/交換", and "/密語" are shown
- **AND** "/交換" and "/密語" each show a name field while the others do not

<!-- @trace
source: command-quick-copy
updated: 2026-06-17
code:
  - version.py
  - src/ui_v2/sidebar_v2.py
  - main_v2.py
  - debug_chip.png
  - src/ui_v2/pages/command_page_v2.py
  - docs/DATA_FORMAT.md
  - README.md
  - .release_notes_v4.3.5.md
  - docs/PROJECT.md
  - src/infrastructure/config_manager.py
  - .release_notes_v4.3.6.md
tests:
  - tests/test_command_recent_names.py
-->