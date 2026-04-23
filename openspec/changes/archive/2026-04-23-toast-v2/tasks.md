## 1. 前置驗證

- [x] 1.1 跑 `python verify_skill_page_v2.py` + `python verify_monster_page_v2.py` 確認既有 V2 全綠

## 2. ToastV2 SHALL render with V2Theme tokens

- [x] 2.1 落實 Requirement「ToastV2 SHALL render with V2Theme tokens」：新建 `src/ui_v2/toast_v2.py`，實作 `ToastV2(QFrame)`：建構參數 `(parent, message: str, kind: str = "info")`；kind→accent 映射 `info→T.CYAN`、`success→T.GREEN`、`warning→T.ORANGE`、`error→T.RED`；styleSheet 使用 `T.alpha(accent, 32)` 背景、1px accent 邊框、`T.R_MD` 圓角、`T.TEXT_HI` 文字；單行 message label 用 T.FONT_LABEL；padding 12/8 px；不放 close button
- [x] 2.2 加 unknown-kind fallback：dict.get(kind, info_colors)
- [x] 2.3 import smoke：`python -c "from src.ui_v2.toast_v2 import ToastV2"` 必須通過

## 3. ToastV2 SHALL fade in, auto-dismiss after 3000 ms, fade out

- [x] 3.1 落實 Requirement「ToastV2 SHALL fade in, auto-dismiss after 3000 ms, fade out」：在 `ToastV2` 加 `QGraphicsOpacityEffect`，初值 opacity 0；`show_animated()` 方法觸發 200ms 0→1 fade-in；fade-in 完成後 `QTimer.singleShot(3000, self._begin_dismiss)`；`_begin_dismiss` 跑 250ms 1→0 fade-out 後 `self.deleteLater()` + emit `dismissed` signal 通知 manager
- [x] 3.2 widget 不可擋滑鼠：`setAttribute(Qt.WA_TransparentForMouseEvents, False)` 預設可點，但確認 toast 不在 main 內容上方擋 input —— 設 `setFocusPolicy(Qt.NoFocus)` 並接受 hover

## 4. ToastManagerV2 SHALL expose show(message, kind)

- [x] 4.1 落實 Requirement「ToastManagerV2 SHALL expose show(message, kind)」：在同檔加 `class ToastManagerV2`，建構 `(window: QMainWindow)`；`_toasts: list[ToastV2] = []`；`show(message, kind="info")` 建立 ToastV2、append 到 _toasts、connect dismissed signal → `_remove_toast`、呼叫 widget.show_animated()、最後 `_reposition_all()`
- [x] 4.2 `_remove_toast(toast)`：從 `_toasts` remove + `_reposition_all()`

## 5. ToastManagerV2 SHALL stack toasts at PreviewWindow bottom-right

- [x] 5.1 落實 Requirement「ToastManagerV2 SHALL stack toasts at PreviewWindow bottom-right」：實作 `_reposition_all()`：window=self._window；margin=16；gap=8；從最新 (list 末尾) 開始放 bottom-right，往上累積：第 N 新的 toast y = window.height() - margin - sum(prev heights + gap)；x = window.width() - margin - toast.width()

## 6. ToastManagerV2 SHALL re-anchor on PreviewWindow resize

- [x] 6.1 落實 Requirement「ToastManagerV2 SHALL re-anchor on PreviewWindow resize」：ToastManagerV2 在 `__init__` 呼叫 `window.installEventFilter(self)`；`eventFilter(obj, event)` 偵測 `event.type() == QEvent.Type.Resize and obj is self._window` → `self._reposition_all()`；class 改繼承 `QObject` 才能裝 eventFilter

## 7. ToastManagerV2 SHALL replace _NoopToast in V2AppContext

- [x] 7.1 落實 Requirement「ToastManagerV2 SHALL replace _NoopToast in V2AppContext」：移除 `main_v2.py` 內 `_NoopToast` class 定義、移除 `V2AppContext.__init__` 中 `self.toast = _NoopToast()` 一行
- [x] 7.2 在 `PreviewWindow.__init__` 末段（`self.app_ctx = V2AppContext()` 後、_build 後）加 `self.app_ctx.toast = ToastManagerV2(self)`，需要 import `from src.ui_v2.toast_v2 import ToastManagerV2`

## 8. 驗證腳本

- [x] 8.1 新建 `verify_toast_v2.py`，仿 verify_skill_page_v2.py：建立 QApplication + 假 PreviewWindow（QMainWindow + resize 1240x760）；建構 ToastManagerV2(win)
- [x] 8.2 test: `show("hello", k)` for k in {info, success, warning, error} 各跑一次，斷言 manager._toasts 長度從 0 累積到 4，無例外
- [x] 8.3 test: `show("???", "exotic")` 不 raise，新 toast.styleSheet 含 T.CYAN（fallback 至 info）
- [x] 8.4 test: 連 show 3 個 → manager._reposition_all 後三個 widget 的 y 座標遞減（最新最低、最舊最高）；x 都靠 window.width() - margin
- [x] 8.5 test: window.resize(800, 600) → 觸發 eventFilter → toast x/y 更新為新邊界
- [x] 8.6 test: success toast 的 styleSheet 字串含 T.GREEN
- [x] 8.7 全腳本通過 exit 0

## 9. 手動驗證

- [x] 9.1 `python main.py --v2` 啟動，python -c "win = QApplication.activeWindow(); win.app_ctx.toast.show('測試 success', 'success')" 看到綠色 toast 從右下角出現、3 秒後淡出
- [x] 9.2 連續觸發 4 個 toast → 確認堆疊（最新最低、舊的往上推）
- [x] 9.3 拖曳視窗 resize → toast 跟著錨定右下角

## 10. 收尾

- [x] 10.1 跑 `/simplify` 與 `/spectra-audit` 檢視 toast_v2 + main_v2 diff
- [x] 10.2 同步 docs/PROJECT.md：在 src/ui_v2/ 條目下加入 `toast_v2.py`
- [x] 10.3 commit：純 V2 新增、V1 不動、不 bump version
