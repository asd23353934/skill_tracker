"""
產生 3 個 buff icon placeholder（generic geometric，非遊戲版權圖）

- 經驗加倍.png — 藍底白楓葉
- 掉寶加倍.png — 粉底白禮物盒
- HT加倍.png    — 藍底白「H」+ 火焰外框

執行：
    python scripts/gen_buff_icons.py
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "images"
SIZE = 32
TARGETS = ("經驗加倍.png", "掉寶加倍.png", "HT加倍.png")


def _rounded_bg(color, radius=6):
    """建立 32x32 圓角矩形背景"""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=radius, fill=color)
    return img


def _maple_leaf(draw, color):
    """簡化版楓葉（5 個尖角的星形抽象）— 中心 (16,16)，半徑 ~10"""
    cx, cy = SIZE // 2, SIZE // 2
    pts = [
        (cx,      cy - 11),  # 上
        (cx + 4,  cy - 4),
        (cx + 11, cy - 3),
        (cx + 6,  cy + 2),
        (cx + 9,  cy + 10),
        (cx,      cy + 5),
        (cx - 9,  cy + 10),
        (cx - 6,  cy + 2),
        (cx - 11, cy - 3),
        (cx - 4,  cy - 4),
    ]
    draw.polygon(pts, fill=color)
    # 莖
    draw.line([(cx, cy + 5), (cx, cy + 12)], fill=color, width=2)


def _gift_box(draw, color):
    """簡化禮物盒：方形 + 緞帶十字"""
    # box body
    draw.rectangle((6, 12, 26, 26), outline=color, width=2)
    # lid
    draw.rectangle((4, 9, 28, 14), fill=color)
    # ribbon vertical
    draw.line([(16, 9), (16, 26)], fill=color, width=2)


def _flame_with_h(draw, fill_color, text_color):
    """藍火焰外框（簡化水滴形）+ 中央白色 H"""
    # flame outline (water-drop-like)
    cx = SIZE // 2
    pts = [
        (cx,      4),
        (cx + 6,  10),
        (cx + 9,  18),
        (cx + 6,  26),
        (cx,      28),
        (cx - 6,  26),
        (cx - 9,  18),
        (cx - 6,  10),
    ]
    draw.polygon(pts, fill=fill_color)
    # 中央 H：用兩條垂直線 + 中央橫線
    draw.line([(11, 12), (11, 24)], fill=text_color, width=2)
    draw.line([(21, 12), (21, 24)], fill=text_color, width=2)
    draw.line([(11, 18), (21, 18)], fill=text_color, width=2)


def gen_exp():
    """產生經驗加倍 placeholder：藍底圓角矩形 + 白色楓葉幾何"""
    img = _rounded_bg("#2C7BE5")  # 楓之谷風藍
    d = ImageDraw.Draw(img)
    _maple_leaf(d, "#FFFFFF")
    img.save(OUT / "經驗加倍.png")
    print("  經驗加倍.png saved")


def gen_drop():
    """產生掉寶加倍 placeholder：粉底圓角矩形 + 白色禮物盒"""
    img = _rounded_bg("#F48FB1")  # 粉
    d = ImageDraw.Draw(img)
    _gift_box(d, "#FFFFFF")
    img.save(OUT / "掉寶加倍.png")
    print("  掉寶加倍.png saved")


def gen_ht():
    """產生 Hot Time placeholder：深藍底 + 中藍火焰 + 白色 H 字"""
    img = _rounded_bg("#0D47A1")  # 深藍底
    d = ImageDraw.Draw(img)
    _flame_with_h(d, "#1976D2", "#FFFFFF")  # 中藍火焰 + 白 H
    img.save(OUT / "HT加倍.png")
    print("  HT加倍.png saved")


def main():
    """主入口：依序產生三個 buff icon placeholder 到 images/

    若三個目標檔已存在（例如使用者已用遊戲精確圖替換），預設不覆蓋；
    傳 `--force` 才覆蓋。避免重跑時把使用者自訂圖蓋回 placeholder。
    """
    OUT.mkdir(exist_ok=True)
    force = "--force" in sys.argv
    existing = [name for name in TARGETS if (OUT / name).exists()]
    if existing and not force:
        print(f"  [skip] 已存在：{', '.join(existing)}")
        print("  若要覆蓋，加 --force 旗標再跑")
        return
    gen_exp()
    gen_drop()
    gen_ht()
    print("DONE — 3 icons generated.")


if __name__ == "__main__":
    main()
