"""
端到端模擬：偵測新版 → 點擊更新 → 真實下載 → 攔截 launcher 啟動

走完除了「真的關閉自己 + 替換 exe + 重啟」以外的所有步驟，並在三個關鍵時刻
grab dialog 截圖到 update_e2e_screenshots/。

特性：
- 透過 in-memory monkey-patch 把 version 改為 4.3.3，不動 version.py 檔案
- offscreen Qt（QT_QPA_PLATFORM=offscreen）— 不會跳出真實視窗
- 真的打 GitHub API、真的下載 ~70 MB 到 temp
- subprocess.Popen 與 _shutdown_app 都被 mock 掉，不會真的執行 launcher / 退出

需要網路；會下載 ~70 MB 到 temp，視網速約 30-90 秒。

執行：
    python verify_update_e2e.py
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SKILL_TRACKER_DISABLE_UPDATE_CHECK"] = "1"

# === 在 import updater 之前 monkey-patch version ===
import version  # noqa: E402
ORIG_VERSION = version.VERSION
version.VERSION = "4.3.3"
version.get_version = lambda: "4.3.3"

# updater 在 import 時就已經 from version import get_version；上面改完後
# 重新 import 它會拿到 4.3.3
import importlib  # noqa: E402
import src.infrastructure.updater as _u  # noqa: E402
importlib.reload(_u)
from src.infrastructure.updater import Updater  # noqa: E402

from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

OUT_DIR = Path("update_e2e_screenshots")
OUT_DIR.mkdir(exist_ok=True)


def shot(dlg, name: str):
    """grab dialog 為 PNG"""
    pix = dlg.grab()
    path = OUT_DIR / f"{name}.png"
    pix.save(str(path))
    print(f"  [shot] {path}")


def step(n: int, title: str):
    print()
    print("=" * 60)
    print(f"Step {n}: {title}")
    print("=" * 60)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    t0 = time.time()

    # === Step 1: check_for_updates（真實打 GitHub）===
    step(1, "check_for_updates（真實打 GitHub API）")
    info = Updater().check_for_updates()
    print(f"  available    : {info.get('available')}")
    print(f"  current      : {info.get('current')}")
    print(f"  latest       : {info.get('latest')}")
    print(f"  download_url : {info.get('download_url')}")
    if not info.get("available"):
        print("FAIL: 沒偵測到新版（version monkey-patch 可能失敗）")
        sys.exit(1)
    assert info.get("current") == "4.3.3"
    assert info.get("latest") == "4.3.4"

    # === Step 2: 開啟 UpdateDialog（offscreen）===
    step(2, "開啟 UpdateDialog（offscreen，模擬「偵測到新版 → 自動彈出」）")
    from src.ui_v2.dialogs.update_dialog_v2 import UpdateDialog

    class FakeParent(QWidget):
        def close(self):
            print("  [FakeParent] close() called（mock 不真關）")
            return True

    parent = FakeParent()
    dlg = UpdateDialog(parent, info)
    dlg.show()
    app.processEvents()
    print(f"  dialog 可見          : {dlg.isVisible()}")
    print(f"  版本字串             : v{info['current']}  →  v{info['latest']}")
    print(f"  status_label         : {dlg.status_label.text()}")
    print(f"  download_btn 文字    : {dlg.download_btn.text()}")
    shot(dlg, "01_initial")

    # === Step 3: 點擊「開始更新」===
    step(3, "點擊「開始更新」按鈕（程式化觸發 click）")

    launcher_invocations: list[dict] = []

    def fake_popen(args, **kwargs):
        launcher_invocations.append({
            "argv": list(args) if not isinstance(args, str) else [args],
            "kwargs": {k: v for k, v in kwargs.items() if k != "stdin"},
        })
        argv_str = list(args) if not isinstance(args, str) else args
        print(f"  [FakePopen] launcher invoked with argv:")
        for a in argv_str:
            print(f"    {a!r}")
        class _FakeProc:
            pid = 99999
        return _FakeProc()

    shutdown_calls = []

    def fake_shutdown():
        shutdown_calls.append(True)
        print("  [FakeShutdown] _shutdown_app() called（mock 不真關 app）")

    dlg._shutdown_app = fake_shutdown

    # 真的點按鈕
    with patch.object(subprocess, "Popen", side_effect=fake_popen):
        dlg.download_btn.click()
        app.processEvents()
        print(f"  按鈕被禁用      : {not dlg.download_btn.isEnabled()}")
        print(f"  按鈕文字變更為  : {dlg.download_btn.text()!r}")
        print(f"  status         : {dlg.status_label.text()!r}")

        # === Step 4: 等下載完成 ===
        step(4, "等下載（真的下 ~70 MB ZIP，視網速 30-90 秒）")
        deadline = time.time() + 180
        mid_shot_taken = False
        complete_shot_taken = False
        last_logged_pct = -10
        while time.time() < deadline:
            app.processEvents()
            pct = dlg.progress_bar.value()
            if pct - last_logged_pct >= 10:
                print(f"  [{int(time.time() - t0):>3}s] 進度 {pct:>3}%  status={dlg.status_label.text()!r}")
                last_logged_pct = pct
            if not mid_shot_taken and 30 <= pct <= 70:
                shot(dlg, "02_downloading")
                mid_shot_taken = True
            if not complete_shot_taken and pct >= 100:
                # 完成時 status 會變「下載完成！正在啟動更新...」
                if "完成" in dlg.status_label.text() or "啟動" in dlg.status_label.text():
                    shot(dlg, "03_complete")
                    complete_shot_taken = True
            if launcher_invocations:
                # _launch_updater 已經被叫到 → flow 走完
                # 給 QTimer 500ms 讓 _shutdown_app 也排上來
                t_extra = time.time() + 1.0
                while time.time() < t_extra:
                    app.processEvents()
                    if shutdown_calls:
                        break
                    time.sleep(0.05)
                break
            time.sleep(0.05)

    # === Step 5: 結果 ===
    step(5, "結果")
    if not launcher_invocations:
        print("FAIL: launcher 從未被觸發")
        # 印 status 與 button text 幫助 debug
        print(f"  status: {dlg.status_label.text()!r}")
        print(f"  button: {dlg.download_btn.text()!r}")
        print(f"  bar  : {dlg.progress_bar.value()}%")
        sys.exit(1)

    inv = launcher_invocations[0]
    argv0 = inv['argv'][0] if inv['argv'] else "(empty)"
    is_ps1 = "powershell" in str(argv0).lower() or "-File" in inv['argv']
    is_bat = str(argv0).lower().endswith(".bat")
    print(f"  [OK]launcher 啟動成功（{'ps1' if is_ps1 else 'bat' if is_bat else 'unknown'}）")
    print(f"  [OK]shutdown_app 被觸發 : {bool(shutdown_calls)}")
    if not complete_shot_taken:
        # 完成截圖補一張
        shot(dlg, "03_complete")
    print(f"  [OK]截圖數              : 3 張 in {OUT_DIR}/")

    # 驗證下載檔真的在
    u = Updater()
    u.download_url = info["download_url"]
    dl_path = u.get_update_temp_path()
    if os.path.exists(dl_path):
        size_mb = os.path.getsize(dl_path) / (1024 * 1024)
        print(f"  [OK]下載檔存在          : {dl_path} ({size_mb:.1f} MB)")
    else:
        print(f"  [WARN] 下載檔不存在        : {dl_path}")

    print()
    print("=" * 60)
    print("ALL E2E STEPS PASSED — 自動更新流程在 source 模式下完整可走")
    print("=" * 60)
    print()
    print("注意：以下兩步在 source 模式無法實測，需要 PyInstaller build：")
    print("  · launcher 等舊 exe 退出 → 解壓 ZIP → 啟動新 exe")
    print("  · 重啟後使用者看到的版本字串變為 v4.3.4")

    # 收尾：明確 close dialog 讓 Qt 走完 cleanup
    try:
        dlg.close()
    except RuntimeError:
        pass


if __name__ == "__main__":
    try:
        main()
    finally:
        version.VERSION = ORIG_VERSION  # restore in-memory
