"""Simplest battery wiring: battery -> TP4056 -> switch -> ESP32 5V / GND (no boost), big and numbered.

Shows the ESP32's top pin row near the USB-C port enlarged, with pins counted from the USB end.
Kurdish (Badini) text. Output: images/battery_simple_esp32.png
Usage: python3 tools/draw_battery_simple_esp32.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "battery_simple_esp32.png"
W, H = 1080, 2060
BG = (252, 252, 248)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
TP_BLUE = (30, 80, 170)
PAD = (235, 200, 90)
BOARD = (28, 28, 32)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def wire(pts, color):
    d.line(pts, fill=color, width=18, joint="curve")


def dot(x, y, color=PAD, r=14):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=INK, width=3)


def badge(x, y, n, color):
    d.ellipse([x - 38, y - 38, x + 38, y + 38], fill=(255, 255, 255), outline=color, width=8)
    en(x, y - 28, str(n), 50, color)


# ---------------- Title ----------------
ku(W / 2, 24, "باتری بۆ ESP32", 64)
ku(W / 2, 112, "ب ساناهیترین ڕێک", 32, GREY)

# ---------------- Battery (top) ----------------
BX0, BY0, BX1, BY1 = 300, 200, 780, 360
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=20, fill=(40, 40, 44), outline=INK, width=5)
ku((BX0 + BX1) / 2, BY0 + 34, "باتری", 46, (255, 255, 255))
en((BX0 + BX1) / 2, BY0 + 100, "3.6V", 32, (230, 230, 230))
en(BX1 - 50, BY0 + 30, "+", 64, RED)
en(BX0 + 50, BY0 + 22, "-", 74, (255, 255, 255))
BAT_P, BAT_M = (BX1, BY0 + 80), (BX0, BY0 + 80)

# ---------------- TP4056 ----------------
TX0, TY0, TX1, TY1 = 300, 500, 780, 740
d.rounded_rectangle([TX0, TY0, TX1, TY1], radius=20, fill=TP_BLUE, outline=INK, width=5)
en((TX0 + TX1) / 2, TY0 + 86, "TP4056", 46, (255, 255, 255))
d.rounded_rectangle([(TX0 + TX1) / 2 - 56, TY0 + 156, (TX0 + TX1) / 2 + 56, TY0 + 200], radius=10,
                    fill=(200, 200, 205), outline=INK, width=3)
TP_BP, TP_BM = (TX1, TY0 + 50), (TX0, TY0 + 50)
TP_OP, TP_OM = (TX0, TY1 - 50), (TX1, TY1 - 50)   # OUT+ left, OUT- right: no crossing below
for (x, y), n, anc, dx in ((TP_BP, "B+", "ra", -22), (TP_BM, "B-", "la", 22),
                           (TP_OP, "OUT+", "la", 22), (TP_OM, "OUT-", "ra", -22)):
    dot(x, y)
    en(x + dx, y - 16, n, 30, (255, 255, 255), anc)

RX, LX = 900, 180
wire([BAT_P, (RX, BAT_P[1]), (RX, TP_BP[1]), TP_BP], RED)
wire([BAT_M, (LX, BAT_M[1]), (LX, TP_BM[1]), TP_BM], BLACK)
badge(RX, (BAT_P[1] + TP_BP[1]) / 2, 1, RED)
badge(LX, (BAT_M[1] + TP_BM[1]) / 2, 2, BLACK)

# ---------------- Switch ----------------
SY0, SY1 = 820, 940
d.rounded_rectangle([LX - 66, SY0, LX + 66, SY1], radius=14, fill=(220, 40, 40), outline=INK, width=5)
d.rectangle([LX - 40, SY0 + 26, LX + 40, SY1 - 26], fill=(170, 20, 20), outline=INK, width=3)
ku(LX + 90, SY0 + 34, "سویچ", 38, INK, anchor="la")
wire([TP_OP, (LX, TP_OP[1]), (LX, SY0)], RED)
badge(LX + 100, (TP_OP[1] + SY0) / 2 + 10, 3, RED)

# ---------------- ESP32: the top pin row near USB-C, enlarged ----------------
EX0, EY0, EX1, EY1 = 40, 1110, 1040, 1420
d.rounded_rectangle([EX0, EY0, EX1, EY1], radius=20, fill=BOARD, outline=INK, width=5)
d.rounded_rectangle([EX0 - 24, EY0 + 150, EX0 + 70, EY0 + 260], radius=12, fill=(190, 190, 195), outline=INK, width=4)
en(EX0 + 90, EY0 + 186, "USB-C", 28, (200, 200, 205), "la")
en(860, EY0 + 200, "ESP32", 46, (200, 200, 205))
en(EX1 - 30, EY0 + 260, "...", 40, (150, 150, 155), "ra")

names = ["5V", "CMD", "SD3", "SD2", "13", "GND", "12"]
PX0, PITCH = 110, 135
PY = EY0 + 40
pin_x = {}
for i, n in enumerate(names):
    x = PX0 + i * PITCH
    dot(x, PY, (200, 170, 70), 18)
    if n == "5V":
        d.rounded_rectangle([x - 40, PY + 30, x + 40, PY + 76], radius=8, fill=RED)
    elif n == "GND":
        d.rounded_rectangle([x - 50, PY + 30, x + 50, PY + 76], radius=8, fill=(90, 90, 95))
    en(x, PY + 36, n, 30, (255, 255, 255))
    # count from the USB end
    en(x, PY + 90, str(i + 1), 26, (160, 160, 165))
    pin_x[n] = x

# switch -> 5V (wire 4), TP OUT- -> GND (wire 5)
wire([(LX, SY1), (LX, 1020), (pin_x["5V"], 1020), (pin_x["5V"], PY - 18)], RED)
badge(LX + 70, 1020, 4, RED)
wire([TP_OM, (RX, TP_OM[1]), (RX, 1040), (pin_x["GND"], 1040), (pin_x["GND"], PY - 18)], BLACK)
badge(RX, (TP_OM[1] + 1040) / 2, 5, BLACK)

# ---------------- Legend ----------------
LY = 1470
d.rounded_rectangle([40, LY, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
rows = [
    (1, RED, "باتری +", "TP4056 B+"),
    (2, BLACK, "باتری -", "TP4056 B-"),
    (3, RED, "TP4056 OUT+", "سویچ"),
    (4, RED, "سویچ", "ESP32 5V  (1)"),
    (5, BLACK, "TP4056 OUT-", "ESP32 GND  (6)"),
]


def any_text(x, y, text, size, color, anchor):
    if text[0].isascii():
        en(x, y, text, size, color, anchor)
    else:
        ku(x, y, text, size, color, anchor)


for k, (n, c, src, dst) in enumerate(rows):
    y = LY + 30 + k * 80
    d.ellipse([W - 126, y, W - 70, y + 56], fill=c)
    en(W - 98, y + 8, str(n), 32, (255, 255, 255))
    any_text(W - 146, y + 12, src, 30, INK, "ra")
    en(500, y + 8, "←", 36, c, "ma")
    any_text(450, y + 12, dst, 30, INK, "ra")

ny = LY + 30 + len(rows) * 80 + 4
d.line([(80, ny), (W - 80, ny)], fill=(220, 220, 220), width=2)
ku(W - 80, ny + 14, "⚠ بێ Boost، تنێ دەمێ باتری تژی بیت باش کار دکەت", 26, RED, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
