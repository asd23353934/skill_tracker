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