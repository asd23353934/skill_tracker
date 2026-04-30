"""
把 verify_sandbox_screenshot.ps1 截下的 PNG 拼成單一 GIF / 縮圖網格

執行：
    python verify_sandbox_screenshot_to_gif.py

輸出：
    sandbox_test_shots/timeline.gif       — 全部時序動畫（每幀 1.5 秒）
    sandbox_test_shots/timeline_grid.png  — 4xN 縮圖網格（一張靜態總覽）
"""
import sys
from pathlib import Path
from PIL import Image

SHOTS_DIR = Path(r"C:\Temp\sandbox_test_shots")
GIF_DURATION_MS = 1500
GRID_THUMB_W = 320      # 每張縮圖寬
GRID_COLS = 4
GRID_GAP = 8


def main():
    if not SHOTS_DIR.exists():
        print(f"FAIL: {SHOTS_DIR} 不存在 — 先跑 verify_sandbox_screenshot.ps1")
        sys.exit(1)

    pngs = sorted(SHOTS_DIR.glob("shot_*.png"))
    if not pngs:
        print(f"FAIL: {SHOTS_DIR} 內沒有 PNG")
        sys.exit(1)
    print(f"找到 {len(pngs)} 張截圖")

    # GIF
    print("產生 GIF...")
    frames = [Image.open(p).convert("RGB") for p in pngs]
    # 縮 50% 減小 GIF 體積（原 1080p 太肥）
    target = (frames[0].width // 2, frames[0].height // 2)
    frames_small = [f.resize(target, Image.Resampling.LANCZOS) for f in frames]
    gif_path = SHOTS_DIR / "timeline.gif"
    frames_small[0].save(
        gif_path,
        save_all=True,
        append_images=frames_small[1:],
        duration=GIF_DURATION_MS,
        loop=0,
        optimize=True,
    )
    print(f"  -> {gif_path}  ({gif_path.stat().st_size / 1024 / 1024:.1f} MB)")

    # Grid (4 cols × N rows)
    print("產生縮圖網格...")
    aspect = frames[0].height / frames[0].width
    thumb_h = int(GRID_THUMB_W * aspect)
    rows = (len(pngs) + GRID_COLS - 1) // GRID_COLS
    grid_w = GRID_COLS * GRID_THUMB_W + (GRID_COLS - 1) * GRID_GAP
    grid_h = rows * thumb_h + (rows - 1) * GRID_GAP
    grid = Image.new("RGB", (grid_w, grid_h), color=(20, 20, 28))
    for idx, frame in enumerate(frames):
        thumb = frame.resize((GRID_THUMB_W, thumb_h), Image.Resampling.LANCZOS)
        col = idx % GRID_COLS
        row = idx // GRID_COLS
        x = col * (GRID_THUMB_W + GRID_GAP)
        y = row * (thumb_h + GRID_GAP)
        grid.paste(thumb, (x, y))
    grid_path = SHOTS_DIR / "timeline_grid.png"
    grid.save(grid_path, optimize=True)
    print(f"  -> {grid_path}  ({grid_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print()
    print("DONE")


if __name__ == "__main__":
    main()
