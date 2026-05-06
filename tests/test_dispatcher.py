"""ui.dispatcher Dispatcher 行為測試 — 主要測 S3 修法（_dispatch 包 try/log）"""

import logging
import os
import sys

import pytest

# 強制 Qt 在 headless 模式（CI / 本地皆可）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.ui.dispatcher import Dispatcher  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


# ── S3：_dispatch 包 try/log ───────────────────────────────

def test_dispatch_normal_callback_executes(qapp):
    """正常 callback 應該被執行。"""
    d = Dispatcher(QObject())

    called = {"n": 0}

    def cb():
        called["n"] += 1

    d._dispatch(cb)
    assert called["n"] == 1


def test_dispatch_swallows_callback_exception(qapp, caplog):
    """callback raise 時不該傳染到 Qt event loop，且應寫 log。"""
    d = Dispatcher(QObject())

    def boom():
        raise RuntimeError("intentional")

    # 攔截 logger 確認 log 有寫
    with caplog.at_level(logging.ERROR, logger="src.ui.dispatcher"):
        d._dispatch(boom)   # 不該 raise

    # 確認真的有 log（exception 等級會以 ERROR 出現）
    assert any("Dispatcher" in r.message for r in caplog.records)


def test_dispatch_continues_after_exception(qapp):
    """一次 callback 失敗不該破壞 dispatcher，後續 callback 仍能執行。"""
    d = Dispatcher(QObject())

    def boom():
        raise ValueError("boom")

    flag = {"ran": False}

    def good():
        flag["ran"] = True

    d._dispatch(boom)   # 吞掉
    d._dispatch(good)   # 仍能執行
    assert flag["ran"] is True
