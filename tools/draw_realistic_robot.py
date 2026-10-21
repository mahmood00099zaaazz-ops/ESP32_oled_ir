"""Realistic-looking wiring picture: ESP32 (38-pin, USB-C) + OLED + IR + INMP441 + MAX98357A + speaker.

Parts are drawn to look like the real modules, signal wires are curved like jumper wires, and power
pins end in coloured tags (same colour = connect together). Kurdish (Badini) labels.
Output: images/realistic_robot.png
Usage: python3 tools/draw_realistic_robot.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "realistic_robot.png"
W, H = 1080, 2160
BG = (244, 240, 232)          # light wooden-table colour
INK = (25, 25, 30)
GREY = (100, 100, 100)
RED = (215, 35, 35)
ORANGE = (240, 130, 20)
BLACK = (20, 20, 20)
GOLD = (222, 184, 80)
SIG = {"SDA": (40, 110, 220), "SCL": (30, 160, 90), "OUT": (150, 70, 200),
       "SD": (220, 60, 160), "SCK": (110, 170, 30), "WS": (0, 160, 180),
       "LRC": (0, 160, 180), "BCLK": (110, 170, 30), "DIN": (220, 60, 160)}

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
for y in range(0, H, 22):                     # subtle wood grain
    d.line([(0, y), (W, y + 6)], fill=(236, 231, 221), width=2)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def bezier(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    return pts


def jumper(p0, p1, p2, p3, color):
    pts = bezier(p0, p1, p2, p3)
    dark = tuple(max(0, c - 70) for c in color)
    d.line(pts, fill=dark, width=13, joint="curve")
    d.line(pts, fill=color, width=8, joint="curve")
    for p in (p0, p3):                             # connector ends
        d.rectangle([p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8], fill=(30, 30, 30))


def pin(x, y, label=None, side="below", color=(255, 255, 255), size=18):
    d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=GOLD, outline=INK, width=2)
    if label:
        if side == "below":
            en(x, y + 12, label, size, color)
        elif side == "above":
            en(x, y - 32, label, size, color)
        elif side == "left":
            en(x - 14, y - 11, label, size, color, "ra")
        else:
            en(x + 14, y - 11, label, size, color, "la")


def tag(x, y, net, direction="down"):
    col = {"3V3": ORANGE, "5V": RED, "GND": BLACK}[net]
    dx, dy = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}[direction]
    ex, ey = x + dx * 40, y + dy * 40
    d.line([(x, y), (ex, ey)], fill=col, width=7)
    tw = d.textlength(net, font=font(18))
    if direction in ("down", "up"):
        box = [ex - tw / 2 - 7, ey if dy > 0 else ey - 28, ex + tw / 2 + 7, ey + 28 if dy > 0 else ey]
    elif direction == "left":
        box = [ex - tw - 14, ey - 14, ex, ey + 14]
    else:
        box = [ex, ey - 14, ex + tw + 14, ey + 14]
    d.rounded_rectangle(box, radius=7, fill=col)
    en((box[0] + box[2]) / 2, box[1] + 4, net, 18, (255, 255, 255))


# ---------------- Title ----------------
ku(W / 2, 20, "ڕۆبۆت: هەمی پارچە", 58)
ku(W / 2, 98, "شاشە، مایک، ئامپلیفایەر، بلندگۆ و IR", 30, GREY)

# =====================================================================
# ESP32 (centre)
# =====================================================================
BX0, BX1, BY0, BY1 = 405, 675, 470, 1500
d.rounded_rectangle([BX0 + 6, BY0 + 8, BX1 + 6, BY1 + 8], radius=16, fill=(200, 194, 182))   # shadow
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=16, fill=(24, 24, 28), outline=INK, width=4)
# metal module + antenna
d.rounded_rectangle([BX0 + 60, BY0 + 20, BX1 - 60, BY0 + 300], radius=6, fill=(196, 196, 200), outline=(90, 90, 95), width=3)
d.rectangle([BX0 + 60, BY0 + 20, BX1 - 60, BY0 + 70], fill=(30, 30, 34))
for k in range(5):
    x = BX0 + 80 + k * 24
    d.line([(x, BY0 + 30), (x, BY0 + 60), (x + 12, BY0 + 60), (x + 12, BY0 + 30)], fill=GOLD, width=3)
en((BX0 + BX1) / 2, BY0 + 140, "ESP32", 30, (70, 70, 75))
en((BX0 + BX1) / 2, BY0 + 184, "WiFi + BT", 18, (90, 90, 95))
# chips, buttons, USB-C
d.rectangle([BX0 + 100, BY1 - 300, BX0 + 170, BY1 - 230], fill=(12, 12, 14))
d.rectangle([BX0 + 190, BY1 - 330, BX0 + 230, BY1 - 290], fill=(12, 12, 14))
for bx, name in ((BX0 + 70, "EN"), (BX1 - 70, "BOOT")):
    d.rectangle([bx - 18, BY1 - 110, bx + 18, BY1 - 74], fill=(200, 200, 205), outline=INK, width=2)
    d.ellipse([bx - 8, BY1 - 100, bx + 8, BY1 - 84], fill=(40, 40, 40))
    en(bx, BY1 - 68, name, 14, (200, 200, 205))
d.rounded_rectangle([(BX0 + BX1) / 2 - 40, BY1 - 40, (BX0 + BX1) / 2 + 40, BY1 + 18], radius=10,
                    fill=(200, 200, 205), outline=INK, width=3)
en((BX0 + BX1) / 2, BY1 + 24, "USB-C", 20, GREY)

LEFT = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12",
        "GND", "13", "D2", "D3", "CMD", "5V"]
RIGHT = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4",
         "0", "2", "15", "D1", "D0", "CLK"]
PY0, PITCH = BY0 + 40, (BY1 - BY0 - 80) / 18
LX, RX = BX0 + 18, BX1 - 18
HOT = {"3V3", "GND", "5V", "34", "35", "32", "33", "25", "26", "27", "21", "22"}


def py(i):
    return PY0 + i * PITCH


for i, n in enumerate(LEFT):
    pin(LX, py(i), n, "right", (255, 255, 255) if n in HOT else (120, 120, 125), 16)
for i, n in enumerate(RIGHT):
    pin(RX, py(i), n, "left", (255, 255, 255) if n in HOT else (120, 120, 125), 16)
ESP = {("L", n): (LX, py(i)) for i, n in enumerate(LEFT)}
ESP.update({("R", n): (RX, py(i)) for i, n in enumerate(RIGHT)})
tag(*ESP[("L", "3V3")], "3V3", "left")
tag(*ESP[("L", "GND")], "GND", "left")
tag(LX, py(18), "5V", "left")
tag(*ESP[("R", "GND")], "GND", "right")

# =====================================================================
# IR sensor (top left)
# =====================================================================
IX0, IY0, IX1, IY1 = 30, 210, 300, 370
d.rounded_rectangle([IX0, IY0, IX1, IY1], radius=10, fill=(30, 85, 170), outline=INK, width=4)
d.ellipse([IX0 + 20, IY0 + 30, IX0 + 70, IY0 + 80], fill=(245, 245, 245), outline=INK, width=2)   # IR LED
d.ellipse([IX0 + 85, IY0 + 30, IX0 + 135, IY0 + 80], fill=(30, 30, 30), outline=INK, width=2)     # receiver
d.rectangle([IX0 + 160, IY0 + 30, IX0 + 200, IY0 + 70], fill=(60, 110, 230), outline=INK, width=2)  # pot
d.ellipse([IX0 + 168, IY0 + 38, IX0 + 192, IY0 + 62], fill=(240, 240, 240))
IR_PINS = {"OUT": (IX0 + 50, IY1 - 18), "GND": (IX0 + 140, IY1 - 18), "VCC": (IX0 + 230, IY1 - 18)}
for n, (x, y) in IR_PINS.items():
    pin(x, y, n, "above", (255, 255, 255), 16)
tag(*IR_PINS["GND"], "GND", "down")
tag(*IR_PINS["VCC"], "3V3", "down")
ku((IX0 + IX1) / 2, IY0 - 44, "سێنسەرێ IR", 26, INK)

# =====================================================================
# OLED (top right)
# =====================================================================
OX0, OY0, OX1, OY1 = 740, 210, 1040, 460
d.rounded_rectangle([OX0, OY0, OX1, OY1], radius=10, fill=(30, 70, 160), outline=INK, width=4)
d.rectangle([OX0 + 18, OY0 + 20, OX1 - 18, OY0 + 170], fill=(8, 10, 16), outline=(60, 60, 70), width=3)
for ex in (OX0 + 70, OX0 + 170):
    d.rounded_rectangle([ex, OY0 + 55, ex + 60, OY0 + 125], radius=12, fill=(90, 200, 255))
OL_PINS = {"GND": (OX0 + 45, OY1 - 22), "VCC": (OX0 + 125, OY1 - 22),
           "SCL": (OX0 + 180, OY1 - 22), "SDA": (OX0 + 240, OY1 - 22)}
for n, (x, y) in OL_PINS.items():
    pin(x, y, n, "above", (255, 255, 255), 16)
tag(*OL_PINS["GND"], "GND", "down")
tag(*OL_PINS["VCC"], "3V3", "down")
ku((OX0 + OX1) / 2, OY0 - 44, "شاشە OLED", 26, INK)

# =====================================================================
# INMP441 microphone (left middle)
# =====================================================================
MCX, MCY, MR = 170, 740, 120
d.ellipse([MCX - MR, MCY - MR, MCX + MR, MCY + MR], fill=(18, 18, 22), outline=(200, 160, 60), width=6)
d.ellipse([MCX - 18, MCY - 70, MCX + 18, MCY - 34], fill=(80, 80, 85), outline=(200, 160, 60), width=3)
en(MCX, MCY - 20, "INMP441", 20, (230, 230, 230))
MIC_SIG = {"SD": (MCX + 90, MCY - 55), "SCK": (MCX + 108, MCY - 12), "WS": (MCX + 100, MCY + 32)}
MIC_PWR = {"VDD": (MCX - 72, MCY + 65), "GND": (MCX - 8, MCY + 95), "L/R": (MCX + 56, MCY + 85)}
for n, (x, y) in MIC_SIG.items():
    pin(x, y, n, "left", (255, 255, 255), 16)
for n, (x, y) in MIC_PWR.items():
    pin(x, y, n, "above", (255, 255, 255), 14)
tag(*MIC_PWR["VDD"], "3V3", "down")
tag(*MIC_PWR["GND"], "GND", "down")
tag(*MIC_PWR["L/R"], "GND", "down")
ku(MCX, MCY - MR - 46, "مایک", 26, INK)

# =====================================================================
# MAX98357A amplifier (left lower)
# =====================================================================
AX0, AY0, AX1, AY1 = 70, 1010, 300, 1330
d.rounded_rectangle([AX0, AY0, AX1, AY1], radius=10, fill=(95, 55, 155), outline=INK, width=4)
d.rectangle([AX0 + 70, AY0 + 120, AX0 + 130, AY0 + 180], fill=(20, 20, 24))
en(AX0 + 100, AY0 + 30, "MAX", 18, (230, 220, 255))
en(AX0 + 100, AY0 + 54, "98357", 18, (230, 220, 255))
amp_names = ["LRC", "BCLK", "DIN", "GAIN", "SD", "GND", "Vin"]
AMP = {}
for k, n in enumerate(amp_names):
    x, y = AX1 - 18, AY0 + 30 + k * 44
    pin(x, y, n, "left", (255, 255, 255) if n not in ("GAIN", "SD") else (180, 170, 200), 16)
    AMP[n] = (x, y)
tag(*AMP["GND"], "GND", "right")
tag(*AMP["Vin"], "5V", "right")
for n in ("GAIN", "SD"):
    x, y = AMP[n]
    d.line([(x + 16, y - 8), (x + 32, y + 8)], fill=GREY, width=4)
    d.line([(x + 16, y + 8), (x + 32, y - 8)], fill=GREY, width=4)
# green screw terminal on the left
d.rectangle([AX0 - 30, AY0 + 230, AX0 + 20, AY0 + 310], fill=(40, 170, 110), outline=INK, width=3)
en(AX0 - 5, AY0 + 236, "+", 22, (255, 255, 255))
en(AX0 - 5, AY0 + 272, "-", 26, (255, 255, 255))
ku((AX0 + AX1) / 2, AY0 - 44, "ئامپلیفایەر", 26, INK)

# =====================================================================
# Speaker (below the amplifier)
# =====================================================================
SCX, SCY, SR = 190, 1520, 95
jumper((AX0 - 30, AY0 + 250), (0, AY0 + 300), (40, SCY - 60), (SCX - 50, SCY - SR + 22), RED)
jumper((AX0 - 30, AY0 + 290), (10, AY0 + 340), (60, SCY - 40), (SCX - 20, SCY - SR + 6), BLACK)
d.ellipse([SCX - SR, SCY - SR, SCX + SR, SCY + SR], fill=(205, 205, 210), outline=INK, width=5)
for r in (70, 45):
    d.ellipse([SCX - r, SCY - r, SCX + r, SCY + r], outline=(150, 150, 155), width=4)
en(SCX, SCY - 34, "8Ω", 28, INK)
en(SCX, SCY + 2, "0.5W", 22, INK)
ku(SCX, SCY + SR + 10, "بلندگۆ", 26, INK)

# =====================================================================
# Signal wires
# =====================================================================
def to_esp(start, side, name, color, bend=110):
    ex, ey = ESP[(side, name)]
    sx, sy = start
    if side == "L":
        jumper((sx, sy), (sx + bend, sy), (ex - bend, ey), (ex, ey), color)
    else:
        jumper((sx, sy), (sx, sy + bend), (ex + bend, ey), (ex, ey), color)


to_esp(IR_PINS["OUT"], "L", "34", SIG["OUT"], bend=200)
for n, esp in (("SD", "35"), ("SCK", "32"), ("WS", "33")):
    to_esp(MIC_SIG[n], "L", esp, SIG[n])
for n, esp in (("LRC", "25"), ("BCLK", "26"), ("DIN", "27")):
    to_esp(AMP[n], "L", esp, SIG[n])
to_esp(OL_PINS["SCL"], "R", "22", SIG["SCL"], bend=140)
to_esp(OL_PINS["SDA"], "R", "21", SIG["SDA"], bend=220)

# =====================================================================
# Legend
# =====================================================================
LY = 1700
d.rounded_rectangle([40, LY, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, LY + 18, "نیشانێن هەمان ڕەنگ ب ئێکڤە گرێ بدە:", 30, INK, anchor="ra")
rows = [(ORANGE, "3V3", "ESP32 3V3  +  OLED VCC  +  IR VCC  +  MIC VDD"),
        (RED, "5V", "ESP32 5V  +  AMP Vin"),
        (BLACK, "GND", "ESP32 GND  +  OLED  +  IR  +  MIC GND, L/R  +  AMP")]
for k, (col, net, text) in enumerate(rows):
    y = LY + 80 + k * 64
    tw = d.textlength(net, font=font(24))
    d.rounded_rectangle([W - 80 - tw - 20, y, W - 80, y + 40], radius=9, fill=col)
    en(W - 90, y + 7, net, 24, (255, 255, 255), "ra")
    en(W - 116 - tw, y + 9, text, 20, INK, "ra")
ku(W / 2, LY + 300, "⚠ مایک ب 5V ڤە نە!   GAIN و SD یێن ئامپی بەتال بهێلە", 24, RED)
ku(W / 2, LY + 346, "ناڤێ پینان ل سەر پارچێن خۆ بخوینە، دبیت ڕێزبەندی جودا بیت", 22, GREY)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
