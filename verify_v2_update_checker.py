"""
驗證 V2 預覽 shell 的自動更新檢查 — wire-v2-update-checker

執行：
    python verify_v2_update_checker.py

涵蓋 6 個 case：
    A. 有新版           → UpdateDialog 被建構，父視窗為傳入的 self（PreviewWindow）
    B. 無新版           → UpdateDialog 不被建構
    C. 網路失敗         → 不彈窗、不 raise、stdout 含錯誤訊息
    D. Dialog 建構錯誤  → 主流程不 crash、stdout 含 dialog error 與 RuntimeError
    E. env=1 排程模式   → _schedule_update_check 不註冊 QTimer
    F. env 未設排程模式 → _schedule_update_check 註冊 QTimer.singleShot(1000, _run_update_check)
"""
import io
import os
import sys
import types
import contextlib
from types import SimpleNamespace
from unittest.mock import patch

# 強制 Qt 在 headless 模式運行（CI / 本地皆可）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# 預設啟用測試模式（避免任何意外的 import 副作用真的打網路）
os.environ.setdefault("SKILL_TRACKER_DISABLE_UPDATE_CHECK", "1")

from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

import main_v2  # noqa: E402
from main_v2 import PreviewWindow  # noqa: E402


# --------------------------------------------------
# 工具
# --------------------------------------------------

class _SyncThread:
    """同步替身：呼叫 .start() 時直接同步執行 target，方便測試 worker 行為"""
    def __init__(self, target, daemon=None, **_):
        self._target = target

    def start(self):
        self._target()


def _make_fake():
    """建立一個 fake PreviewWindow：只綁定我們要測的方法 + app_ctx.after stub"""
    fake = SimpleNamespace()
    # after(0, fn) → 同步呼叫，模擬已 marshalled 到主執行緒
    fake.app_ctx = SimpleNamespace(after=lambda ms, fn: fn())
    fake._schedule_update_check = types.MethodType(PreviewWindow._schedule_update_check, fake)
    fake._run_update_check      = types.MethodType(PreviewWindow._run_update_check, fake)
    fake._on_update_result      = types.MethodType(PreviewWindow._on_update_result, fake)
    return fake


@contextlib.contextmanager
def _capture_stdout():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


@contextlib.contextmanager
def _patched_updater(return_value):
    """patch Updater().check_for_updates() 的回傳值"""
    with patch("src.infrastructure.updater.Updater") as MockUpdater:
        MockUpdater.return_value.check_for_updates.return_value = return_value
        yield MockUpdater


@contextlib.contextmanager
def _patched_dialog(dialog_cls):
    with patch("src.ui.dialogs.update_dialog.UpdateDialog", dialog_cls):
        yield


# --------------------------------------------------
# Cases
# --------------------------------------------------

def case_a_new_version():
    """有新版 → UpdateDialog 被建構，父視窗為傳入的 self"""
    fake = _make_fake()
    update_info = {
        "available": True,
        "current": "1.0.0",
        "latest": "99.0.0",
        "download_url": "https://example/x.exe",
        "release_notes": "",
    }
    calls = []

    class FakeDialog:
        def __init__(self, parent, info):
            calls.append(("init", parent, info))

        def exec(self):
            calls.append(("exec",))

    with patch("main_v2.threading.Thread", _SyncThread), \
         _patched_updater(update_info), \
         _patched_dialog(FakeDialog):
        fake._run_update_check()

    assert len(calls) == 2, f"expected 2 calls (init + exec), got {calls}"
    kind, parent, info = calls[0]
    assert kind == "init"
    assert parent is fake, f"parent must be the PreviewWindow self, got {parent!r}"
    assert info is update_info, "update_info must pass through unchanged"
    assert calls[1] == ("exec",), "dialog.exec() must be called"
    print("[A] PASS — new version → dialog opened with self as parent")


def case_b_no_update():
    """無新版 → UpdateDialog 不被建構，無 exception"""
    fake = _make_fake()
    calls = []

    class FakeDialog:
        def __init__(self, *a, **k):
            calls.append("init")

        def exec(self):
            calls.append("exec")

    with patch("main_v2.threading.Thread", _SyncThread), \
         _patched_updater({"available": False}), \
         _patched_dialog(FakeDialog):
        fake._run_update_check()

    assert calls == [], f"UpdateDialog must not be constructed; got {calls}"
    print("[B] PASS — no update → no dialog, no exception")


def case_c_network_failure():
    """網路失敗 → 不彈窗、不 raise、stdout 含錯誤訊息"""
    fake = _make_fake()
    calls = []

    class FakeDialog:
        def __init__(self, *a, **k):
            calls.append("init")

    with _capture_stdout() as buf, \
         patch("main_v2.threading.Thread", _SyncThread), \
         _patched_updater({"available": False, "error": "network unreachable"}), \
         _patched_dialog(FakeDialog):
        fake._run_update_check()

    output = buf.getvalue()
    assert calls == [], f"UpdateDialog must not be constructed; got {calls}"
    assert "network unreachable" in output, f"stdout must mention error; got: {output!r}"
    print("[C] PASS — network failure → no dialog, error printed")


def case_d_dialog_error():
    """Dialog 建構錯誤 → 主流程不 crash、stdout 含 dialog error 與 RuntimeError"""
    fake = _make_fake()

    class BoomDialog:
        def __init__(self, *a, **k):
            raise RuntimeError("boom")

    update_info = {
        "available": True,
        "current": "1.0.0",
        "latest": "99.0.0",
        "download_url": "https://example/x.exe",
        "release_notes": "",
    }
    with _capture_stdout() as buf, \
         patch("main_v2.threading.Thread", _SyncThread), \
         _patched_updater(update_info), \
         _patched_dialog(BoomDialog):
        # 不應 raise
        fake._run_update_check()

    output = buf.getvalue()
    assert "dialog error" in output, f"stdout must contain 'dialog error'; got: {output!r}"
    assert "RuntimeError" in output, f"stdout must mention RuntimeError; got: {output!r}"
    print("[D] PASS — dialog error → swallowed, error printed")


def case_e_env_disabled():
    """env=1 時 _schedule_update_check 不註冊 QTimer"""
    fake = _make_fake()
    qt_calls = []

    with patch.dict(os.environ, {"SKILL_TRACKER_DISABLE_UPDATE_CHECK": "1"}, clear=False):
        with patch.object(main_v2.QTimer, "singleShot",
                          lambda *a, **k: qt_calls.append(a)):
            fake._schedule_update_check()

    assert qt_calls == [], f"QTimer.singleShot must not be called; got {qt_calls}"
    print("[E] PASS — env=1 → no QTimer scheduled")


def case_f_env_enabled():
    """env 未設時 _schedule_update_check 註冊 QTimer.singleShot(1000, _run_update_check)"""
    fake = _make_fake()
    qt_calls = []

    # 暫時清掉 env，patch.dict 會自動 restore
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("SKILL_TRACKER_DISABLE_UPDATE_CHECK", None)
        with patch.object(main_v2.QTimer, "singleShot",
                          lambda *a, **k: qt_calls.append(a)):
            fake._schedule_update_check()

    assert len(qt_calls) == 1, f"expected 1 QTimer.singleShot call; got {qt_calls}"
    delay, callback = qt_calls[0]
    assert delay == 1000, f"delay must be 1000ms; got {delay}"
    assert callable(callback), "callback must be callable"
    # callback 應該綁到 fake._run_update_check（bound method 的 __func__ 比較）
    assert getattr(callback, "__func__", None) is PreviewWindow._run_update_check, \
        f"callback must be _run_update_check bound method; got {callback!r}"
    assert getattr(callback, "__self__", None) is fake, \
        f"callback must be bound to fake instance; got {callback!r}"
    print("[F] PASS — env unset → QTimer.singleShot(1000, _run_update_check) scheduled")


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    cases = [
        case_a_new_version,
        case_b_no_update,
        case_c_network_failure,
        case_d_dialog_error,
        case_e_env_disabled,
        case_f_env_enabled,
    ]
    failures = []
    for c in cases:
        try:
            c()
        except AssertionError as e:
            failures.append((c.__name__, str(e)))
            print(f"[{c.__name__}] FAIL — {e}")
        except Exception as e:
            failures.append((c.__name__, f"{type(e).__name__}: {e}"))
            print(f"[{c.__name__}] ERROR — {type(e).__name__}: {e}")

    print()
    if failures:
        print(f"FAILED: {len(failures)}/{len(cases)}")
        for name, msg in failures:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    print(f"ALL PASSED: {len(cases)}/{len(cases)}")


if __name__ == "__main__":
    main()
