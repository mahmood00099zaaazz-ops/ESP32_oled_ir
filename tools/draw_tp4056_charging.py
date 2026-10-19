"""How to charge one 18650 cell with a TP4056 module - Kurdish (Badini) labels.

Output: images/tp4056_charging.png   Usage: python3 tools/draw_tp4056_charging.py
(needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "tp4056_charging.png"
W, H = 1080, 1800
BG = (250, 250, 246)
INK = (25, 25, 30)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
GREY = (95, 95, 95)
BLUE_PCB = (30, 70, 160)
PINK = (235, 120, 170)
GREEN = (25, 145, 65)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=40, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=40, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def wire(pts, color, w=14):
    d.line(pts, fill=color, width=w, joint="curve")


def dot(x, y, color, r=14):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color)


# ---------------- Title ----------------
ku(W / 2, 30, "شارژکرنا باتریێ", 64)
en(W / 2, 112, "TP4056 + 1x 18650", 44, GREY)

# ---------------- Phone charger + cable ----------------
d.rounded_rectangle([60, 230, 260, 430], radius=24, fill=(245, 245, 245), outline=INK, width=5)
for px in (120, 200):
    d.rectangle([px - 8, 190, px + 8, 232], fill=(190, 190, 190), outline=INK, width=2)
ku(160, 280, "شارژەرێ", 36)
ku(160, 330, "مۆبایلێ", 36)
en(160, 380, "5V 1A", 30, GREY)
# cable
wire([(160, 430), (160, 560), (330, 560)], (60, 60, 60), 20)
d.rounded_rectangle([330, 535, 400, 585], radius=8, fill=(40, 40, 40))
en(365, 600, "USB", 26, GREY)

# ---------------- TP4056 board ----------------
BX0, BY0, BX1, BY1 = 400, 470, 760, 660
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=10, fill=BLUE_PCB, outline=INK, width=5)
d.rounded_rectangle([BX0 - 10, BY0 + 65, BX0 + 40, BY0 + 125], radius=6, fill=(200, 200, 205), outline=INK, width=3)
d.rectangle([BX0 + 110, BY0 + 70, BX0 + 190, BY0 + 140], fill=(20, 20, 20))
en(BX0 + 150, BY0 + 150, "TP4056", 24, (220, 230, 255))
# LEDs
d.ellipse([BX0 + 80, BY0 + 18, BX0 + 106, BY0 + 44], fill=(255, 60, 60), outline=INK, width=2)
d.ellipse([BX0 + 130, BY0 + 18, BX0 + 156, BY0 + 44], fill=(70, 140, 255), outline=INK, width=2)
# pads on the right
pads = [("OUT+", BY0 + 25, (210, 210, 210)), ("B+", BY0 + 75, RED), ("B-", BY0 + 120, BLACK), ("OUT-", BY0 + 165, (210, 210, 210))]
for name, y, c in pads:
    d.rectangle([BX1 - 30, y - 14, BX1 - 4, y + 14], fill=(230, 200, 90), outline=INK, width=2)
    en(BX1 - 40, y - 13, name, 22, (255, 255, 255), anchor="ra")

# ---------------- Battery in a single holder ----------------
HX0, HY0, HX1, HY1 = 880, 300, 1020, 980
d.rounded_rectangle([HX0, HY0, HX1, HY1], radius=16, fill=(35, 35, 38), outline=INK, width=5)
d.rounded_rectangle([HX0 + 18, HY0 + 40, HX1 - 18, HY1 - 40], radius=40, fill=PINK, outline=INK, width=3)
d.rectangle([HX0 + 50, HY0 + 24, HX1 - 50, HY0 + 42], fill=(200, 200, 200), outline=INK, width=2)
en((HX0 + HX1) / 2, HY0 + 70, "+", 70, RED)
en((HX0 + HX1) / 2, HY1 - 140, "-", 80, INK)
en((HX0 + HX1) / 2, (HY0 + HY1) / 2 - 20, "18650", 26, INK)
dot(HX0, HY0 + 110, RED)
dot(HX0, HY1 - 110, BLACK)

# wires B+ -> battery +, B- -> battery -
wire([(BX1 - 4, BY0 + 75), (820, BY0 + 75), (820, HY0 + 110), (HX0, HY0 + 110)], RED)
wire([(BX1 - 4, BY0 + 120), (840, BY0 + 120), (840, HY1 - 110), (HX0, HY1 - 110)], BLACK)
def mixed(x_right, y, kurdish, english, size, color):
    """Kurdish word on the right, English part to its left (drawn separately, so it stays LTR)."""
    ku(x_right, y, kurdish, size, color, anchor="ra")
    kw = d.textlength(kurdish, font=font(size), direction="rtl")
    en(x_right - kw - 16, y, english, size, color, anchor="ra")


mixed(800, 760, "سۆر:", "B+  →  battery +", 32, RED)
mixed(800, 808, "ڕەش:", "B-  →  battery -", 32, BLACK)
mixed(740, 700, "بکار نەئینە", "OUT+ / OUT-", 28, GREY)

# ---------------- LED meaning ----------------
d.rounded_rectangle([40, 1040, W - 40, 1310], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, 1062, "ڕۆناهیا ل سەر پارچێ:", 40, INK, anchor="ra")
d.ellipse([W - 140, 1140, W - 90, 1190], fill=(255, 60, 60), outline=INK, width=3)
ku(W - 170, 1142, "سۆر = شارژ دبیت...", 40, RED, anchor="ra")
d.ellipse([W - 140, 1220, W - 90, 1270], fill=(70, 140, 255), outline=INK, width=3)
ku(W - 170, 1222, "شین = تژی بوو ✓", 40, (40, 100, 220), anchor="ra")

# ---------------- Important note ----------------
d.rounded_rectangle([40, 1340, W - 40, 1760], radius=22, fill=(255, 238, 238), outline=RED, width=4)
ku(W / 2, 1362, "⚠ گرنگ", 46, RED)
lines = [
    "ئەڤ پارچە تنێ ئێک باتریێ شارژ دکەت",
    "باتریان ژ ڕۆبۆتی دەربێخە",
    "و ئێک ب ئێک شارژ بکە",
    "ب جهێ باتریێ یێ دو جهی ڤە گرێ نەدە!",
]
for k, t in enumerate(lines):
    ku(W / 2, 1440 + k * 72, t, 38, INK if k < 3 else RED)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT)
