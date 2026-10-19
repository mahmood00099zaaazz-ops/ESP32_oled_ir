"""Battery -> TP4056 -> switch -> boost -> exact pins on a 38-pin USB-C ESP32 board (DevKitC pinout).

Numbered wires 1..7 (same numbers as images/battery_numbered.png), all 38 pins named, Kurdish legend.
Output: images/battery_to_esp32.png
Usage: python3 tools/draw_battery_to_esp32.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "battery_to_esp32.png"
W, H = 1080, 2080
BG = (252, 252, 248)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
GREEN = (25, 145, 65)
TP_BLUE = (30, 80, 170)
BOOST = (40, 120, 200)
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


def wire(pts, color, w=12):
    d.line(pts, fill=color, width=w, joint="curve")


def dot(x, y, color, r=10):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=INK, width=2)


def badge(x, y, n, color):
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=(255, 255, 255), outline=color, width=6)
    en(x, y - 19, str(n), 32, color)


def vtext(x, y_top, text, size, color, bg=None):
    """Vertical (rotated) Latin text whose top is at (x centre, y_top)."""
    f = font(size)
    tw = int(d.textlength(text, font=f)) + 8
    th = size + 8
    layer = Image.new("RGBA", (tw, th), bg + (255,) if bg else (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((4, 2), text, font=f, fill=color)
    layer = layer.rotate(90, expand=True)
    img.paste(layer, (int(x - layer.width / 2), int(y_top)), layer)
    return layer.height


# ---------------- Title ----------------
ku(W / 2, 22, "باتری دچیتە کیژ پینێ؟", 56)
en(W / 2, 100, "ESP32  38 pin  USB-C", 30, GREY)

# ---------------- Battery (top right) ----------------
BX0, BY0, BX1, BY1 = 770, 200, 1030, 400
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=16, fill=(40, 40, 44), outline=INK, width=4)
ku((BX0 + BX1) / 2, BY0 + 40, "باتری", 36, (255, 255, 255))
en((BX0 + BX1) / 2, BY0 + 96, "3.6V 1080mAh", 24, (230, 230, 230))
BAT_P, BAT_M = (BX0, BY0 + 50), (BX0, BY1 - 50)
en(BX0 + 24, BAT_P[1] - 26, "+", 40, RED, "la")
en(BX0 + 26, BAT_M[1] - 30, "-", 46, (255, 255, 255), "la")

# ---------------- TP4056 (top middle) ----------------
TX0, TY0, TX1, TY1 = 440, 200, 680, 420
d.rounded_rectangle([TX0, TY0, TX1, TY1], radius=12, fill=TP_BLUE, outline=INK, width=4)
en((TX0 + TX1) / 2, TY0 + 80, "TP4056", 32, (255, 255, 255))
en((TX0 + TX1) / 2, TY0 + 120, "HW-373", 20, (210, 225, 255))
TP_BP, TP_BM = (TX1, BAT_P[1]), (TX1, BAT_M[1])
TP_OP, TP_OM = (TX0, TY0 + 50), (TX0, TY1 - 50)
for (x, y), n, anc, dx in ((TP_BP, "B+", "ra", -14), (TP_BM, "B-", "ra", -14),
                           (TP_OP, "OUT+", "la", 14), (TP_OM, "OUT-", "la", 14)):
    dot(x, y, PAD)
    en(x + dx, y - 13, n, 22, (255, 255, 255), anc)
wire([BAT_P, TP_BP], RED)
wire([BAT_M, TP_BM], BLACK)
badge((TX1 + BX0) / 2, BAT_P[1] - 44, 1, RED)
badge((TX1 + BX0) / 2, BAT_M[1] + 44, 2, BLACK)

# ---------------- Switch ----------------
SWX, SWY = 340, TP_OP[1]
d.rounded_rectangle([SWX - 46, SWY - 34, SWX + 46, SWY + 34], radius=10, fill=(220, 40, 40), outline=INK, width=4)
ku(SWX, SWY - 86, "سویچ", 28)
wire([TP_OP, (SWX + 46, SWY)], RED)
badge((TP_OP[0] + SWX + 46) / 2, SWY + 44, 3, RED)

# ---------------- Boost (left, above the 5V pin) ----------------
UX0, UY0, UX1, UY1 = 60, 470, 330, 640
d.rounded_rectangle([UX0, UY0, UX1, UY1], radius=12, fill=BOOST, outline=INK, width=4)
en((UX0 + UX1) / 2, UY0 + 52, "Boost 5V", 30, (255, 255, 255))
en((UX0 + UX1) / 2, UY0 + 90, "MT3608", 20, (220, 235, 255))
IN_P, IN_M = (180, UY0), (290, UY0)
for (x, y), n in ((IN_P, "IN+"), (IN_M, "IN-")):
    dot(x, y, PAD)
    en(x, y + 14, n, 20, (255, 255, 255))

# ---------------- ESP32 board (38 pins, USB-C on the LEFT) ----------------
EX0, EY0, EX1, EY1 = 50, 780, 1030, 1200
d.rounded_rectangle([EX0, EY0, EX1, EY1], radius=16, fill=BOARD, outline=INK, width=4)
# USB-C + buttons on the left, metal module on the right
d.rounded_rectangle([EX0 - 20, 950, EX0 + 50, 1030], radius=10, fill=(190, 190, 195), outline=INK, width=3)
en(EX0 + 70, 974, "USB-C", 20, (200, 200, 205), "la")
d.rounded_rectangle([700, 935, 990, 1045], radius=8, fill=(185, 185, 190), outline=INK, width=3)
en(845, 970, "ESP-32", 30, (60, 60, 60))

PIN_X0, PITCH = 110, (970 - 110) / 18
top = ["5V", "CMD", "SD3", "SD2", "13", "GND", "12", "14", "27", "26", "25",
       "33", "32", "35", "34", "VN", "VP", "EN", "3V3"]
bottom = ["CLK", "SD0", "SD1", "15", "2", "0", "4", "16", "17", "5", "18",
          "19", "GND", "21", "RX", "TX", "22", "23", "GND"]
TOP_Y, BOT_Y = EY0 + 26, EY1 - 26


def label_style(name):
    if name == "5V":
        return (255, 255, 255), RED
    if name == "GND":
        return (255, 255, 255), (90, 90, 95)
    if name == "3V3":
        return (255, 255, 255), (140, 60, 160)
    return (215, 215, 220), None


pin_x = {}
for i, name in enumerate(top):
    x = PIN_X0 + i * PITCH
    d.ellipse([x - 11, TOP_Y - 11, x + 11, TOP_Y + 11], fill=(200, 170, 70), outline=INK, width=2)
    fg, bg = label_style(name)
    vtext(x, TOP_Y + 18, name, 18, fg, bg)
    pin_x[("top", name)] = x
for i, name in enumerate(bottom):
    x = PIN_X0 + i * PITCH
    d.ellipse([x - 11, BOT_Y - 11, x + 11, BOT_Y + 11], fill=(200, 170, 70), outline=INK, width=2)
    fg, bg = label_style(name)
    h = int(d.textlength(name, font=font(18))) + 8      # height of the rotated label
    vtext(x, BOT_Y - 18 - h, name, 18, fg, bg)          # ends just above the bottom pin

X_5V = pin_x[("top", "5V")]
X_GND = pin_x[("top", "GND")]
X_3V3 = pin_x[("top", "3V3")]

# switch -> boost IN+ (4), TP OUT- -> boost IN- (5)
wire([(SWX - 46, SWY), (250, SWY), (250, 420), (IN_P[0], 420), IN_P], RED)
badge(250, (SWY + 420) / 2 + 10, 4, RED)
wire([TP_OM, (400, TP_OM[1]), (400, 445), (IN_M[0], 445), IN_M], BLACK)
badge(400, (TP_OM[1] + 445) / 2 + 30, 5, BLACK)

# boost OUT+ -> 5V (6), boost OUT- -> GND (7)
OUT_P, OUT_M = (X_5V, UY1), (300, UY1)
for (x, y), n in ((OUT_P, "OUT+"), (OUT_M, "OUT-")):
    dot(x, y, PAD)
    en(x, y - 34, n, 20, (255, 255, 255))
wire([OUT_P, (X_5V, TOP_Y - 12)], RED)
badge(X_5V + 44, (UY1 + TOP_Y) / 2, 6, RED)
wire([OUT_M, (300, 700), (X_GND, 700), (X_GND, TOP_Y - 12)], BLACK)
badge(X_GND + 44, 735, 7, BLACK)

# 3V3 warning
d.line([(X_3V3 - 30, 700), (X_3V3 + 30, 760)], fill=RED, width=8)
d.line([(X_3V3 + 30, 700), (X_3V3 - 30, 760)], fill=RED, width=8)
ku(X_3V3 - 50, 690, "باتری ب 3V3 ڤە نە!", 26, RED, anchor="ra")

# ---------------- Legend ----------------
LY = 1260
d.rounded_rectangle([40, LY, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
rows = [
    (1, RED, "باتری +", "TP4056 B+"),
    (2, BLACK, "باتری -", "TP4056 B-"),
    (3, RED, "TP4056 OUT+", "سویچ"),
    (4, RED, "سویچ", "Boost IN+"),
    (5, BLACK, "TP4056 OUT-", "Boost IN-"),
    (6, RED, "Boost OUT+", "ESP32 5V"),
    (7, BLACK, "Boost OUT-", "ESP32 GND"),
]


def any_text(x, y, text, size, color, anchor):
    if text[0].isascii():
        en(x, y, text, size, color, anchor)
    else:
        ku(x, y, text, size, color, anchor)


for k, (n, c, src, dst) in enumerate(rows):
    y = LY + 30 + k * 76
    d.ellipse([W - 124, y, W - 72, y + 52], fill=c)
    en(W - 98, y + 6, str(n), 30, (255, 255, 255))
    any_text(W - 144, y + 10, src, 28, INK, "ra")
    en(480, y + 6, "←", 34, c, "ma")
    any_text(420, y + 10, dst, 28, INK, "ra")

NY = LY + 30 + len(rows) * 76 + 10
d.line([(80, NY), (W - 80, NY)], fill=(220, 220, 220), width=2)
ku(W - 80, NY + 18, "• 5V = پینا ئێکێ ل نک USB-C، ل ڕێزا سەرێ", 26, RED, anchor="ra")
ku(W - 80, NY + 64, "• پشت بۆردی ببینە: دڤێت 5V و GND ل وێرێ نڤیسی بن", 26, INK, anchor="ra")
ku(W - 80, NY + 110, "• بەری 6 و 7، Boost بکە 5.0V", 26, INK, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
