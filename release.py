#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
發布單一入口 — 這是唯一一條打包路徑

    python release.py

從前置檢查一路跑到產出 ZIP，中間沒有需要人工介入的步驟，也沒有第二條路可走。
之所以做成單一入口，是因為 v4.10.2 的事故正是「流程分散成多個腳本、沒人說得清
該跑哪幾個、順序為何」造成的 —— 開發者在 dist/ 跑過 exe 驗證（正確的習慣），
生成的 config_user.json 就被打包進 ZIP，使用者一更新設定全被覆蓋成預設值。

流程：
    1. 前置檢查      資源齊全、.ps1 帶 BOM、沒有殘留備份檔
    2. strip config  config.json 的 user 可變區重設為出廠預設
    3. build         PyInstaller
    4. restore       還原 config.json（**保證執行**，build 失敗也會還原）
    5. zip           排除所有使用者資料，壓完回讀驗證

選項：
    --no-build       跳過 PyInstaller，直接用現有 dist/ 重新打包
                     （改了 zip 邏輯、或只想重壓一次時用）
"""

import argparse
import os
import subprocess
import sys

from zip_release import is_user_data

STRIP_SCRIPT = os.path.join("scripts", "strip_config_for_release.py")
CONFIG_BACKUP = "config.json.dev_backup"
DIST_DIR = os.path.join("dist", "skill_tracker")


def _run(args: list[str], label: str) -> bool:
    """跑一個子命令，回傳是否成功（輸出直接透傳到終端）"""
    print(f"\n$ {' '.join(args)}")
    result = subprocess.run(args)
    if result.returncode != 0:
        print(f"\n❌ {label} 失敗（exit {result.returncode}）")
        return False
    return True


# ════════════════════════════════════════════════════════════
# 1. 前置檢查
# ════════════════════════════════════════════════════════════

def check_images() -> bool:
    """images/ 需有圖示（打包資源）"""
    if not os.path.isdir("images"):
        print("  ❌ images/ 不存在")
        return False
    count = len([f for f in os.listdir("images") if f.lower().endswith(".png")])
    if count == 0:
        print("  ❌ images/ 沒有任何 .png 圖示")
        return False
    print(f"  ✅ images/ 共 {count} 個圖示")
    return True


def check_icon() -> bool:
    """icon.ico 需存在（exe 圖示）"""
    if not os.path.exists("icon.ico"):
        print("  ❌ icon.ico 不存在")
        return False
    print(f"  ✅ icon.ico ({os.path.getsize('icon.ico')} bytes)")
    return True


def check_overlays() -> bool:
    """overlays/ 需存在，PyInstaller spec 才打包得到（缺就建空的）"""
    if not os.path.isdir("overlays"):
        os.makedirs("overlays")
        print("  ✅ overlays/ 不存在，已建立空目錄")
        return True
    count = len([f for f in os.listdir("overlays")
                 if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"))])
    print(f"  ✅ overlays/ 共 {count} 個圖片")
    return True


def check_ps1_bom() -> bool:
    """所有 .ps1 都要帶 UTF-8 BOM

    PS 5.1 預設用系統 ANSI codepage 讀檔，含中文的 .ps1 缺 BOM 會 silent parse
    fail（整段 block 被跳過且不報錯）。實機升級必踩雷，編輯器偶爾會 strip 掉。
    """
    targets = []
    for sub in (".", "scripts"):
        if os.path.isdir(sub):
            for name in sorted(os.listdir(sub)):
                if name.endswith(".ps1"):
                    targets.append(name if sub == "." else os.path.join(sub, name))

    ok = True
    for path in targets:
        with open(path, "rb") as f:
            head = f.read(3)
        if head == b"\xef\xbb\xbf":
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path} 缺 UTF-8 BOM（前 3 bytes: {head.hex()}）")
            ok = False
    return ok


def check_no_stale_backup() -> bool:
    """不可有殘留的 config.json.dev_backup

    存在代表上一次 release 沒跑完 restore，此時 config.json 內容是 stripped 版；
    直接往下跑會把出廠預設當成開發者的設定備份掉，覆水難收。
    """
    if os.path.exists(CONFIG_BACKUP):
        print(f"  ❌ 發現殘留備份 {CONFIG_BACKUP}")
        print("     代表上次發布沒有完成還原，config.json 可能是 stripped 狀態。")
        print(f"     請先確認 config.json 內容，再執行："
              f" python {STRIP_SCRIPT} --restore")
        return False
    print(f"  ✅ 沒有殘留的 {CONFIG_BACKUP}")
    return True


def check_dist_user_data() -> bool:
    """掃描 dist/ 內的使用者資料，僅提示不阻擋

    在 dist/ 跑過 exe 驗證是**應該做**的事，程式會就地生成這些檔。zip 階段會
    自動排除，這裡先講出來，讓人知道待會兒被排除的是什麼、而不是默默消失。
    """
    if not os.path.isdir(DIST_DIR):
        print("  ⏭️  dist/ 尚未建立，略過")
        return True

    # 重用 zip 階段的同一支判定，避免兩處規則漂移（手抄版本會漏掉 .bak 之類的規則）
    found = []
    for root, _dirs, files in os.walk(DIST_DIR):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), DIST_DIR)
            if is_user_data(rel):
                found.append(rel.replace("\\", "/"))

    if found:
        print(f"  ℹ️  dist/ 內有 {len(found)} 個使用者資料檔（打包時會自動排除）：")
        for rel in found[:10]:
            print(f"      - {rel}")
        if len(found) > 10:
            print(f"      … 其餘 {len(found) - 10} 個")
    else:
        print("  ✅ dist/ 內沒有使用者資料")
    return True


def preflight() -> bool:
    """跑完所有前置檢查，回傳是否全部通過"""
    print("=" * 55)
    print("🔍 [1/5] 前置檢查")
    print("=" * 55)

    checks = {
        "images/":        check_images(),
        "icon.ico":       check_icon(),
        "overlays/":      check_overlays(),
        ".ps1 BOM":       check_ps1_bom(),
        "殘留備份":       check_no_stale_backup(),
        "dist/ 使用者資料": check_dist_user_data(),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        print(f"\n❌ 前置檢查未通過：{', '.join(failed)}")
        return False
    print("\n✅ 前置檢查全數通過")
    return True


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-build", action="store_true",
                        help="跳過 PyInstaller，用現有 dist/ 直接重新打包")
    args = parser.parse_args()

    try:
        from version import get_version
        version = get_version()
    except Exception as e:
        print(f"❌ 無法讀取 version.py: {e}")
        return 1

    print()
    print("=" * 55)
    print(f"📦 技能追蹤器 — 發布 v{version}")
    print("=" * 55)

    if not preflight():
        return 1

    # ── strip：config.json 的 user 可變區重設為出廠預設 ──
    print()
    print("=" * 55)
    print("🧹 [2/5] strip config.json（user 可變區 → 出廠預設）")
    print("=" * 55)
    if not _run([sys.executable, STRIP_SCRIPT], "strip config"):
        return 1

    # strip 之後無論如何都要還原，否則 config.json 會留在 stripped 狀態被 commit
    try:
        if args.no_build:
            print()
            print("=" * 55)
            print("⏭️  [3/5] 跳過 PyInstaller（--no-build）")
            print("=" * 55)
            if not os.path.isdir(DIST_DIR):
                print(f"❌ {DIST_DIR} 不存在，--no-build 無檔可打包")
                return 1
        else:
            print()
            print("=" * 55)
            print("🔨 [3/5] PyInstaller build")
            print("=" * 55)
            # --noconfirm：dist/ 非空時不跳互動確認直接覆蓋。
            # 順帶清掉上次在 dist/ 跑 exe 驗證時生成的使用者資料，不留殘骸。
            if not _run([sys.executable, "-m", "PyInstaller", "--noconfirm",
                         "skill_tracker.spec"], "PyInstaller build"):
                return 1
    finally:
        print()
        print("=" * 55)
        print("♻️  [4/5] 還原 config.json")
        print("=" * 55)
        _run([sys.executable, STRIP_SCRIPT, "--restore"], "restore config")

    # ── zip：排除使用者資料 + 壓完回讀驗證 ──
    print()
    print("=" * 55)
    print("📦 [5/5] 壓縮發布 ZIP")
    print("=" * 55)
    if not _run([sys.executable, "zip_release.py"], "zip release"):
        return 1

    print()
    print("=" * 55)
    print(f"🎉 發布完成 — dist/skill_tracker_v{version}.zip")
    print("=" * 55)
    print("   下一步：上傳到 GitHub Release，tag 為 v" + version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
