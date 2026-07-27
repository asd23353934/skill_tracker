#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包後壓縮腳本
將 dist/skill_tracker/ 壓縮為 ZIP 發布檔案
"""

import os
import re
import shutil
import sys
import zipfile

from src.infrastructure.helpers import USER_DATA_DIRS, USER_DATA_FILES


# ── 絕不可打包的使用者資料 ──
# 開發者在 dist/ 跑過 exe 驗證時，程式會就地生成這些檔。它們一旦進了 ZIP，
# update_launcher 解壓時會以「覆寫」語意蓋掉使用者本機的同名檔，把設定、配置、
# 練功紀錄全部打回預設值（v4.10.2 即因 _internal/config_user.json 進 ZIP 而發生）。
#
# 清單的單一來源在 helpers.py（緊鄰產生這些路徑的 user_data_path），新增 user
# 檔只需改那一處；這裡不另立一份，避免兩份清單漂移又重演同一個 bug。
_EXCLUDE_FILES = USER_DATA_FILES
_EXCLUDE_DIRS = USER_DATA_DIRS
_EXCLUDE_SUFFIXES = (".bak",)


def is_user_data(rel_path: str) -> bool:
    """判斷 dist 內的相對路徑是否為使用者資料（不可打包）

    以 basename / 路徑 component 比對，因此 `_internal/` 內與 exe 同層的
    同名檔案都會被攔下（歷史版本兩處都寫過）。

    Args:
        rel_path: 相對於 dist/skill_tracker/ 的路徑

    Returns:
        True 表示屬於使用者資料，應排除
    """
    parts = rel_path.replace("\\", "/").split("/")
    if parts[-1] in _EXCLUDE_FILES:
        return True
    if parts[-1].endswith(_EXCLUDE_SUFFIXES):
        return True
    return any(p in _EXCLUDE_DIRS for p in parts[:-1])


def get_version() -> str:
    """從 version.py 讀取版本號"""
    try:
        with open("version.py", "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'VERSION = "([^"]+)"', content)
        return match.group(1) if match else "unknown"
    except Exception as e:
        print(f"  ⚠️  無法讀取 version.py: {e}")
        return "unknown"


def zip_release() -> int:
    """壓縮 dist/skill_tracker/ 為 ZIP

    Returns:
        0 成功, 1 失敗
    """
    version = get_version()
    src_dir = os.path.join("dist", "skill_tracker")
    zip_name = f"skill_tracker_v{version}.zip"
    zip_path = os.path.join("dist", zip_name)

    print("=" * 55)
    print("📦 skill_tracker - 壓縮發布")
    print("=" * 55)
    print()
    print(f"  版本:   v{version}")
    print(f"  來源:   {src_dir}")
    print(f"  目標:   {zip_path}")
    print()

    # 確認來源目錄存在
    if not os.path.isdir(src_dir):
        print(f"❌ 找不到打包目錄: {src_dir}")
        print("   請先執行: pyinstaller skill_tracker.spec")
        return 1

    # ── overlays：複製到 exe 同層（使用者資料，不放 _internal/）──
    src_overlays = "overlays"
    dest_overlays = os.path.join(src_dir, "overlays")
    if os.path.isdir(src_overlays):
        if os.path.exists(dest_overlays):
            shutil.rmtree(dest_overlays)
        shutil.copytree(src_overlays, dest_overlays)
        overlay_count = sum(len(f) for _, _, f in os.walk(src_overlays))
        print(f"  🖼️  已複製 overlays/ → {dest_overlays}（{overlay_count} 個檔案）")
    else:
        os.makedirs(dest_overlays, exist_ok=True)
        print(f"  🖼️  overlays/ 不存在，已在 dist 建立空目錄")

    # ── sounds：複製或生成到 exe 同層（使用者資料，不放 _internal/）──
    src_sounds = "sounds"
    dest_sounds = os.path.join(src_dir, "sounds")
    if os.path.isdir(src_sounds):
        # 開發環境已有 sounds/（含內建 + 使用者自訂）→ 直接複製
        if os.path.exists(dest_sounds):
            shutil.rmtree(dest_sounds)
        shutil.copytree(src_sounds, dest_sounds)
        sounds_count = sum(len(f) for _, _, f in os.walk(src_sounds))
        print(f"  🔊  已複製 sounds/ → {dest_sounds}（{sounds_count} 個檔案）")
    else:
        # sounds/ 尚未生成 → 直接在 dist 裡生成內建音效
        os.makedirs(dest_sounds, exist_ok=True)
        try:
            from src.infrastructure.sound_manager import BUILTIN_SOUNDS, _generate_wav
            for filename, info in BUILTIN_SOUNDS.items():
                _generate_wav(os.path.join(dest_sounds, filename), info["tones"])
            print(f"  🔊  sounds/ 不存在，已在 dist 生成內建音效（{len(BUILTIN_SOUNDS)} 個）")
        except Exception as e:
            # 靜默失敗會讓發出去的 ZIP 內 sounds/ 是空的（使用者完全沒有提示音），
            # 所以這裡不吞掉 —— 直接讓 zip_release 失敗，逼人處理
            print(f"  ❌ 無法生成內建音效: {e}")
            raise
    # ── update_launcher：複製到 exe 同層（程式去 exe 旁找，不在 _internal/）──
    for launcher_name in ("update_launcher.ps1", "update_launcher.bat"):
        src_launcher = launcher_name
        dest_launcher = os.path.join(src_dir, launcher_name)
        if os.path.exists(src_launcher):
            shutil.copy2(src_launcher, dest_launcher)
            # PS 5.1 必需 UTF-8 BOM 才能正確 parse 中文 .ps1，否則 [3/4] block
            # 整段 silent skip。Edit 工具偶爾會 strip BOM，build pipeline 主動補。
            if launcher_name.endswith(".ps1"):
                with open(dest_launcher, "rb") as f:
                    content = f.read()
                if not content.startswith(b"\xef\xbb\xbf"):
                    with open(dest_launcher, "wb") as f:
                        f.write(b"\xef\xbb\xbf" + content)
                    print(f"  📝  {launcher_name} 補 UTF-8 BOM")
            print(f"  🔧  已複製 {launcher_name} → {dest_launcher}")
        else:
            print(f"  ⚠️  找不到 {launcher_name}，跳過")
    print()

    # 若舊 ZIP 存在先刪除
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"  🗑️  已刪除舊版 {zip_name}")

    # 先分出「要壓的」與「使用者資料」，進度分母才會是真的壓縮檔數
    to_compress: list[str] = []
    skipped: list[str] = []
    for root, _dirs, files in os.walk(src_dir):
        for filename in sorted(files):
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, src_dir)
            # 使用者資料絕不進 ZIP（否則更新解壓會覆蓋掉使用者本機設定）
            if is_user_data(rel_path):
                skipped.append(rel_path.replace("\\", "/"))
            else:
                to_compress.append(full_path)

    total_files = len(to_compress)
    print(f"  🔍 共 {total_files} 個檔案，壓縮中...")

    # 大小統計與壓縮走同一份清單，不再重走一次目錄樹
    src_bytes = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for compressed, full_path in enumerate(to_compress, start=1):
            # arcname 保留 "skill_tracker/..." 結構（相對於 dist/）
            zf.write(full_path, os.path.relpath(full_path, "dist"))
            src_bytes += os.path.getsize(full_path)
            if compressed % 50 == 0:
                print(f"    {compressed}/{total_files}...")

    if skipped:
        print()
        print(f"  🛡️  已排除 {len(skipped)} 個使用者資料檔（不進 ZIP）：")
        for rel in skipped:
            print(f"      - {rel}")

    # ── 最後防線：回讀 ZIP 內實際 entry 名稱，確認沒有使用者資料混入 ──
    # 驗的是最終產物，擋「打包迴圈的路徑判斷寫錯」（relpath 算錯、skip 分支沒生效）。
    # 刻意重用 is_user_data 而非手抄一份判定 —— 手抄的版本漏過 .bak 規則，
    # 「獨立實作」反而製造破洞；清單本身共用 USER_DATA_*，齊不齊才是真防線。
    with zipfile.ZipFile(zip_path, "r") as zf:
        leaked = [n for n in zf.namelist() if is_user_data(n)]
    if leaked:
        print()
        print("❌ ZIP 內含使用者資料，已中止發布：")
        for name in leaked:
            print(f"   - {name}")
        print("   這些檔案會在使用者更新時覆蓋掉他們的個人設定。")
        os.remove(zip_path)
        return 1

    # 統計結果（src_bytes 已在壓縮迴圈中累加，不重走目錄樹）
    zip_bytes = os.path.getsize(zip_path)
    ratio = (1 - zip_bytes / src_bytes) * 100 if src_bytes > 0 else 0

    print()
    print("✅ 壓縮完成！")
    print(f"   原始大小: {src_bytes / 1024 / 1024:.1f} MB")
    print(f"   ZIP 大小: {zip_bytes / 1024 / 1024:.1f} MB  (壓縮率 {ratio:.0f}%)")
    print(f"   輸出路徑: {zip_path}")
    print()
    print("🚀 發布準備完成！")
    print(f"   建議上傳: dist/{zip_name}")
    return 0


if __name__ == "__main__":
    sys.exit(zip_release())
