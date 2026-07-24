## ADDED Requirements

### Requirement: Sidebar version label opens the changelog dialog

The sidebar's version label (displaying `v{VERSION}`) SHALL be clickable. Clicking it SHALL open a modal `ChangelogDialogV2` dialog. The label SHALL show a pointing-hand cursor on hover and a tooltip indicating it can be clicked to view the changelog.

#### Scenario: Clicking the version label opens the dialog

- **WHEN** the user clicks the version label at the bottom of the sidebar
- **THEN** a modal changelog dialog opens

#### Scenario: Version label shows an interactive cursor

- **WHEN** the user hovers over the version label
- **THEN** the cursor SHALL change to a pointing hand

### Requirement: Changelog dialog parses the changelog into per-version blocks

`ChangelogDialogV2` SHALL parse the raw text returned by `version.get_changelog()` into a list of version blocks, one per version header matching the pattern `vX.Y.Z (YYYY-MM-DD)`. Each block SHALL retain the version string, the date string, and the body text between that header and the next header (or end of string), with the header's separator line (a line consisting only of `-` characters) stripped and the body's leading/trailing whitespace stripped while preserving internal line breaks and indentation. Blocks SHALL be displayed in the same order they appear in the source text (newest first, matching the existing `CHANGELOG` string's newest-first convention).

#### Scenario: Multi-version changelog is split into separate blocks

- **WHEN** the changelog text contains multiple `vX.Y.Z (YYYY-MM-DD)` headers
- **THEN** the dialog SHALL render one card per header, in source order

##### Example: two versions

- **GIVEN** changelog text `"v2.0.0 (2026-01-01)\n---\n- feature A\n\nv1.0.0 (2025-01-01)\n---\n- initial release\n"`
- **WHEN** the dialog parses this text
- **THEN** it produces two blocks: `("2.0.0", "2026-01-01", "- feature A")` and `("1.0.0", "2025-01-01", "- initial release")`

#### Scenario: No version header found falls back to a single block

- **WHEN** the changelog text contains no line matching the `vX.Y.Z (YYYY-MM-DD)` header pattern
- **THEN** the dialog SHALL render exactly one block containing the entire text, labeled with the current version from `version.get_version()`
- **AND** the dialog SHALL NOT raise an exception or render an empty body

### Requirement: Changelog dialog renders version blocks as a scrollable list

`ChangelogDialogV2` SHALL render the parsed version blocks inside a scrollable area, each block as a card showing the version and date as a header and the body text below it as read-only, word-wrapped plain text.

#### Scenario: Long changelog history is scrollable

- **WHEN** the parsed changelog contains more blocks than fit in the dialog's visible height
- **THEN** the user SHALL be able to scroll to view the remaining blocks
