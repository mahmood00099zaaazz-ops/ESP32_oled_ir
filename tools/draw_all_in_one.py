"""All parts in ONE clear picture, every wire drawn and numbered (power included).

Power uses two rails (orange 3V3, black GND) like a breadboard; signal wires go straight to the
ESP32 without crossings; where a wire must cross a rail it jumps over it (small arch = not connected).
ESP32 is the 38-pin USB-C board (DevKitC pinout). Kurdish (Badini) text.
Output: images/all_in_one.png
Usage: python3 tools/draw_all_in_one.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "all_in_one.png"
W, H = 1080, 2560
BG = (246, 243, 236)
INK = (25, 25, 30)
GREY = (105, 105, 105)
RED = (215, 35, 35)
ORANGE = (240, 130, 20)
BLACK = (20, 20, 20)
GOLD = (222, 184, 80)
C_SCL, C_SDA, C_OUT = (30, 160, 90), (40, 110, 220), (150, 70, 200)
C_SD, C_SCK, C_WS = (220, 60, 160), (110, 170, 30), (0, 160, 180)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size):
    return ImageFont.truetype("DejaVuSans-Bold.ttf", size, layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, t, size, color=INK, anchor="ma"):
    d.text((x, y), t, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, t, size, color=INK, anchor="ma"):
    d.text((x, y), t, font=font(size), fill=color, anchor=anchor)


def line(pts, color, w=8):
    dark = tuple(max(0, v - 70) for v in color)
    d.line(pts, fill=dark, width=w + 5, joint="curve")
    d.line(pts, fill=color, width=w, joint="curve")


def hline_with_hops(x_from, x_to, y, color, hops, w=8):
    """Horizontal wire from x_from to x_to at height y, jumping over vertical lines at `hops` x."""
    xs = sorted([x_from, x_to])
    pts = [(xs[0], y)]
    for hx in sorted(h for h in hops if xs[0] < h < xs[1]):
        pts.append((hx - 14, y))
        for k in range(0, 181, 20):                 # half circle over the crossing
            import math
            a = math.radians(180 - k)
            pts.append((hx + 14 * math.cos(a), y - 14 * math.sin(a)))
        pts.append((hx + 14, y))
    pts.append((xs[1], y))
    line(pts, color, w)


def bezier(p0, p3, bend, n=40):
    (x0, y0), (x3, y3) = p0, p3
    p1, p2 = (x0 + bend[0], y0 + bend[1]), (x3 + bend[2], y3 + bend[3])
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        out.append((a * x0 + b * p1[0] + c * p2[0] + e * x3, a * y0 + b * p1[1] + c * p2[1] + e * y3))
    return out


def plug(x, y):
    d.rectangle([x - 8, y - 8, x + 8, y + 8], fill=(30, 30, 30))


def dot(x, y, color):
    d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=color, outline=INK, width=2)


def badge(x, y, n, color):
    d.ellipse([x - 19, y - 19, x + 19, y + 19], fill=color, outline=INK, width=2)
    en(x, y - 13, str(n), 22 if n < 10 else 19, (255, 255, 255))


def gold_pin(x, y):
    d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=GOLD, outline=INK, width=2)


# ---------------- Title ----------------
ku(W / 2, 18, "هەمی پارچە پێکڤە", 56)
ku(W / 2, 92, "هەر وایەرەک ژمارەک هەیە، ل خشتێ ببینە", 26, GREY)

# =====================================================================
# ESP32
# =====================================================================
BX0, BX1, BY0, BY1 = 430, 700, 330, 1530
PITCH = (BY1 - BY0 - 80) / 18
LEFT = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12",
        "GND", "13", "D2", "D3", "CMD", "5V"]
RIGHT = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4",
         "0", "2", "15", "D1", "D0", "CLK"]
LX, RX = BX0 + 18, BX1 - 18


def ly(name):
    return BY0 + 40 + LEFT.index(name) * PITCH


def ry(name):
    return BY0 + 40 + RIGHT.index(name) * PITCH


d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=16, fill=(24, 24, 28), outline=INK, width=4)
d.rounded_rectangle([BX0 + 75, BY0 + 20, BX1 - 75, BY0 + 280], radius=6, fill=(196, 196, 200), outline=(90, 90, 95), width=3)
en((BX0 + BX1) / 2, BY0 + 125, "ESP32", 26, (70, 70, 75))
d.rounded_rectangle([(BX0 + BX1) / 2 - 38, BY1 - 36, (BX0 + BX1) / 2 + 38, BY1 + 16], radius=9,
                    fill=(200, 200, 205), outline=INK, width=3)
en((BX0 + BX1) / 2, BY1 + 22, "USB-C", 20, GREY)
HOT_L = {"3V3", "34", "35", "32", "33", "25", "26", "27", "GND", "5V"}
HOT_R = {"GND0", "22", "21"}
for i, n in enumerate(LEFT):
    y = BY0 + 40 + i * PITCH
    hot = n in HOT_L
    d.ellipse([LX - 9, y - 9, LX + 9, y + 9], fill=GOLD if hot else (110, 100, 70), outline=INK, width=2)
    en(LX + 15, y - 11, n, 17, (255, 255, 255) if hot else (110, 110, 115), "la")
for i, n in enumerate(RIGHT):
    y = BY0 + 40 + i * PITCH
    hot = (n == "GND" and i == 0) or n in ("22", "21")
    d.ellipse([RX - 9, y - 9, RX + 9, y + 9], fill=GOLD if hot else (110, 100, 70), outline=INK, width=2)
    en(RX - 15, y - 11, n, 17, (255, 255, 255) if hot else (110, 110, 115), "ra")

# =====================================================================
# Power rails (left margin): GND outer (x=30), 3V3 inner (x=58)
# =====================================================================
GX, VX = 30, 60
TOP_G, TOP_V = 240, 262            # heights of the rail lines that run over the top
# 3V3 rail: down the left, over the top, into ESP 3V3 (left pin 1)
line([(VX, 830), (VX, TOP_V), (400, TOP_V), (400, ly("3V3")), (LX, ly("3V3"))], ORANGE)
# GND rail: down the left, over the top, into ESP GND (right pin 1)
line([(GX, 880), (GX, TOP_G), (725, TOP_G), (725, ry("GND")), (RX, ry("GND"))], BLACK)
plug(LX, ly("3V3"))
plug(RX, ry("GND"))
en(VX + 14, TOP_V + 8, "3V3", 18, ORANGE, "la")
en(GX + 4, TOP_G - 30, "GND", 18, BLACK, "la")

# =====================================================================
# OLED (right, turned sideways, pins on its left edge)
# =====================================================================
OX0, OY0, OX1, OY1 = 790, 330, 1040, 740
d.rounded_rectangle([OX0, OY0, OX1, OY1], radius=10, fill=(30, 70, 160), outline=INK, width=4)
d.rectangle([OX0 + 95, OY0 + 20, OX1 - 18, OY1 - 20], fill=(8, 10, 16), outline=(60, 60, 70), width=3)
for ey in (OY0 + 90, OY0 + 250):
    d.rounded_rectangle([OX0 + 125, ey, OX0 + 205, ey + 70], radius=12, fill=(90, 200, 255))
ku((OX0 + OX1) / 2, OY0 - 44, "شاشە", 26, INK)
OP = {"VCC": ly("3V3"), "GND": ry("GND") + 62, "SCL": ry("22"), "SDA": ry("21")}
for n, y in OP.items():
    gold_pin(OX0 + 18, y)
    en(OX0 + 32, y - 11, n, 17, (255, 255, 255), "la")
OPX = OX0 + 18
# 1 VCC -> over the top (jumps over the GND rail line) -> joins the 3V3 line
line([(OPX, OP["VCC"]), (755, OP["VCC"]), (755, 205), (412, 205)], ORANGE)
d.line([(400, 205), (400, TOP_G - 14)], fill=(170, 80, 10), width=13)
d.line([(400, 205), (400, TOP_G - 14)], fill=ORANGE, width=8)
d.arc([386, TOP_G - 14, 414, TOP_G + 14], start=270, end=90, fill=ORANGE, width=8)   # hop over GND line
d.line([(400, TOP_G + 14), (400, TOP_V)], fill=ORANGE, width=8)
line([(412, 205), (400, 205)], ORANGE)
dot(400, TOP_V, ORANGE)
plug(OPX, OP["VCC"])
badge(755, 290, 1, ORANGE)
# 2 GND -> right GND pin 1
pts = bezier((OPX, OP["GND"]), (RX, ry("GND")), (-60, 0, 30, 30))
line(pts, BLACK)
plug(OPX, OP["GND"])
badge(*pts[20], 2, BLACK)
# 3 SCL, 4 SDA straight
for n, num, col in (("SCL", 3, C_SCL), ("SDA", 4, C_SDA)):
    line([(OPX, OP[n]), (RX, OP[n])], col)
    plug(OPX, OP[n])
    plug(RX, OP[n])
    badge((OPX + RX) / 2, OP[n], num, col)

# =====================================================================
# IR sensor (top left)
# =====================================================================
IX0, IY0, IX1, IY1 = 100, 340, 330, 560
d.rounded_rectangle([IX0, IY0, IX1, IY1], radius=10, fill=(30, 85, 170), outline=INK, width=4)
d.ellipse([IX0 + 70, IY0 + 20, IX0 + 120, IY0 + 70], fill=(245, 245, 245), outline=INK, width=2)
d.ellipse([IX0 + 135, IY0 + 20, IX0 + 185, IY0 + 70], fill=(30, 30, 30), outline=INK, width=2)
ku((IX0 + IX1) / 2, IY0 - 44, "سێنسەرێ IR", 26, INK)
IR_V, IR_G, IR_O = 420, 480, 530
for n, y, x in (("VCC", IR_V, IX0 + 18), ("GND", IR_G, IX0 + 18)):
    gold_pin(x, y)
    en(x + 14, y - 11, n, 17, (255, 255, 255), "la")
gold_pin(IX1 - 18, IR_O)
en(IX1 - 32, IR_O - 11, "OUT", 17, (255, 255, 255), "ra")
# 5 VCC -> 3V3 rail, 6 GND -> GND rail (hop over 3V3 rail), 7 OUT -> 34
line([(IX0 + 18, IR_V), (VX, IR_V)], ORANGE)
dot(VX, IR_V, ORANGE)
plug(IX0 + 18, IR_V)
badge(IX0 - 12, IR_V - 34, 5, ORANGE)
hline_with_hops(GX, IX0 + 18, IR_G, BLACK, [VX])
dot(GX, IR_G, BLACK)
plug(IX0 + 18, IR_G)
badge(IX0 - 12, IR_G + 34, 6, BLACK)
pts = bezier((IX1 - 18, IR_O), (LX, ly("34")), (90, 0, -90, 0))
line(pts, C_OUT)
plug(IX1 - 18, IR_O)
plug(LX, ly("34"))
badge(*pts[22], 7, C_OUT)

# =====================================================================
# INMP441 microphone (left middle)
# =====================================================================
MCX, MCY, MR = 215, 760, 130
d.ellipse([MCX - MR, MCY - MR, MCX + MR, MCY + MR], fill=(18, 18, 22), outline=(200, 160, 60), width=6)
d.ellipse([MCX - 18, MCY - 100, MCX + 18, MCY - 64], fill=(80, 80, 85), outline=(200, 160, 60), width=3)
ku(MCX, MCY - MR - 44, "مایک", 26, INK)
MV, MG, MLR = 700, 760, 820
for n, y in (("VDD", MV), ("GND", MG), ("L/R", MLR)):
    gold_pin(MCX - 100, y)
    en(MCX - 86, y - 11, n, 16, (255, 255, 255), "la")
for n, name in (("SD", "35"), ("SCK", "32"), ("WS", "33")):
    y = ly(name)
    gold_pin(MCX + 105, y)
    en(MCX + 91, y - 11, n, 16, (255, 255, 255), "ra")
# 8 VDD -> 3V3 rail, 9 GND + 10 L/R -> GND rail (hop over 3V3 rail)
line([(MCX - 100, MV), (VX, MV)], ORANGE)
dot(VX, MV, ORANGE)
badge(MCX - 100 - 38, MV - 26, 8, ORANGE)
for y, num in ((MG, 9), (MLR, 10)):
    hline_with_hops(GX, MCX - 100, y, BLACK, [VX])
    dot(GX, y, BLACK)
    badge(MCX - 100 - 38, y + 24 if num == 10 else y - 26 + 50, num, BLACK) if False else None
badge(MCX - 100 - 38, MG + 0 - 26 + 52, 9, BLACK) if False else None
for p in ((MCX - 100, MV), (MCX - 100, MG), (MCX - 100, MLR)):
    plug(*p)
# badges for 9 and 10 just below their wires (left of the mic)
badge(MCX - 150, MG + 26, 9, BLACK)
badge(MCX - 150, MLR + 26, 10, BLACK)
# 11 SD, 12 SCK, 13 WS straight to the ESP32
for n, name, num, col in (("SD", "35", 11, C_SD), ("SCK", "32", 12, C_SCK), ("WS", "33", 13, C_WS)):
    y = ly(name)
    line([(MCX + 105, y), (LX, y)], col)
    plug(MCX + 105, y)
    plug(LX, y)
    badge((MCX + 105 + LX) / 2, y, num, col)

# =====================================================================
# MAX98357A amplifier (left lower) + speaker
# =====================================================================
AX0, AY0, AX1, AY1 = 100, 960, 330, 1320
d.rounded_rectangle([AX0, AY0, AX1, AY1], radius=10, fill=(95, 55, 155), outline=INK, width=4)
d.rectangle([AX0 + 40, AY0 + 150, AX0 + 100, AY0 + 210], fill=(20, 20, 24))
ku((AX0 + AX1) / 2, AY0 - 44, "ئامپلیفایەر", 26, INK)
amp_y = {"LRC": 1000, "BCLK": 1046, "DIN": 1092, "GAIN": 1138,
         "SD": 1184, "GND": 1230, "Vin": 1276}
for n, y in amp_y.items():
    gold_pin(AX1 - 18, y)
    en(AX1 - 32, y - 11, n, 16, (255, 255, 255) if n not in ("GAIN", "SD") else (180, 170, 200), "ra")
    if n in ("GAIN", "SD"):
        d.line([(AX1 + 4, y - 9), (AX1 + 22, y + 9)], fill=GREY, width=4)
        d.line([(AX1 + 4, y + 9), (AX1 + 22, y - 9)], fill=GREY, width=4)
for n, name, num, col in (("LRC", "25", 14, C_WS), ("BCLK", "26", 15, C_SCK), ("DIN", "27", 16, C_SD)):
    pts = bezier((AX1 - 18, amp_y[n]), (LX, ly(name)), (55, 0, -55, 0))
    line(pts, col)
    plug(AX1 - 18, amp_y[n])
    plug(LX, ly(name))
    badge(*pts[20], num, col)
# 17 GND -> ESP GND (left pin 14), 18 Vin -> ESP 5V (left pin 19)
pts = bezier((AX1 - 18, amp_y["GND"]), (LX, ly("GND")), (60, 0, -60, 0))
line(pts, BLACK)
badge(*pts[20], 17, BLACK)
pts = bezier((AX1 - 18, amp_y["Vin"]), (LX, ly("5V")), (70, 0, -70, 0))
line(pts, RED)
badge(*pts[20], 18, RED)
for p in ((AX1 - 18, amp_y["GND"]), (LX, ly("GND")), (AX1 - 18, amp_y["Vin"]), (LX, ly("5V"))):
    plug(*p)
# speaker terminal (left edge) + speaker
d.rectangle([AX0 - 26, AY0 + 260, AX0 + 18, AY0 + 340], fill=(40, 170, 110), outline=INK, width=3)
en(AX0 - 4, AY0 + 266, "+", 22, (255, 255, 255))
en(AX0 - 4, AY0 + 302, "-", 26, (255, 255, 255))
SCX, SCY, SR = 210, 1460, 75
line([(AX0 - 26, AY0 + 280), (70, AY0 + 280), (70, SCY - 20), (SCX - SR + 4, SCY - 20)], RED, 6)
line([(AX0 - 26, AY0 + 320), (84, AY0 + 320), (84, SCY + 20), (SCX - SR + 2, SCY + 20)], BLACK, 6)
d.ellipse([SCX - SR, SCY - SR, SCX + SR, SCY + SR], fill=(205, 205, 210), outline=INK, width=5)
d.ellipse([SCX - 46, SCY - 46, SCX + 46, SCY + 46], outline=(150, 150, 155), width=4)
en(SCX, SCY - 16, "8Ω", 26, INK)
ku(SCX, SCY + SR + 8, "بلندگۆ", 26, INK)

# =====================================================================
# Table
# =====================================================================
TY = 1640
groups = [
    ("شاشە", [(1, ORANGE, "VCC", "3V3"), (2, BLACK, "GND", "GND"), (3, C_SCL, "SCL", "GPIO22"), (4, C_SDA, "SDA", "GPIO21")]),
    ("IR", [(5, ORANGE, "VCC", "3V3"), (6, BLACK, "GND", "GND"), (7, C_OUT, "OUT", "GPIO34")]),
    ("مایک", [(8, ORANGE, "VDD", "3V3"), (9, BLACK, "GND", "GND"), (10, BLACK, "L/R", "GND"),
              (11, C_SD, "SD", "GPIO35"), (12, C_SCK, "SCK", "GPIO32"), (13, C_WS, "WS", "GPIO33")]),
    ("ئامپلیفایەر", [(14, C_WS, "LRC", "GPIO25"), (15, C_SCK, "BCLK", "GPIO26"), (16, C_SD, "DIN", "GPIO27"),
                     (17, BLACK, "GND", "GND"), (18, RED, "Vin", "5V")]),
]
d.rounded_rectangle([30, TY, W - 30, H - 30], radius=20, fill=(255, 255, 255), outline=INK, width=4)
colx = [(W - 60, 560), (520, 50)]          # (right edge, left edge) of the two columns
cursor = [TY + 24, TY + 24]
for gi, (title, rows) in enumerate(groups):
    c = 0 if gi in (0, 2) else 1
    xr, xl = colx[c]
    y = cursor[c]
    ku(xr, y, title, 28, INK, anchor="ra")
    y += 46
    for n, col, part_pin, esp in rows:
        badge(xr - 20, y + 18, n, col)
        en(xr - 50, y + 4, part_pin, 24, INK, "ra")
        en(xr - 170, y + 2, "→", 26, col)
        en(xr - 200, y + 4, esp, 24, col, "ra")
        y += 52
    cursor[c] = y + 20
ky = max(cursor) + 6
d.line([(60, ky), (W - 60, ky)], fill=(220, 220, 220), width=2)
ku(W / 2, ky + 16, "⚠ مایک و شاشە و IR ب 3V3 ڤە، نە 5V", 26, RED)
ku(W / 2, ky + 58, "GAIN و SD یێن ئامپی بەتال بهێلە (✕)", 24, GREY)
ku(W / 2, ky + 98, "کەڤانا بچووک = وایەر ب سەر وایەرێ دی ڕا دچیت، پێکڤە گرێ نابن", 22, GREY)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size, "table ends at", ky + 130)
