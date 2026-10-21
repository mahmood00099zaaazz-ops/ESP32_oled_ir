"""Wire-by-wire guide on the user's 38-pin USB-C ESP32 (DevKitC pinout), for the audio/AI robot.

The board is drawn upright (antenna up, USB-C down) with every pin named and counted from the top,
and each needed wire numbered with its destination. Kurdish (Badini) text.
Output: images/wire_by_wire.png
Usage: python3 tools/draw_wire_by_wire.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "wire_by_wire.png"
W, H = 1080, 2560
BG = (252, 252, 248)
INK = (25, 25, 30)
GREY = (110, 110, 110)
RED = (215, 35, 35)
ORANGE = (240, 130, 20)
BLACK = (15, 15, 15)
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


# DevKitC 38-pin, antenna up / USB down, counted from the top
LEFT = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12",
        "GND", "13", "D2", "D3", "CMD", "5V"]
RIGHT = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4",
         "0", "2", "15", "D1", "D0", "CLK"]

# wire number, side, pin name, colour, what it connects to
WIRES = [
    (1, "R", "21", (40, 110, 220), "OLED SDA"),
    (2, "R", "22", (30, 160, 90), "OLED SCL"),
    (3, "L", "34", (150, 70, 200), "IR OUT"),
    (4, "L", "35", (200, 60, 160), "MIC SD"),
    (5, "L", "32", (110, 160, 30), "MIC SCK"),
    (6, "L", "33", (0, 150, 170), "MIC WS"),
    (7, "L", "25", (0, 150, 170), "AMP LRC"),
    (8, "L", "26", (110, 160, 30), "AMP BCLK"),
    (9, "L", "27", (200, 60, 160), "AMP DIN"),
]
POWER = {  # pin -> (colour, text)
    ("L", "3V3"): (ORANGE, "OLED VCC + IR VCC + MIC VDD"),
    ("L", "5V"): (RED, "AMP Vin"),
    ("R", "GND"): (BLACK, "GND"),
    ("L", "GND"): (BLACK, "GND"),
}

# ---------------- Title ----------------
ku(W / 2, 20, "وایەر ئێک ب ئێک", 60)
ku(W / 2, 100, "ل سەر بۆردا تە: ESP32 یا 38 پین", 30, GREY)

# ---------------- Board ----------------
BX0, BX1, BY0, BY1 = 360, 720, 190, 1330
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=18, fill=BOARD, outline=INK, width=5)
d.rounded_rectangle([BX0 + 125, BY0 + 30, BX1 - 125, BY0 + 230], radius=8, fill=(190, 190, 195), outline=INK, width=3)
en((BX0 + BX1) / 2, BY0 + 110, "ESP32", 24, (70, 70, 70))
d.rounded_rectangle([(BX0 + BX1) / 2 - 40, BY1 - 20, (BX0 + BX1) / 2 + 40, BY1 + 34], radius=8,
                    fill=(190, 190, 195), outline=INK, width=3)
en((BX0 + BX1) / 2, BY1 + 40, "USB-C", 22, GREY)

PY0, PITCH = BY0 + 40, (BY1 - BY0 - 80) / 18
used = {(s, p): (n, c, t) for n, s, p, c, t in WIRES}


def pin_y(i):
    return PY0 + i * PITCH


for side, names, x in (("L", LEFT, BX0), ("R", RIGHT, BX1)):
    for i, name in enumerate(names):
        y = pin_y(i)
        key = (side, name)
        hot = key in used or key in POWER
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=(230, 190, 70) if hot else (120, 110, 80),
                  outline=INK, width=2)
        label_col = (255, 255, 255) if hot else (150, 150, 155)
        if side == "L":
            en(x + 18, y - 13, name, 22, label_col, "la")
            en(x + 112, y - 11, str(i + 1), 18, (120, 120, 125), "ra")   # count from the top (inside)
        else:
            en(x - 18, y - 13, name, 22, label_col, "ra")
            en(x - 112, y - 11, str(i + 1), 18, (120, 120, 125), "la")

# ---------------- Wires ----------------
def badge(x, y, n, color):
    d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=color, outline=INK, width=2)
    en(x, y - 15, str(n), 26, (255, 255, 255))


for n, side, pin, col, text in WIRES:
    names = LEFT if side == "L" else RIGHT
    y = pin_y(names.index(pin))
    if side == "L":
        d.line([(BX0 - 50, y), (BX0 - 11, y)], fill=col, width=8)
        d.line([(60, y), (BX0 - 90, y)], fill=col, width=8)
        badge(BX0 - 70, y, n, col)
        d.rectangle([30, y - 20, 222, y + 20], fill=BG)
        en(218, y - 14, text, 22, col, "ra")
    else:
        d.line([(BX1 + 11, y), (BX1 + 50, y)], fill=col, width=8)
        d.line([(BX1 + 90, y), (1020, y)], fill=col, width=8)
        badge(BX1 + 70, y, n, col)
        d.rectangle([862, y - 20, 1060, y + 20], fill=BG)
        en(866, y - 14, text, 22, col, "la")

# power pins: short stub + tag
for (side, pin), (col, text) in POWER.items():
    names = LEFT if side == "L" else RIGHT
    for i, name in enumerate(names):
        if name != pin:
            continue
        y = pin_y(i)
        if side == "L":
            d.line([(BX0 - 120, y), (BX0 - 11, y)], fill=col, width=8)
            tw = d.textlength(pin, font=font(22))
            d.rounded_rectangle([BX0 - 120 - tw - 20, y - 18, BX0 - 120, y + 18], radius=8, fill=col)
            en(BX0 - 130, y - 13, pin, 22, (255, 255, 255), "ra")
        else:
            d.line([(BX1 + 11, y), (BX1 + 120, y)], fill=col, width=8)
            tw = d.textlength(pin, font=font(22))
            d.rounded_rectangle([BX1 + 120, y - 18, BX1 + 140 + tw, y + 18], radius=8, fill=col)
            en(BX1 + 130, y - 13, pin, 22, (255, 255, 255), "la")

ku(W / 2, BY1 + 72, "ژمارێن خۆلەمێشی د ناڤ بۆردێ دا = پینا چەندێ ژ سەری", 22, GREY)

# ---------------- Step list ----------------
LY = 1470
d.rounded_rectangle([40, LY, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, LY + 18, "وایەر ل دویڤ ئێک:", 36, INK, anchor="ra")
steps = [
    (1, (40, 110, 220), "OLED SDA", "21", "ڕاست، پینا 6"),
    (2, (30, 160, 90), "OLED SCL", "22", "ڕاست، پینا 3"),
    (3, (150, 70, 200), "IR OUT", "34", "چەپ، پینا 5"),
    (4, (200, 60, 160), "MIC SD", "35", "چەپ، پینا 6"),
    (5, (110, 160, 30), "MIC SCK", "32", "چەپ، پینا 7"),
    (6, (0, 150, 170), "MIC WS", "33", "چەپ، پینا 8"),
    (7, (0, 150, 170), "AMP LRC", "25", "چەپ، پینا 9"),
    (8, (110, 160, 30), "AMP BCLK", "26", "چەپ، پینا 10"),
    (9, (200, 60, 160), "AMP DIN", "27", "چەپ، پینا 11"),
]
for k, (n, col, part, pin, where) in enumerate(steps):
    y = LY + 84 + k * 70
    badge(W - 96, y + 18, n, col)
    en(W - 140, y + 4, part, 28, INK, "ra")
    en(620, y + 2, "→", 32, col, "ma")
    en(560, y + 4, "GPIO" + pin, 28, col, "ra")
    ku(330, y + 8, where, 24, GREY, anchor="ra")

py = LY + 84 + len(steps) * 70 + 10
d.line([(80, py), (W - 80, py)], fill=(220, 220, 220), width=2)
power_rows = [
    (ORANGE, "3V3", "OLED VCC + IR VCC + MIC VDD", "چەپ، پینا 1"),
    (RED, "5V", "AMP Vin", "چەپ، پینا 19"),
    (BLACK, "GND", "OLED + IR + MIC GND + MIC L/R + AMP GND", ""),
]
for k, (col, net, text, where) in enumerate(power_rows):
    y = py + 24 + k * 66
    tw = d.textlength(net, font=font(24))
    d.rounded_rectangle([W - 80 - tw - 20, y, W - 80, y + 38], radius=8, fill=col)
    en(W - 90, y + 6, net, 24, (255, 255, 255), "ra")
    en(W - 120 - tw, y + 8, "← " + text, 22, INK, "ra")
    if where:
        ku(330, y + 10, where, 22, GREY, anchor="ra")
ku(W / 2, py + 24 + 3 * 66 + 6, "GND: چەپ پینا 14، یان ڕاست پینا 1 و 7", 24, GREY)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
