"""
驗證 update_failed.txt marker 偵測 — main_v2 啟動時讀檔 → toast → 刪檔

涵蓋 case：
    A. marker 存在（reason 有值）→ toast warning 含 reason、檔案被刪
    B. marker 存在但 reason 行缺失   → toast warning 含「未知原因」、檔案被刪
    C. marker 不存在                → toast 不被呼叫
    D. marker 內容無法 parse        → 不 raise、檔案仍被刪
    E. SKILL_TRACKER_DISABLE_UPDATE_CHECK=1 → 不掃 marker（test 環境隔離）
    F. reason 為空字串                → toast 顯示 fallback「未知原因」
    G. reason 含 URL（marker 偽造攻擊）→ toast fallback，避免釣魚 echo
    H. reason 超長                    → 截斷至 200 字 + 「…」
    I. unlink PermissionError 不 raise → toast 仍觸發

用 tmp dir + monkeypatch user_data_path，避免 Ctrl+C 殘留污染真實 user_data。

執行：
    python verify_update_failure_marker.py
"""
import os
import sys
import tempfile
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# 個別 case 會自行處理這個 env，預設不設

from PySide6.QtWidgets import QApplication  # noqa: E402

_app = QApplication.instance() or QApplication(sys.argv)

import main_v2  # noqa: E402
from main_v2 import PreviewWindow  # noqa: E402


def _make_fake():
    fake = SimpleNamespace()
    fake.app_ctx = SimpleNamespace()
    fake.app_ctx.toast = SimpleNamespace(_calls=[])
    fake.app_ctx.toast.show = lambda msg, kind="info": fake.app_ctx.toast._calls.append((msg, kind))
    fake._check_update_failure_marker = types.MethodType(
        PreviewWindow._check_update_failure_marker, fake
    )
    return fake


def _run_with_tmp_marker(content: str | None, env_disable: bool = False, fake_unlink_error: bool = False):
    """共用 fixture：tmp dir + monkeypatch user_data_path + 可選 unlink error。

    Returns: (toast_calls, marker_still_exists_after_call)
    在 tempdir context 內取 bool，避免 context 結束自動 cleanup 影響判斷。
    """
    fake = _make_fake()
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        marker = td_path / "update_failed.txt"
        if content is not None:
            marker.write_text(content, encoding="utf-8")

        env_patches = []
        if env_disable:
            env_patches.append(patch.dict(os.environ, {"SKILL_TRACKER_DISABLE_UPDATE_CHECK": "1"}, clear=False))
        else:
            # 顯式移除以避免外部 env 污染（例如其他 verify script 留下的）
            env_patches.append(patch.dict(os.environ, {}, clear=False))

        unlink_patch = None
        if fake_unlink_error:
            real_unlink = Path.unlink

            def boom_unlink(self, *a, **kw):
                if str(self) == str(marker):
                    raise PermissionError("simulated AV lock")
                return real_unlink(self, *a, **kw)
            unlink_patch = patch.object(Path, "unlink", boom_unlink)

        with patch.object(main_v2, "user_data_path", lambda rel: str(td_path / rel)):
            for p in env_patches:
                p.start()
            if not env_disable:
                os.environ.pop("SKILL_TRACKER_DISABLE_UPDATE_CHECK", None)
            try:
                if unlink_patch:
                    with unlink_patch:
                        fake._check_update_failure_marker()
                else:
                    fake._check_update_failure_marker()
            finally:
                for p in reversed(env_patches):
                    p.stop()

        return fake.app_ctx.toast._calls, marker.exists()


def case_a_marker_with_reason():
    calls, marker_exists = _run_with_tmp_marker(
        "timestamp: 2026-04-30 10:00:00\n"
        "reason: 解壓 ZIP 完成但找不到新版 exe\n"
    )
    assert len(calls) == 1, f"toast must be called once; got {calls}"
    msg, kind = calls[0]
    assert "解壓 ZIP 完成但找不到新版 exe" in msg, f"toast 訊息缺 reason；got {msg!r}"
    assert kind == "warning"
    assert not marker_exists
    print("[A] PASS — marker 含 reason → toast warning + 刪檔")


def case_b_marker_missing_reason():
    calls, marker_exists = _run_with_tmp_marker("timestamp: 2026-04-30 10:00:00\n")
    assert len(calls) == 1
    msg, kind = calls[0]
    assert "未知原因" in msg
    assert not marker_exists
    print("[B] PASS — marker 缺 reason → toast 顯示 '未知原因'")


def case_c_no_marker():
    calls, _ = _run_with_tmp_marker(None)
    assert calls == [], "marker 不存在時不應觸發 toast"
    print("[C] PASS — 無 marker → toast 不被呼叫")


def case_d_unreadable_marker():
    fake = _make_fake()
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        marker = td_path / "update_failed.txt"
        marker.write_text("ok\n", encoding="utf-8")

        real_open = open
        call_count = [0]

        def boom_open(file, *a, **kw):
            if str(file) == str(marker) and call_count[0] == 0:
                call_count[0] += 1
                raise OSError("simulated read error")
            return real_open(file, *a, **kw)

        with patch.object(main_v2, "user_data_path", lambda rel: str(td_path / rel)), \
             patch("builtins.open", side_effect=boom_open):
            fake._check_update_failure_marker()

        calls = fake.app_ctx.toast._calls
        assert len(calls) == 1, f"預期 toast 仍被叫；got {calls}"
        assert calls[0][1] == "warning"
        assert not marker.exists(), "讀失敗仍要嘗試刪檔"
    print("[D] PASS — marker 讀失敗 → 不 raise、仍 toast + 刪檔")


def case_e_env_disabled():
    calls, marker_exists = _run_with_tmp_marker(
        "reason: 安裝失敗\n",
        env_disable=True,
    )
    assert calls == [], f"DISABLE 時不應觸發 toast；got {calls}"
    assert marker_exists, "DISABLE 時不應刪 marker（保留給下次正常啟動）"
    print("[E] PASS — DISABLE_UPDATE_CHECK=1 → marker scan 跳過")


def case_f_empty_reason():
    calls, marker_exists = _run_with_tmp_marker(
        "timestamp: 2026-04-30 10:00:00\n"
        "reason: \n"
    )
    assert len(calls) == 1
    msg, _ = calls[0]
    assert "未知原因" in msg, f"空 reason 應 fallback；got {msg!r}"
    # 防 broken 中文 「上次自動更新失敗：，請手動下載」
    assert "失敗：，" not in msg
    assert not marker_exists
    print("[F] PASS — 空 reason → fallback「未知原因」（無 broken 中文）")


def case_g_url_reason():
    calls, _ = _run_with_tmp_marker(
        "reason: 您的密碼已過期，請至 https://evil.example/login 重新登入\n"
    )
    assert len(calls) == 1
    msg, _ = calls[0]
    assert "https" not in msg, f"URL reason 必須 fallback；got {msg!r}"
    assert "evil.example" not in msg
    assert "未知原因" in msg
    print("[G] PASS — reason 含 URL → fallback（防 marker 偽造釣魚）")


def case_h_overlong_reason():
    long_reason = "X" * 500
    calls, _ = _run_with_tmp_marker(f"reason: {long_reason}\n")
    assert len(calls) == 1
    msg, _ = calls[0]
    # 200 字 + 截斷符號 + 模板字 → 不會超過 250
    assert len(msg) < 260, f"toast 訊息過長未截斷；len={len(msg)}"
    assert "…" in msg
    print("[H] PASS — reason 超長 → 截斷至 200 字 + 「…」")


def case_i_unlink_permission_error():
    calls, _ = _run_with_tmp_marker(
        "reason: 安裝失敗\n",
        fake_unlink_error=True,
    )
    assert len(calls) == 1, f"unlink 失敗仍要 toast；got {calls}"
    print("[I] PASS — unlink PermissionError 被吞、仍 toast")


def main():
    cases = [
        case_a_marker_with_reason,
        case_b_marker_missing_reason,
        case_c_no_marker,
        case_d_unreadable_marker,
        case_e_env_disabled,
        case_f_empty_reason,
        case_g_url_reason,
        case_h_overlong_reason,
        case_i_unlink_permission_error,
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
        for name, err in failures:
            print(f"  - {name}: {err}")
        sys.exit(1)
    print(f"ALL PASSED: {len(cases)}/{len(cases)}")


if __name__ == "__main__":
    main()
