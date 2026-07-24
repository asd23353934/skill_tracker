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

The command catalog SHALL mirror the in-game Artale `/幫助` command list and present commands in that order. These SHALL be name-parameterized commands (rendering an editable name field and substituting `{name}`): "/搜尋", "/交換", "/密語", "/邀請組隊", "/踢出隊伍", "/邀請進入公會", "/封鎖", "/解除封鎖". All remaining commands SHALL be no-argument commands: "/位置", "/全體", "/地區", "/隊伍", "/公會", "/回覆", "/建立隊伍", "/退出隊伍", "/放煙火", "/箭頭", "/離開突擊", "/離開練習突擊", "/關閉", "/刪除聊天", "/刪除召喚獸", "/幫助". The catalog is data-driven so that commands can be added or removed without code structure changes.

#### Scenario: Catalog mirrors the in-game command list

- **WHEN** the 指令 page loads with the default catalog
- **THEN** the page renders one card per command in the `/幫助` list, in the same order
- **AND** the name-parameterized commands ("/搜尋", "/交換", "/密語", "/邀請組隊", "/踢出隊伍", "/邀請進入公會", "/封鎖", "/解除封鎖") each show a name field while the no-argument commands do not

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
### Requirement: Player name input hint reflects code requirement per command

For each command whose needs_name flag is true, the add-name input's placeholder text SHALL indicate whether a "#code" suffix (e.g. "Apple#aSqOX") is required for that specific command. Only the "/密語" command SHALL show a placeholder mentioning the "#code" suffix. All other needs_name commands SHALL show a placeholder that does NOT mention the "#code" suffix.

#### Scenario: Whisper shows the code hint

- **WHEN** the user views the add-name input of the "/密語" card
- **THEN** the placeholder text mentions the "#code" suffix

#### Scenario: Other needs_name commands omit the code hint

- **WHEN** the user views the add-name input of the "/交換", "/搜尋", "/邀請組隊", "/踢出隊伍", "/邀請進入公會", "/封鎖", or "/解除封鎖" card
- **THEN** the placeholder text does NOT mention the "#code" suffix

<!-- @trace
source: command-page-ux-polish
updated: 2026-07-24
code:
  - src/ui_v2/pages/command_page_v2.py
  - src/ui/hotkey_manager.py
  - src/ui_v2/dialogs/settings_dialog_v2.py
-->