"""Very simple battery wiring with NUMBERED wires (1 cell 3.7V -> TP4056 -> switch -> boost 5V -> ESP32).

Red wires on the right, black wires on the left, no crossings. Kurdish (Badini) legend.
Output: images/battery_numbered.png
Usage: python3 tools/draw_battery_numbered.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "battery_numbered.png"
W, H = 1080, 2530
BG = (252, 252, 248)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
TP_BLUE = (30, 80, 170)
BOOST = (40, 120, 200)
PAD = (235, 200, 90)

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
    d.line(pts, fill=color, width=16, joint="curve")


def badge(x, y, n, color):
    d.ellipse([x - 34, y - 34, x + 34, y + 34], fill=(255, 255, 255), outline=color, width=7)
    en(x, y - 25, str(n), 44, color)


def part(x0, y0, x1, y1, title, fill, sub=None, text=(255, 255, 255)):
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=fill, outline=INK, width=5)
    en((x0 + x1) / 2, (y0 + y1) / 2 - (34 if sub else 22), title, 40, text)
    if sub:
        en((x0 + x1) / 2, (y0 + y1) / 2 + 14, sub, 26, text)


def pad(x, y, name, inside_left):
    d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=PAD, outline=INK, width=3)
    if inside_left:
        en(x + 20, y - 15, name, 26, (255, 255, 255), anchor="la")
    else:
        en(x - 20, y - 15, name, 26, (255, 255, 255), anchor="ra")


CX0, CX1 = 300, 780            # all parts share these x edges
LX, RX = 170, 910              # black lane (left) and red lane (right)

# ---------------- Title ----------------
ku(W / 2, 24, "وایەرێن باتریێ ب ژمارە", 60)
ku(W / 2, 108, "سۆر ل ڕاستێ، ڕەش ل چەپێ", 32, GREY)

# ---------------- Battery ----------------
B0, B1 = 190, 350
part(CX0, B0, CX1, B1, "باتری", (40, 40, 44), "3.7V 1000mAh")
# replace the Latin title with a Kurdish one
d.rounded_rectangle([CX0, B0, CX1, B1], radius=18, fill=(40, 40, 44), outline=INK, width=5)
ku((CX0 + CX1) / 2, B0 + 34, "باتری", 42, (255, 255, 255))
en((CX0 + CX1) / 2, B0 + 96, "3.7V 1000mAh", 28, (230, 230, 230))
en(CX1 - 40, B0 + 26, "+", 56, RED)
en(CX0 + 40, B0 + 20, "-", 64, (255, 255, 255))
BAT_P, BAT_M = (CX1, B0 + 70), (CX0, B0 + 70)

# ---------------- TP4056 ----------------
T0, T1 = 470, 690
part(CX0, T0, CX1, T1, "TP4056", TP_BLUE, "(شارژ)")
d.rounded_rectangle([CX0, T0, CX1, T1], radius=18, fill=TP_BLUE, outline=INK, width=5)
en((CX0 + CX1) / 2, T0 + 80, "TP4056", 40, (255, 255, 255))
d.rounded_rectangle([(CX0 + CX1) / 2 - 50, T0 + 138, (CX0 + CX1) / 2 + 50, T0 + 178], radius=8,
                    fill=(200, 200, 205), outline=INK, width=3)
en((CX0 + CX1) / 2, T0 + 186, "USB-C", 20, (220, 230, 255))
TP_BP, TP_BM = (CX1, T0 + 40), (CX0, T0 + 40)
TP_OP, TP_OM = (CX1, T1 - 40), (CX0, T1 - 40)
pad(*TP_BP, "B+", False)
pad(*TP_BM, "B-", True)
pad(*TP_OP, "OUT+", False)
pad(*TP_OM, "OUT-", True)

# ---------------- Switch (on the red lane) ----------------
S0, S1 = 790, 900
d.rounded_rectangle([RX - 60, S0, RX + 60, S1], radius=12, fill=(220, 40, 40), outline=INK, width=5)
d.rectangle([RX - 36, S0 + 24, RX + 36, S1 - 24], fill=(170, 20, 20), outline=INK, width=3)
ku(RX - 80, S0 + 30, "سویچ", 34, INK, anchor="ra")

# ---------------- Boost ----------------
U0, U1 = 1000, 1220
d.rounded_rectangle([CX0, U0, CX1, U1], radius=18, fill=BOOST, outline=INK, width=5)
en((CX0 + CX1) / 2, U0 + 70, "Boost 5V", 40, (255, 255, 255))
en((CX0 + CX1) / 2, U0 + 120, "MT3608", 26, (220, 235, 255))
UP_IP, UP_IM = (CX1, U0 + 40), (CX0, U0 + 40)
UP_OP, UP_OM = (CX1, U1 - 40), (CX0, U1 - 40)
pad(*UP_IP, "IN+", False)
pad(*UP_IM, "IN-", True)
pad(*UP_OP, "OUT+", False)
pad(*UP_OM, "OUT-", True)

# ---------------- ESP32 ----------------
E0, E1 = 1330, 1530
d.rounded_rectangle([CX0, E0, CX1, E1], radius=18, fill=(30, 30, 30), outline=INK, width=5)
en((CX0 + CX1) / 2, E0 + 70, "ESP32", 44, (255, 255, 255))
ES_V, ES_G = (CX1, E0 + 100), (CX0, E0 + 100)
pad(*ES_V, "VIN", False)
pad(*ES_G, "GND", True)

# ---------------- Wires (numbered) ----------------
wire([BAT_P, (RX, BAT_P[1]), (RX, TP_BP[1]), TP_BP], RED)                    # 1
wire([BAT_M, (LX, BAT_M[1]), (LX, TP_BM[1]), TP_BM], BLACK)                  # 2
wire([TP_OP, (RX, TP_OP[1]), (RX, S0)], RED)                                 # 3
wire([(RX, S1), (RX, UP_IP[1]), UP_IP], RED)                                 # 4
wire([TP_OM, (LX, TP_OM[1]), (LX, UP_IM[1]), UP_IM], BLACK)                  # 5
wire([UP_OP, (RX, UP_OP[1]), (RX, ES_V[1]), ES_V], RED)                      # 6
wire([UP_OM, (LX, UP_OM[1]), (LX, ES_G[1]), ES_G], BLACK)                    # 7

badge(RX, (BAT_P[1] + TP_BP[1]) / 2, 1, RED)
badge(LX, (BAT_M[1] + TP_BM[1]) / 2, 2, BLACK)
badge(RX, (TP_OP[1] + S0) / 2, 3, RED)
badge(RX, (S1 + UP_IP[1]) / 2, 4, RED)
badge(LX, (TP_OM[1] + UP_IM[1]) / 2, 5, BLACK)
badge(RX, (UP_OP[1] + ES_V[1]) / 2, 6, RED)
badge(LX, (UP_OM[1] + ES_G[1]) / 2, 7, BLACK)

# ---------------- Legend ----------------
LY = 1610
d.rounded_rectangle([40, LY, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
rows = [
    (1, RED, "باتری +", "TP4056 B+"),
    (2, BLACK, "باتری -", "TP4056 B-"),
    (3, RED, "TP4056 OUT+", "سویچ"),
    (4, RED, "سویچ", "Boost IN+"),
    (5, BLACK, "TP4056 OUT-", "Boost IN-"),
    (6, RED, "Boost OUT+", "ESP32 VIN"),
    (7, BLACK, "Boost OUT-", "ESP32 GND"),
]


def any_text(x, y, text, size, color, anchor):
    """Kurdish (RTL) or Latin text, chosen by the first character."""
    if text[0].isascii():
        en(x, y, text, size, color, anchor)
    else:
        ku(x, y, text, size, color, anchor)


for k, (n, c, src, dst) in enumerate(rows):
    y = LY + 40 + k * 100
    # number on the right (start of an RTL line)
    d.ellipse([W - 130, y, W - 70, y + 60], fill=c)
    en(W - 100, y + 8, str(n), 34, (255, 255, 255))
    # "from" on the right, arrow, "to" on the left
    any_text(W - 150, y + 12, src, 30, INK, "ra")
    en(480, y + 8, "←", 38, c, "ma")
    any_text(420, y + 12, dst, 30, INK, "ra")

WY = LY + 40 + len(rows) * 100 + 20
d.line([(80, WY - 10), (W - 80, WY - 10)], fill=(220, 220, 220), width=2)
ku(W / 2, WY + 10, "⚠ بەری وایەرێن 6 و 7:", 32, RED)
ku(W / 2, WY + 60, "پیچا Boost بزڤڕینە هەتا 5.0V (ب مالتیمیتەری)", 28, INK)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
