## ADDED Requirements

### Requirement: Player name input hint reflects code requirement per command

For each command whose needs_name flag is true, the add-name input's placeholder text SHALL indicate whether a "#code" suffix (e.g. "Apple#aSqOX") is required for that specific command. Only the "/密語" command SHALL show a placeholder mentioning the "#code" suffix. All other needs_name commands SHALL show a placeholder that does NOT mention the "#code" suffix.

#### Scenario: Whisper shows the code hint

- **WHEN** the user views the add-name input of the "/密語" card
- **THEN** the placeholder text mentions the "#code" suffix

#### Scenario: Other needs_name commands omit the code hint

- **WHEN** the user views the add-name input of the "/交換", "/搜尋", "/邀請組隊", "/踢出隊伍", "/邀請進入公會", "/封鎖", or "/解除封鎖" card
- **THEN** the placeholder text does NOT mention the "#code" suffix
