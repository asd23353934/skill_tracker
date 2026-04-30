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
            from src.ui.sound_manager import BUILTIN_SOUNDS, _generate_wav
            for filename, info in BUILTIN_SOUNDS.items():
                _generate_wav(os.path.join(dest_sounds, filename), info["tones"])
            print(f"  🔊  sounds/ 不存在，已在 dist 生成內建音效（{len(BUILTIN_SOUNDS)} 個）")
        except Exception as e:
            print(f"  ⚠️  無法生成內建音效: {e}，已建立空目錄")
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

    # 計算檔案數量
    total_files = sum(len(files) for _, _, files in os.walk(src_dir))
    print(f"  🔍 共 {total_files} 個檔案，壓縮中...")

    compressed = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, _dirs, files in os.walk(src_dir):
            for filename in sorted(files):
                full_path = os.path.join(root, filename)
                # arcname 保留 "skill_tracker/..." 結構（相對於 dist/）
                arcname = os.path.relpath(full_path, "dist")
                zf.write(full_path, arcname)
                compressed += 1
                if compressed % 50 == 0:
                    print(f"    {compressed}/{total_files}...")

    # 統計結果
    zip_bytes = os.path.getsize(zip_path)
    src_bytes = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _, files in os.walk(src_dir)
        for f in files
    )
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
