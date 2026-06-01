# sound-system Specification

## Purpose

TBD - created by archiving change 'sound-system'. Update Purpose after archive.

## Requirements

### Requirement: Builtin sounds are versioned and auto-regenerated

`SoundManager._ensure_builtin_sounds()` SHALL check `sounds/.builtin_version` on initialization.
If the stored version is less than `_SOUND_VERSION`, the system SHALL:
1. Delete known obsolete builtin files (defined in `_OLD_BUILTIN_FILES`)
2. Regenerate all entries in `BUILTIN_SOUNDS` as WAV files in `sounds/`
3. Write the new version number to `sounds/.builtin_version`

If `_SOUND_VERSION` matches the stored version, only missing files SHALL be regenerated.

#### Scenario: Version bump triggers regeneration

- **WHEN** `sounds/.builtin_version` contains a lower version than `_SOUND_VERSION`
- **THEN** all builtin WAV files SHALL be regenerated
- **THEN** `sounds/.builtin_version` SHALL be updated to the current `_SOUND_VERSION`

#### Scenario: No version file triggers full generation

- **WHEN** `sounds/.builtin_version` does not exist
- **THEN** all builtin WAV files SHALL be generated
- **THEN** the version file SHALL be created


<!-- @trace
source: sound-system
updated: 2026-03-20
code:
  - config.json
  - docs/PROJECT.md
  - src/ui/app.py
  - CLAUDE.md
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - src/ui/skill_manager.py
-->

---
### Requirement: WAV files are played via winsound

WAV files SHALL be played using `winsound.PlaySound(filepath, winsound.SND_FILENAME)`.
Playback SHALL occur in a daemon background thread (non-blocking).

If `winsound` is not available (non-Windows), the play call SHALL be silently skipped.

#### Scenario: WAV plays in background

- **WHEN** `SoundManager.play("chime_up.wav")` is called
- **THEN** a daemon thread SHALL start and play the file without blocking the UI


<!-- @trace
source: sound-system
updated: 2026-03-20
code:
  - config.json
  - docs/PROJECT.md
  - src/ui/app.py
  - CLAUDE.md
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - src/ui/skill_manager.py
-->

---
### Requirement: MP3 files are played via Windows MCI

MP3 files SHALL be played using Windows MCI (`winmm.dll` `mciSendStringW`).
Playback SHALL occur in a daemon background thread.
The MCI alias SHALL use the format `snd{counter}` with a globally incrementing counter.
After playback, the MCI device SHALL be closed with `close {alias}`.

#### Scenario: MP3 plays via MCI

- **WHEN** `SoundManager.play("custom.mp3")` is called
- **THEN** a daemon thread SHALL open the file via MCI, play it, then close it


<!-- @trace
source: sound-system
updated: 2026-03-20
code:
  - config.json
  - docs/PROJECT.md
  - src/ui/app.py
  - CLAUDE.md
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - src/ui/skill_manager.py
-->

---
### Requirement: MCI playback is mutually exclusive

Only one MCI playback SHALL occur at a time.
`_mci_lock` (a `threading.Lock`) SHALL be acquired before allocating a new MCI alias.
Concurrent MP3 play requests SHALL be queued by the lock, not dropped.

#### Scenario: Concurrent MP3 requests are serialized

- **WHEN** two MP3 files are played in rapid succession
- **THEN** the second SHALL wait for the first to complete before starting


<!-- @trace
source: sound-system
updated: 2026-03-20
code:
  - config.json
  - docs/PROJECT.md
  - src/ui/app.py
  - CLAUDE.md
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - src/ui/skill_manager.py
-->

---
### Requirement: Legacy sound filenames are migrated

`SoundManager.migrate_sound_filename(filename)` SHALL map obsolete filenames to their replacements:
- `beep_1.wav` → `soft_bell.wav`
- `beep_2.wav` → `alert_double.wav`
- `beep_3.wav` → `alert_urgent.wav`

Filenames not in the migration map SHALL be returned unchanged.

#### Scenario: Legacy filename is remapped

- **WHEN** `migrate_sound_filename("beep_1.wav")` is called
- **THEN** the return value SHALL be `"soft_bell.wav"`

#### Scenario: Unknown filename is unchanged

- **WHEN** `migrate_sound_filename("custom.wav")` is called
- **THEN** the return value SHALL be `"custom.wav"`


<!-- @trace
source: sound-system
updated: 2026-03-20
code:
  - config.json
  - docs/PROJECT.md
  - src/ui/app.py
  - CLAUDE.md
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - src/ui/skill_manager.py
-->

---
### Requirement: Sound import copies file to sounds directory

`SoundManager.import_sound(source_path)` SHALL:
1. Accept only `.wav` and `.mp3` files (case-insensitive extension check)
2. Copy the file to `sounds/` using the original basename
3. If a file with the same name already exists, append `_{counter}` before the extension
4. Return the final filename used, or `None` on failure

#### Scenario: Import unique filename

- **WHEN** `import_sound("/downloads/alert.wav")` is called and `sounds/alert.wav` does not exist
- **THEN** the file SHALL be copied to `sounds/alert.wav`
- **THEN** `"alert.wav"` SHALL be returned

#### Scenario: Import with name collision

- **WHEN** `import_sound("/downloads/alert.wav")` is called and `sounds/alert.wav` already exists
- **THEN** the file SHALL be copied as `sounds/alert_1.wav` (or next available suffix)
- **THEN** the new filename SHALL be returned

#### Scenario: Unsupported format rejected

- **WHEN** `import_sound("/downloads/track.ogg")` is called
- **THEN** the method SHALL return `None` and no file SHALL be copied

<!-- @trace
source: sound-system
updated: 2026-03-20
code:
  - config.json
  - docs/PROJECT.md
  - src/ui/app.py
  - CLAUDE.md
  - src/ui/hotkey_manager.py
  - docs/RELEASE.md
  - docs/ARCHITECTURE.md
  - docs/DATA_FORMAT.md
  - docs/CODE_STYLE.md
  - src/ui/skill_manager.py
-->

---
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


<!-- @trace
source: sound-mute-and-window-scoped-hotkeys
updated: 2026-06-01
code:
  - .release_notes_v4.3.6.md
  - debug_chip.png
  - .release_notes_v4.3.5.md
-->

---
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

<!-- @trace
source: sound-mute-and-window-scoped-hotkeys
updated: 2026-06-01
code:
  - .release_notes_v4.3.6.md
  - debug_chip.png
  - .release_notes_v4.3.5.md
-->