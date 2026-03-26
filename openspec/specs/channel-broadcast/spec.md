# channel-broadcast Specification

## Purpose

TBD - created by archiving change 'channel-broadcast'. Update Purpose after archive.

## Requirements

### Requirement: Packet capture and message parsing

The system SHALL monitor TCP port 32800 using Scapy AsyncSniffer in a daemon thread to capture game channel broadcast messages. The system SHALL parse captured packets by searching for the `TOZ ` marker and extracting fields: Nickname, Text, Type, ProfileCode, UserId, and channel number. Parsed messages SHALL be dispatched to the main thread via `app.after(0, callback)`.

#### Scenario: Successful message capture

- **WHEN** the broadcast listener is running and a game channel message packet arrives on TCP port 32800
- **THEN** the system parses the packet and displays the message in the broadcast page with channel, nickname, content, and timestamp

#### Scenario: Malformed packet

- **WHEN** a captured packet does not contain the `TOZ ` marker or has incomplete fields
- **THEN** the system silently discards the packet without error


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Start, pause, and clear controls

The system SHALL provide three controls on the broadcast page: a Start/Pause toggle button and a Clear button. Start SHALL begin packet capture, Pause SHALL stop capture while retaining displayed messages, and Clear SHALL remove all displayed messages.

#### Scenario: Start capture

- **WHEN** the user clicks the Start button
- **THEN** the system begins packet capture and the button label changes to indicate pause state

#### Scenario: Pause capture

- **WHEN** the user clicks the Pause button while capture is running
- **THEN** the system stops packet capture, retains all currently displayed messages, and the button label changes to indicate start state

#### Scenario: Clear messages

- **WHEN** the user clicks the Clear button
- **THEN** all displayed messages are removed from the message list and the message count resets to zero


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Auto-start option

The system SHALL provide a checkbox labeled for auto-start. When enabled, the broadcast listener SHALL start automatically when the application launches. This setting SHALL be persisted in `config.json` → `settings.broadcast_auto_start`.

#### Scenario: Auto-start enabled

- **WHEN** the application starts and `settings.broadcast_auto_start` is true
- **THEN** the broadcast listener starts automatically without user interaction

#### Scenario: Auto-start disabled

- **WHEN** the application starts and `settings.broadcast_auto_start` is false
- **THEN** the broadcast listener remains stopped until the user manually clicks Start


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Category keyword filtering

The system SHALL provide a category filter with a default "All" option that shows all messages. The user SHALL be able to add custom keyword filters. When a keyword filter is selected, only messages whose content contains that keyword SHALL be displayed.

#### Scenario: Default all filter

- **WHEN** the category filter is set to "All"
- **THEN** all captured messages are displayed regardless of content

#### Scenario: Keyword filter active

- **WHEN** the user selects a custom keyword filter (e.g., "賣")
- **THEN** only messages containing that keyword in their text content are displayed

#### Scenario: Add new keyword

- **WHEN** the user adds a new keyword to the filter list
- **THEN** the keyword appears in the category dropdown and is persisted in `settings.broadcast_keywords`

#### Scenario: Remove keyword

- **WHEN** the user removes a keyword from the filter list
- **THEN** the keyword is removed from the category dropdown and the setting is updated


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Copy FriendTag

The system SHALL allow the user to copy a player's FriendTag (formatted as `Nickname#UserId`) from any displayed message. The copy action SHALL place the FriendTag string into the system clipboard.

#### Scenario: Copy FriendTag via context menu

- **WHEN** the user right-clicks a message and selects "Copy FriendTag"
- **THEN** the FriendTag string (e.g., `Player123#456789`) is copied to the system clipboard

#### Scenario: Copy FriendTag via button

- **WHEN** the user clicks the copy button on a message card
- **THEN** the FriendTag string is copied to the system clipboard and a Toast notification confirms the action


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Blacklist management

The system SHALL maintain a blacklist of FriendTags. Messages from blacklisted players SHALL NOT be displayed. The blacklist SHALL be persisted in `config.json` → `settings.broadcast_blacklist`.

#### Scenario: Add player to blacklist via context menu

- **WHEN** the user right-clicks a message and selects "Add to blacklist"
- **THEN** the player's FriendTag is added to the blacklist and all their messages are immediately hidden

#### Scenario: Remove player from blacklist

- **WHEN** the user removes a FriendTag from the blacklist management UI
- **THEN** the player's future messages are displayed normally

#### Scenario: Blacklisted player sends message

- **WHEN** a captured message belongs to a blacklisted player
- **THEN** the message is not added to the display list


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Disclaimer dialog

The system SHALL display a disclaimer dialog when the user first attempts to start the broadcast listener. The disclaimer SHALL inform the user that: this feature performs passive packet monitoring only, does not modify game data, requires Npcap installation, and usage is at the user's own risk. The user MUST accept the disclaimer before capture can begin. Acceptance SHALL be persisted in `settings.broadcast_disclaimer_accepted`.

#### Scenario: First-time start

- **WHEN** the user clicks Start for the first time and `settings.broadcast_disclaimer_accepted` is false
- **THEN** the system displays the disclaimer dialog before starting capture

#### Scenario: Disclaimer accepted

- **WHEN** the user accepts the disclaimer
- **THEN** `settings.broadcast_disclaimer_accepted` is set to true and the capture starts

#### Scenario: Disclaimer declined

- **WHEN** the user declines the disclaimer
- **THEN** the capture does not start and the button remains in the Start state

#### Scenario: Subsequent starts

- **WHEN** the user clicks Start and `settings.broadcast_disclaimer_accepted` is true
- **THEN** the capture starts immediately without showing the disclaimer


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Message display limit

The system SHALL enforce a maximum number of displayed messages (configured via `settings.broadcast_max_messages`, default 200). When the limit is reached, the oldest messages SHALL be removed to make room for new ones.

#### Scenario: Message limit reached

- **WHEN** the number of displayed messages reaches the configured maximum and a new message arrives
- **THEN** the oldest message is removed and the new message is added


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Page registration

The broadcast page SHALL be registered in the application following the existing page pattern: exported in `pages/__init__.py`, listed in `sidebar.py` PAGES tuple, and instantiated in `app.py` `_build_ui()`.

#### Scenario: Page accessible from sidebar

- **WHEN** the user clicks the broadcast page icon in the sidebar
- **THEN** the broadcast page is displayed in the main content area


<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->

---
### Requirement: Npcap dependency handling

The system SHALL detect when Scapy/Npcap is not available and display a clear error message via Toast notification when the user attempts to start capture.

#### Scenario: Npcap not installed

- **WHEN** the user clicks Start but Npcap is not installed or Scapy cannot initialize
- **THEN** the system displays a Toast notification explaining that Npcap is required and does not crash

<!-- @trace
source: channel-broadcast
updated: 2026-03-26
code:
  - config.json
  - src/ui/pages/__init__.py
  - requirements.txt
  - src/ui/app.py
  - skill_tracker.spec
  - src/ui/pages/broadcast_page.py
  - src/ui/dialogs/broadcast_blacklist_dialog.py
  - src/ui/dialogs/broadcast_disclaimer_dialog.py
  - src/ui/pages/mapleworld_page.py
  - src/ui/sidebar.py
  - src/ui/broadcast_manager.py
  - .spectra.yaml
-->