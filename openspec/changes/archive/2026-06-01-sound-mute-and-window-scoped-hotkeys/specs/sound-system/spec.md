## ADDED Requirements

### Requirement: Completion and alert sounds are independently mutable

The system SHALL provide two independent global toggles: one for the cooldown-completion sound and one for the early-alert sound. Each toggle SHALL gate only its own sound category. The completion sound SHALL play only when the completion toggle is enabled; the early-alert sound SHALL play only when the alert toggle is enabled.

On loading user settings, if the legacy single `enable_sound` setting exists but the two new settings (`enable_end_sound`, `enable_alert_sound`) are absent, both new settings SHALL be initialized from the legacy value.

#### Scenario: Mute completion sound only

- **WHEN** the completion toggle is disabled and the alert toggle is enabled
- **THEN** a skill reaching cooldown completion SHALL NOT play its completion sound
- **THEN** an early-alert for that skill SHALL still play its alert sound

#### Scenario: Migration from legacy enable_sound

- **WHEN** user settings contain `enable_sound = false` and neither new toggle is present
- **THEN** both `enable_end_sound` and `enable_alert_sound` SHALL be initialized to `false`

### Requirement: Individual skills can mute their sounds

Each skill's completion sound and early-alert sound SHALL each support three states: use-global (inherit the global sound), a specific sound file, or muted (never play). The muted state SHALL be represented by a reserved sentinel value distinct from the empty (use-global) value, stored in the existing per-skill override maps.

When resolving a skill's sound, the system SHALL apply this precedence: if the relevant global toggle is disabled, the sound SHALL be silent regardless of per-skill state; otherwise a muted sentinel SHALL resolve to silent, a specific file SHALL resolve to that file, and an empty value SHALL resolve to the global sound.

#### Scenario: Per-skill mute while global enabled

- **WHEN** the completion toggle is enabled and a skill's completion override is the mute sentinel
- **THEN** that skill SHALL play no completion sound while other skills play theirs

#### Scenario: Global toggle overrides per-skill setting

- **WHEN** the completion toggle is disabled and a skill's completion override is a specific file
- **THEN** that skill SHALL play no completion sound

##### Example: completion sound resolution

| Global completion toggle | Per-skill override | Resolved sound |
| --- | --- | --- |
| disabled | (any) | silent |
| enabled | mute sentinel | silent |
| enabled | "ding.wav" | ding.wav |
| enabled | empty | global completion sound |
