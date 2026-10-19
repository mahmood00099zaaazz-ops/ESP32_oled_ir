"""6-wheel rover design (rocker-bogie look) with Kurdish (Badini) labels.

Side view, top view, motor wiring (3 motors per side in parallel on the L298N) and a parts list.
Output: images/robot_rover.png
Usage: python3 tools/draw_rover.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "robot_rover.png"
W, H = 1080, 2560
BG = (250, 250, 246)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
GREEN = (25, 145, 65)
BODY = (235, 235, 228)
BODY_EDGE = (70, 70, 75)
GOLD = (215, 170, 60)
LEG = (120, 125, 135)
YELLOW = (255, 208, 30)
TIRE = (40, 40, 42)
PCB_BLUE = (35, 80, 170)
PCB_RED = (200, 40, 40)
SERVO = (60, 100, 220)
EYE = (90, 200, 255)
SOLAR = (40, 70, 130)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def leader(px, py, tx, ty, text, side, size=28, color=INK):
    if side == "right":
        tw = d.textlength(text, font=font(size), direction="rtl")
        tx = min(tx, W - 30 - tw - 8)
    d.line([(px, py), (tx, ty)], fill=color, width=3)
    d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=color)
    if side == "left":
        ku(tx - 8, ty - size // 2 - 2, text, size, color, anchor="ra")
    else:
        ku(tx + 8, ty - size // 2 - 2, text, size, color, anchor="la")


def section_title(y, text):
    d.line([(40, y + 30), (W - 40, y + 30)], fill=(210, 210, 205), width=2)
    tw = d.textlength(text, font=font(40), direction="rtl")
    d.rectangle([W / 2 - tw / 2 - 20, y, W / 2 + tw / 2 + 20, y + 60], fill=BG)
    ku(W / 2, y + 6, text, 40)


def wheel(cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TIRE, outline=INK, width=3)
    for k in range(12):                      # tread
        import math
        a = k * math.pi / 6
        x0, y0 = cx + (r - 2) * math.cos(a), cy + (r - 2) * math.sin(a)
        x1, y1 = cx + (r - 12) * math.cos(a), cy + (r - 12) * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=(90, 90, 90), width=4)
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], fill=(255, 225, 90), outline=INK, width=3)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(240, 240, 240), outline=INK, width=2)


def bar(p0, p1, w=18, color=LEG):
    d.line([p0, p1], fill=INK, width=w + 6)
    d.line([p0, p1], fill=color, width=w)


def pivot(x, y):
    d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=GOLD, outline=INK, width=3)


# =====================================================================
# Title
# =====================================================================
ku(W / 2, 24, "ڕۆبۆتێ ڕۆڤەر", 68)
ku(W / 2, 112, "6 چەرخ، 6 مۆتۆرێن زەر، ب سەر بەر و ڕێکێن نە ساناهی دچیت", 28, GREY)

# =====================================================================
# 1) Side view (front on the RIGHT)
# =====================================================================
section_title(170, "١. ژ لایێ ڤە")
GROUND = 1040
WR = 62
WY = GROUND - WR
REAR, MID, FRONT = 230, 520, 790
ROCKER = (430, 760)          # pivot on the body
BOGIE = (655, 860)           # pivot of the small front arm

# legs (rocker + bogie)
bar(ROCKER, (REAR, WY))
bar(ROCKER, BOGIE)
bar(BOGIE, (MID, WY))
bar(BOGIE, (FRONT, WY))

# motors at each hub
for x in (REAR, MID, FRONT):
    d.rectangle([x - 34, WY - 22, x + 34, WY + 22], fill=YELLOW, outline=INK, width=3)
for x in (REAR, MID, FRONT):
    wheel(x, WY, WR)
pivot(*ROCKER)
pivot(*BOGIE)

# body box
BX0, BY0, BX1, BY1 = 260, 610, 740, 750
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=16, fill=BODY, outline=BODY_EDGE, width=5)
for x in range(BX0 + 30, BX1 - 20, 60):            # side ribs
    d.line([(x, BY0 + 20), (x, BY1 - 20)], fill=(205, 205, 198), width=4)
# top deck (solar panel look)
d.rectangle([BX0 + 10, BY0 - 22, BX0 + 330, BY0], fill=SOLAR, outline=INK, width=3)
for x in range(BX0 + 50, BX0 + 330, 40):
    d.line([(x, BY0 - 22), (x, BY0)], fill=(110, 150, 210), width=2)
# antenna
d.line([(BX0 + 40, BY0 - 22), (BX0 + 40, BY0 - 110)], fill=INK, width=4)
d.ellipse([BX0 + 32, BY0 - 122, BX0 + 48, BY0 - 106], fill=RED, outline=INK, width=2)
# IR sensor at the front
d.rectangle([BX1, BY0 + 70, BX1 + 40, BY0 + 110], fill=PCB_BLUE, outline=INK, width=2)
d.rounded_rectangle([BX1 + 38, BY0 + 74, BX1 + 58, BY0 + 88], radius=5, fill=(240, 240, 240), outline=INK)
d.rounded_rectangle([BX1 + 38, BY0 + 92, BX1 + 58, BY0 + 106], radius=5, fill=(40, 40, 40), outline=INK)

# mast + servo + OLED head
MX = 680
d.rectangle([MX - 10, BY0 - 150, MX + 10, BY0], fill=LEG, outline=INK, width=3)
d.rectangle([MX - 36, BY0 - 205, MX + 36, BY0 - 150], fill=SERVO, outline=INK, width=3)
HX0, HY0, HX1, HY1 = MX - 95, BY0 - 330, MX + 95, BY0 - 205
d.rounded_rectangle([HX0, HY0, HX1, HY1], radius=18, fill=(45, 50, 62), outline=INK, width=4)
d.rounded_rectangle([HX0 + 14, HY0 + 16, HX1 - 14, HY1 - 16], radius=8, fill=(10, 14, 22))
for ex in (HX0 + 52, HX0 + 112):
    d.rounded_rectangle([ex, HY0 + 38, ex + 32, HY0 + 84], radius=8, fill=EYE)

d.line([(120, GROUND + 3), (960, GROUND + 3)], fill=(150, 150, 150), width=4)
# a stone under the middle wheel area to show it climbs
d.chord([860, GROUND - 40, 960, GROUND + 40], start=180, end=360, fill=(170, 150, 120), outline=INK, width=3)
en(980, GROUND - 120, "→", 52, GREY, anchor="ra")
ku(980, GROUND - 170, "پێش", 30, GREY, anchor="ra")

leader(HX0, HY0 + 50, 540, 415, "سەر: OLED", "left")
leader(MX - 36, BY0 - 178, 540, 505, "SG90", "left")
leader(BX0 + 40, BY0 - 112, 220, 460, "ئەنتێن", "left")
leader(BX0 + 160, BY0 - 12, 220, 560, "پلێتا سەرێ", "left")
leader(BX0 + 60, BY0 + 80, 220, 660, "لەش", "left")
leader(BX1 + 50, BY0 + 80, 1000, 630, "IR", "right")
leader(ROCKER[0], ROCKER[1], 330, 1140, "لاقێ مەزن (Rocker)", "left")
leader(BOGIE[0], BOGIE[1], 760, 1140, "لاقێ بچووک (Bogie)", "left")
leader(FRONT + 20, WY - 30, 1000, 770, "مۆتۆر + چەرخ", "right")

# =====================================================================
# 2) Top view + 3) motor wiring
# =====================================================================
TOP0 = 1210
section_title(TOP0, "٢. ژ سەری ڤە و وایەرێن مۆتۆران")

# --- top view (left half), front = UP
ku(300, TOP0 + 62, "ژ سەری ڤە", 30, GREY)
TB0, TB1 = 190, 410                        # body x
TY0, TY1 = TOP0 + 150, TOP0 + 590         # body y
d.rounded_rectangle([TB0, TY0, TB1, TY1], radius=16, fill=BODY, outline=BODY_EDGE, width=5)
wheel_rows = (TY0 + 40, (TY0 + TY1) / 2, TY1 - 40)
for wy in wheel_rows:
    for side in (-1, 1):
        mx0 = TB0 - 48 if side < 0 else TB1 + 8
        d.rectangle([mx0, wy - 20, mx0 + 40, wy + 20], fill=YELLOW, outline=INK, width=3)
        wx0 = TB0 - 100 if side < 0 else TB1 + 52
        d.rounded_rectangle([wx0, wy - 48, wx0 + 48, wy + 48], radius=12, fill=TIRE, outline=INK, width=3)
# inside the body
d.rounded_rectangle([TB0 + 50, TY0 + 30, TB1 - 50, TY0 + 90], radius=8, fill=(45, 50, 62), outline=INK, width=3)
ku((TB0 + TB1) / 2, TY0 + 96, "سەر", 22, GREY)
d.rectangle([TB0 + 60, TY0 + 140, TB1 - 60, TY0 + 230], fill=(30, 30, 30), outline=INK, width=3)
en((TB0 + TB1) / 2, TY0 + 172, "ESP32", 22, (255, 255, 255))
d.rounded_rectangle([TB0 + 30, TY0 + 250, TB1 - 30, TY0 + 330], radius=10, fill=(50, 50, 56), outline=INK, width=3)
d.rounded_rectangle([TB0 + 42, TY0 + 262, TB1 - 42, TY0 + 288], radius=12, fill=YELLOW, outline=INK, width=2)
d.rounded_rectangle([TB0 + 42, TY0 + 296, TB1 - 42, TY0 + 322], radius=12, fill=YELLOW, outline=INK, width=2)
d.rectangle([TB0 + 60, TY0 + 345, TB1 - 60, TY0 + 420], fill=PCB_RED, outline=INK, width=3)
en((TB0 + TB1) / 2, TY0 + 370, "L298N", 22, (255, 255, 255))
en((TB0 + TB1) / 2, TY0 - 46, "↑", 34, GREY)

# --- wiring schematic (right half)
ku(810, TOP0 + 80, "3 مۆتۆر ل هەر لایەکی پێکڤە", 28, GREY)
LX0, LX1 = 715, 905                  # L298N box
LY0, LY1 = TOP0 + 300, TOP0 + 470
d.rounded_rectangle([LX0, LY0, LX1, LY1], radius=12, fill=(255, 215, 215), outline=INK, width=4)
en((LX0 + LX1) / 2, LY0 + 12, "L298N", 26)
OUT_A, OUT_B = LY0 + 70, LY0 + 130     # y of OUT1/OUT3 (red) and OUT2/OUT4 (black)
for x, (a, b), anc, dx in ((LX0, ("OUT1", "OUT2"), "la", 10), (LX1, ("OUT3", "OUT4"), "ra", -10)):
    for y, name in ((OUT_A, a), (OUT_B, b)):
        d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=INK)
        en(x + dx, y - 10, name, 18, INK, anchor=anc)

motor_ys = (TOP0 + 190, TOP0 + 360, TOP0 + 530)


def motor_column(mx0, red_bus, black_bus, out_x, red_side):
    """Three motors stacked; + terminals to a red bus, - terminals to a black bus, both to the L298N."""
    plus_x = mx0 + 46 if red_side == "right" else mx0
    minus_x = mx0 if red_side == "right" else mx0 + 46
    for my in motor_ys:
        d.rounded_rectangle([mx0, my - 32, mx0 + 46, my + 32], radius=6, fill=YELLOW, outline=INK, width=3)
        d.line([(plus_x, my - 12), (red_bus, my - 12)], fill=RED, width=6)
        d.line([(minus_x, my + 12), (black_bus, my + 12)], fill=BLACK, width=6)
        d.ellipse([red_bus - 7, my - 19, red_bus + 7, my - 5], fill=RED)
        d.ellipse([black_bus - 7, my + 5, black_bus + 7, my + 19], fill=BLACK)
    # red bus straight to OUT1/OUT3
    d.line([(red_bus, motor_ys[0] - 12), (red_bus, motor_ys[-1] - 12)], fill=RED, width=6)
    d.line([(red_bus, OUT_A), (out_x, OUT_A)], fill=RED, width=6)
    # black bus goes around underneath to OUT2/OUT4 (no crossing)
    low = motor_ys[-1] + 70
    step_x = out_x - 22 if out_x == LX0 else out_x + 22
    d.line([(black_bus, motor_ys[0] + 12), (black_bus, low), (step_x, low), (step_x, OUT_B), (out_x, OUT_B)],
           fill=BLACK, width=6, joint="curve")


motor_column(610, red_bus=690, black_bus=592, out_x=LX0, red_side="right")
motor_column(964, red_bus=930, black_bus=1028, out_x=LX1, red_side="left")
ku(633, motor_ys[-1] + 90, "چەپ", 26, GREY)
ku(987, motor_ys[-1] + 90, "ڕاست", 26, GREY)

# =====================================================================
# 4) Parts list + tips
# =====================================================================
PY0 = 1880
d.rounded_rectangle([40, PY0, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, PY0 + 22, "چ پێدڤیە؟", 40, INK, anchor="ra")
items = [
    "6 مۆتۆرێن زەر و 6 چەرخ",
    "لەش: سندوقەکێ پلاستیکی یان تەختە، 25 ل سەر 15 سانتیم",
    "لاق: شریتێن ئالەمنیۆمی یان پلاستیکی + پیچێن M3",
    "L298N، باتری 2×18650، Buck، ESP32، OLED، SG90، IR",
]
for k, t in enumerate(items):
    ku(W - 80, PY0 + 86 + k * 50, "•  " + t, 27, INK, anchor="ra")

ku(W - 80, PY0 + 310, "ئامۆژگاری:", 34, RED, anchor="ra")
tips = [
    "3 مۆتۆرێن چەپێ پێکڤە ب OUT1 و OUT2 ڤە بکە",
    "3 مۆتۆرێن ڕاستێ پێکڤە ب OUT3 و OUT4 ڤە بکە",
    "پیچێن لاقان هندەکێ شل بهێلە، دا ب سەر بەران بچیت",
    "6 مۆتۆر پتر کارەبێ دخوەن، باتریێن باش بکڕە",
]
for k, t in enumerate(tips):
    ku(W - 80, PY0 + 366 + k * 50, "•  " + t, 27, INK, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
