## ADDED Requirements

### Requirement: ToastManagerV2 SHALL replace _NoopToast in V2AppContext

The system SHALL replace the `_NoopToast` class in `main_v2.py` with a real `ToastManagerV2` instance bound to the `PreviewWindow`. After replacement:

- `V2AppContext.toast` SHALL be set to a `ToastManagerV2` instance instead of `_NoopToast`
- The instance SHALL be created in `PreviewWindow.__init__` after `_build()` completes (toast container needs the window to exist)
- The `_NoopToast` class definition in `main_v2.py` SHALL be removed entirely

#### Scenario: V2AppContext.toast is real

- **WHEN** the V2 preview launches
- **THEN** `app_ctx.toast` is a `ToastManagerV2` instance, NOT a `_NoopToast`

### Requirement: ToastManagerV2 SHALL expose show(message, kind)

The system SHALL provide `ToastManagerV2.show(message: str, kind: str = "info")` accepting four kinds: `"info"`, `"success"`, `"warning"`, `"error"`. Unknown kinds SHALL fall back to `"info"`. The method SHALL be safe to call from the main thread; calls from other threads are NOT supported (callers must dispatch through `app.after(0, ...)`, matching V1 contract).

#### Scenario: All 4 kinds dispatch without error

- **GIVEN** a constructed `ToastManagerV2`
- **WHEN** `show("hello", k)` is called for each k in `{"info", "success", "warning", "error"}`
- **THEN** each call returns without raising and a toast widget is added to the manager's tracking list

#### Scenario: Unknown kind falls back to info

- **WHEN** `show("hello", "exotic")` is called
- **THEN** the toast renders with the same colors as `kind="info"` and no exception is raised

### Requirement: ToastV2 SHALL render with V2Theme tokens

The system SHALL implement `ToastV2(QFrame)` whose visuals derive from `src/ui_v2/theme_v2.py` (`V2Theme as T`):

- Border-radius: `T.R_MD` (matches other V2 cards)
- Background: kind-specific accent at `T.alpha(accent, 32)` over `T.BG_ELEVATED` for contrast
- Border: 1px solid kind-specific accent
- Text color: `T.TEXT_HI`
- Font: `T.FONT_LABEL` family/size
- Kind → accent mapping: `info → T.CYAN`, `success → T.GREEN`, `warning → T.ORANGE`, `error → T.RED`
- Layout: 12 px horizontal padding, 8 px vertical padding, single-line message label, NO close button (auto-dismiss only — keep V2 minimal)

The widget SHALL NOT use any color literal not derived from `V2Theme`.

#### Scenario: Success toast uses V2Theme.GREEN accent

- **WHEN** a `ToastV2(parent, "saved", "success")` is constructed
- **THEN** querying `widget.styleSheet()` contains `T.GREEN` as a substring (border color)

### Requirement: ToastV2 SHALL fade in, auto-dismiss after 3000 ms, fade out

The system SHALL animate each ToastV2 lifecycle:

- On show: 200 ms fade-in via `QGraphicsOpacityEffect` from opacity 0 → 1
- After 3000 ms wall time: trigger fade-out
- Fade-out: 250 ms opacity 1 → 0, then `deleteLater()` and removal from `ToastManagerV2._toasts` list

The auto-dismiss timer SHALL be a `QTimer.singleShot(3000, ...)` started after fade-in completes. The widget SHALL NOT block input events on the parent window.

#### Scenario: Auto-dismiss timing

- **GIVEN** a ToastV2 just shown at t=0
- **WHEN** wall-clock t = 3500 ms (3000 dismiss + 250 fade + 250 buffer)
- **THEN** the toast widget is no longer in `manager._toasts` and has been `deleteLater()`'d

### Requirement: ToastManagerV2 SHALL stack toasts at PreviewWindow bottom-right

The system SHALL position toasts in the PreviewWindow's bottom-right corner with 16 px margin from edges. When multiple toasts coexist, newer toasts appear above older ones with 8 px gap. Layout SHALL re-flow when:

- A new toast is added (push older ones up)
- An old toast is dismissed (slide remaining toasts down)

The manager SHALL track active toasts in `self._toasts: list[ToastV2]` ordered oldest → newest.

#### Scenario: Stack of 3 toasts positioned correctly

- **GIVEN** PreviewWindow size 1240×760, three toasts shown in succession with `info`/`success`/`error`
- **WHEN** all three are simultaneously visible
- **THEN** the newest (error) is at the bottom-right at y_position farthest from top; older ones stack above with 8 px gaps; all three within window bounds

### Requirement: ToastManagerV2 SHALL re-anchor on PreviewWindow resize

The system SHALL reposition all active toasts when the PreviewWindow size changes (user resizes the window). The reposition SHALL trigger from listening to the window's `resizeEvent` or via `QObject.installEventFilter` on the PreviewWindow.

#### Scenario: Window resize moves toasts

- **GIVEN** A toast positioned at (1224 - toast_width, 744 - toast_height) in a 1240×760 window
- **WHEN** PreviewWindow resizes to 800×600
- **THEN** the toast's position updates to (784 - toast_width, 584 - toast_height) — still anchored 16 px from new bottom-right
