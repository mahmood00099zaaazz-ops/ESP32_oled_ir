"""Charging + power for ONE 3.7V LiPo cell (TP4056 USB-C + boost to 5V), and where it goes in the robot.

Kurdish (Badini) labels. Output: images/single_cell_power.png
Usage: python3 tools/draw_single_cell_power.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "single_cell_power.png"
W, H = 1080, 2560
BG = (250, 250, 246)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
GREEN = (25, 145, 65)
TP_BLUE = (30, 80, 170)
BOOST = (40, 120, 200)
LIPO = (40, 40, 44)

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


def dot(x, y, color, r=11):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def section_title(y, text):
    d.line([(40, y + 30), (W - 40, y + 30)], fill=(210, 210, 205), width=2)
    tw = d.textlength(text, font=font(40), direction="rtl")
    d.rectangle([W / 2 - tw / 2 - 20, y, W / 2 + tw / 2 + 20, y + 60], fill=BG)
    ku(W / 2, y + 6, text, 40)


def pin_label(x, y, text, side, color=(255, 255, 255)):
    if side == "right":
        en(x - 12, y - 13, text, 22, color, anchor="ra")
    else:
        en(x + 12, y - 13, text, 22, color, anchor="la")


# =====================================================================
# Title
# =====================================================================
ku(W / 2, 24, "شارژ و کارەبا ڕۆبۆتی", 58)
ku(W / 2, 106, "ب ئێک باتریا 3.7V (وەکی یا تە)", 32, GREY)

# =====================================================================
# 1) Wiring
# =====================================================================
section_title(170, "١. وایەر")

# battery (left, flat LiPo)
BX0, BY0, BX1, BY1 = 60, 290, 330, 470
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=18, fill=LIPO, outline=INK, width=4)
en((BX0 + BX1) / 2, BY0 + 40, "Li-ion", 30, (255, 255, 255))
en((BX0 + BX1) / 2, BY0 + 84, "3.7V 1000mAh", 26, (230, 230, 230))
ku((BX0 + BX1) / 2, BY1 + 14, "باتریا تە", 28, GREY)
BAT_P, BAT_M = (BX1, BY0 + 45), (BX1, BY1 - 40)
dot(*BAT_P, RED)
dot(*BAT_M, BLACK)

# TP4056 (middle)
TX0, TY0, TX1, TY1 = 430, 280, 690, 520
d.rounded_rectangle([TX0, TY0, TX1, TY1], radius=10, fill=TP_BLUE, outline=INK, width=4)
d.rounded_rectangle([TX0 + 80, TY0 - 30, TX0 + 180, TY0 + 12], radius=10, fill=(200, 200, 205), outline=INK, width=3)
en(TX0 + 192, TY0 - 26, "USB-C", 24, GREY, anchor="la")
en((TX0 + TX1) / 2, TY0 + 60, "TP4056", 30, (255, 255, 255))
d.ellipse([TX0 + 90, TY0 + 110, TX0 + 114, TY0 + 134], fill=(255, 70, 70), outline=INK, width=2)
d.ellipse([TX0 + 150, TY0 + 110, TX0 + 174, TY0 + 134], fill=(80, 150, 255), outline=INK, width=2)
pads_l = {"B+": TY0 + 45, "B-": TY1 - 40}
pads_r = {"OUT+": TY0 + 45, "OUT-": TY1 - 40}
for n, y in pads_l.items():
    dot(TX0, y, (230, 200, 90), 9)
    pin_label(TX0, y, n, "left")
for n, y in pads_r.items():
    dot(TX1, y, (230, 200, 90), 9)
    pin_label(TX1, y, n, "right")
wire([BAT_P, (380, BAT_P[1]), (380, pads_l["B+"]), (TX0, pads_l["B+"])], RED)
wire([BAT_M, (380, BAT_M[1]), (380, pads_l["B-"]), (TX0, pads_l["B-"])], BLACK)

# switch
SW = (790, 325)
d.rounded_rectangle([SW[0] - 50, SW[1] - 40, SW[0] + 50, SW[1] + 40], radius=10, fill=(220, 40, 40), outline=INK, width=4)
d.rectangle([SW[0] - 30, SW[1] - 22, SW[0] + 30, SW[1] + 22], fill=(170, 20, 20), outline=INK, width=2)
ku(SW[0], SW[1] + 50, "سویچ", 28)
wire([(TX1, pads_r["OUT+"]), (SW[0] - 50, pads_r["OUT+"])], RED)

# boost converter (bottom middle)
UX0, UY0, UX1, UY1 = 430, 620, 780, 820
d.rounded_rectangle([UX0, UY0, UX1, UY1], radius=10, fill=BOOST, outline=INK, width=4)
en((UX0 + UX1) / 2, UY0 + 14, "Boost  →  5.0V", 30, (255, 255, 255))
en((UX0 + UX1) / 2, UY0 + 52, "MT3608 / 5V 2A", 22, (220, 235, 255))
d.ellipse([UX0 + 140, UY0 + 90, UX0 + 210, UY0 + 160], fill=(60, 60, 60), outline=INK, width=3)
pads_in = {"IN+": UY0 + 110, "IN-": UY0 + 170}
pads_out = {"OUT+": UY0 + 110, "OUT-": UY0 + 170}
for n, y in pads_in.items():
    dot(UX1, y, (230, 200, 90), 9)
    pin_label(UX1, y, n, "right")
for n, y in pads_out.items():
    dot(UX0, y, (230, 200, 90), 9)
    pin_label(UX0, y, n, "left")
# switch -> boost IN+
wire([(SW[0] + 50, SW[1]), (900, SW[1]), (900, pads_in["IN+"]), (UX1, pads_in["IN+"])], RED)
# TP OUT- -> boost IN-
wire([(TX1, pads_r["OUT-"]), (950, pads_r["OUT-"]), (950, pads_in["IN-"]), (UX1, pads_in["IN-"])], BLACK)

# ESP32 + other 5V parts (bottom left)
EX0, EY0, EX1, EY1 = 60, 900, 300, 1110
d.rounded_rectangle([EX0, EY0, EX1, EY1], radius=10, fill=(30, 30, 30), outline=INK, width=4)
d.rectangle([EX0 + 50, EY0 + 20, EX1 - 50, EY0 + 90], fill=(200, 200, 205), outline=INK, width=2)
en((EX0 + EX1) / 2, EY0 + 108, "ESP32", 28, (255, 255, 255))
for n, y in (("VIN", EY0 + 150), ("GND", EY0 + 190)):
    dot(EX1, y, (230, 200, 90), 9)
    pin_label(EX1, y, n, "right", (255, 210, 120))
# boost OUT -> ESP32 VIN / GND
wire([(UX0, pads_out["OUT+"]), (380, pads_out["OUT+"]), (380, EY0 + 150), (EX1, EY0 + 150)], RED)
wire([(UX0, pads_out["OUT-"]), (340, pads_out["OUT-"]), (340, EY0 + 190), (EX1, EY0 + 190)], BLACK)
# also to sound module + OLED
d.rounded_rectangle([430, 930, 780, 1090], radius=12, fill=(255, 255, 255), outline=INK, width=3)
ku(760, 948, "5V بۆ:", 26, RED, anchor="ra")
ku(760, 990, "پارچا دەنگی", 24, INK, anchor="ra")
en(760, 1030, "OLED, IR: ESP32 3V3", 22, GREY, anchor="ra")
wire([(380, 1010), (430, 1010)], RED, 8)
dot(380, 1010, RED, 8)

# warnings under the wiring
ku(W - 60, 1150, "⚠ باتریێ هەرگیز ب 3V3 یان VIN ڤە ڕاستەوخۆ گرێ نەدە!", 28, RED, anchor="ra")
ku(W - 60, 1196, "بەری گرێدانێ، Boost ب مالتیمیتەری بکە 5.0V", 28, INK, anchor="ra")

# =====================================================================
# 2) Inside the robot (top view)
# =====================================================================
IY = 1270
section_title(IY, "٢. د ناڤ ڕۆبۆتی دا (ژ سەری ڤە)")
RX0, RY0, RX1, RY1 = 220, IY + 120, 860, IY + 700
d.rounded_rectangle([RX0, RY0, RX1, RY1], radius=30, fill=(245, 245, 240), outline=(70, 70, 75), width=8)
en((RX0 + RX1) / 2, RY0 - 56, "↑", 34, GREY)
ku((RX0 + RX1) / 2 + 20, RY0 - 52, "پێش", 26, GREY, anchor="la")

# battery flat at the bottom, middle
d.rounded_rectangle([RX0 + 150, RY0 + 230, RX1 - 150, RY0 + 400], radius=14, fill=LIPO, outline=INK, width=3)
ku((RX0 + RX1) / 2, RY0 + 290, "باتری", 30, (255, 255, 255))
ku((RX0 + RX1) / 2, RY0 + 410, "ل بنی، ل ناڤەڕاستێ", 22, GREY)
# ESP32 near the front
d.rectangle([RX0 + 220, RY0 + 40, RX1 - 220, RY0 + 160], fill=(30, 30, 30), outline=INK, width=3)
en((RX0 + RX1) / 2, RY0 + 84, "ESP32", 26, (255, 255, 255))
# boost on the left side
d.rectangle([RX0 + 30, RY0 + 250, RX0 + 120, RY0 + 380], fill=BOOST, outline=INK, width=3)
en(RX0 + 75, RY0 + 300, "5V", 26, (255, 255, 255))
# TP4056 against the BACK wall, USB-C port through a hole
TPX = (RX0 + RX1) / 2
d.rectangle([TPX - 70, RY1 - 110, TPX + 70, RY1 - 8], fill=TP_BLUE, outline=INK, width=3)
en(TPX, RY1 - 84, "TP4056", 22, (255, 255, 255))
d.rounded_rectangle([TPX - 34, RY1 - 18, TPX + 34, RY1 + 18], radius=8, fill=(200, 200, 205), outline=INK, width=3)
# cable plugged in from outside
wire([(TPX, RY1 + 18), (TPX, RY1 + 90)], (60, 60, 60), 18)
d.rounded_rectangle([TPX - 60, RY1 + 90, TPX + 60, RY1 + 150], radius=10, fill=(240, 240, 240), outline=INK, width=3)
ku(TPX + 80, RY1 + 100, "کێبلا شارژێ ل ڤێرێ", 26, GREEN, anchor="la")
ku(TPX - 80, RY1 + 30, "کونا USB-C", 24, GREEN, anchor="ra")
# switch on the right side wall
d.rounded_rectangle([RX1 - 16, RY0 + 270, RX1 + 34, RY0 + 360], radius=8, fill=(220, 40, 40), outline=INK, width=3)
ku(RX1 + 46, RY0 + 290, "سویچ", 26, INK, anchor="la")
ku(RX1 + 46, RY0 + 326, "ل دیوارێ لایی", 20, GREY, anchor="la")

# =====================================================================
# 3) How to charge
# =====================================================================
CY = IY + 900
d.rounded_rectangle([40, CY, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, CY + 20, "چاوا شارژ بکەی؟", 36, GREEN, anchor="ra")
steps = [
    "١. سویچێ بگرە (OFF)",
    "٢. کێبلا USB-C بکە د کونا پشتێ دا",
    "٣. ڕۆناهیا سۆر = شارژ دبیت...",
    "٤. ڕۆناهیا شین یان کەسک = تژی بوو ✓",
    "٥. کێبلێ دەربێخە و سویچێ ڤەکە (ON)",
]
for k, t in enumerate(steps):
    ku(W - 80, CY + 84 + k * 56, t, 28, INK, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
