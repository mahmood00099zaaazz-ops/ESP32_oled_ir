"""Battery / power picture for the walking robot (4 servos + ESP32), Kurdish (Badini) labels.

2x18650 -> switch -> 3A buck (5.0V) -> 5V rail -> 4 servos + ESP32 VIN, plus a lighter 4xAA option.
Output: images/walker_power.png
Usage: python3 tools/draw_walker_power.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "walker_power.png"
W, H = 1080, 2330
BG = (250, 250, 246)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
GREEN = (25, 145, 65)
YELLOW = (255, 208, 30)
SG_BLUE = (50, 95, 225)
MG_DARK = (55, 52, 58)
BUCK_BLUE = (40, 110, 200)
ORANGE = (245, 145, 20)

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


def dot(x, y, color, r=12):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color)


# =====================================================================
# Title
# =====================================================================
ku(W / 2, 24, "باتری بۆ ڕۆبۆتێ ب پێیان", 58)
en(W / 2, 108, "2x 18650 + Buck 3A", 40, GREY)

# =====================================================================
# Battery holder (top)
# =====================================================================
BX0, BY0, BX1, BY1 = 200, 190, 880, 450
d.rounded_rectangle([BX0, BY0, BX1, BY1], radius=24, fill=(50, 50, 56), outline=INK, width=5)
for k, plus_right in enumerate((True, False)):
    y = BY0 + 30 + k * 115
    d.rounded_rectangle([BX0 + 50, y, BX1 - 50, y + 90], radius=40, fill=YELLOW, outline=INK, width=4)
    nub = BX1 - 54 if plus_right else BX0 + 30
    d.rectangle([nub, y + 28, nub + 24, y + 62], fill=(205, 205, 205), outline=INK, width=2)
    en((BX0 + BX1) / 2, y + 22, "18650  3.7V", 38, INK)
    en(BX1 - 100 if plus_right else BX0 + 100, y + 12, "+", 56, RED)
    en(BX0 + 100 if plus_right else BX1 - 100, y + 6, "-", 64, INK)
ku((BX0 + BX1) / 2, BY1 + 14, "پێکڤە = 7.4V", 32, GREY)

RPLUS = (BX1, BY0 + 75)            # red wire out of the holder (top cell +)
BMINUS = (BX1, BY0 + 190)          # black wire out of the holder (bottom cell -, on the right)
dot(*RPLUS, RED)
dot(*BMINUS, BLACK)

# =====================================================================
# Switch + buck converter
# =====================================================================
SW = (900, 600)                    # switch centre
d.rounded_rectangle([SW[0] - 70, SW[1] - 45, SW[0] + 70, SW[1] + 45], radius=12, fill=(240, 240, 240), outline=INK, width=5)
d.rounded_rectangle([SW[0] - 30, SW[1] - 22, SW[0] + 30, SW[1] + 22], radius=8, fill=(60, 60, 60))
ku(SW[0] - 82, SW[1] - 20, "سویچ", 30, anchor="ra")
wire([RPLUS, (960, RPLUS[1]), (960, SW[1] - 45 + 6)], RED)
wire([(SW[0], SW[1] + 45), (SW[0], SW[1] + 100), (720, SW[1] + 100)], RED)

# buck board
UX0, UY0, UX1, UY1 = 320, 560, 720, 800
d.rounded_rectangle([UX0, UY0, UX1, UY1], radius=12, fill=BUCK_BLUE, outline=INK, width=5)
d.ellipse([UX0 + 140, UY0 + 70, UX0 + 250, UY0 + 180], fill=(60, 60, 60), outline=INK, width=3)      # coil
d.rectangle([UX0 + 280, UY0 + 70, UX0 + 320, UY0 + 120], fill=(70, 120, 230), outline=INK, width=2)   # trim pot
d.ellipse([UX0 + 288, UY0 + 82, UX0 + 312, UY0 + 106], fill=(240, 200, 60), outline=INK, width=2)
en((UX0 + UX1) / 2, UY0 + 16, "Buck 3A  →  5.0V", 30, (255, 255, 255))
en(UX1 - 12, UY0 + 120 - 15, "IN+", 22, (255, 255, 255), anchor="ra")
en(UX1 - 12, UY0 + 200 - 15, "IN-", 22, (255, 255, 255), anchor="ra")
en(UX0 + 12, UY0 + 120 - 15, "OUT+", 22, (255, 255, 255), anchor="la")
en(UX0 + 12, UY0 + 200 - 15, "OUT-", 22, (255, 255, 255), anchor="la")
# switch -> IN+
d.line([(720, SW[1] + 100), (UX1, SW[1] + 100)], fill=RED, width=12)
dot(UX1, UY0 + 120, RED, 9)
wire([(720, SW[1] + 100), (720, UY0 + 120)], RED)
# battery - -> IN-
wire([BMINUS, (1010, BMINUS[1]), (1010, UY0 + 200), (UX1, UY0 + 200)], BLACK)
dot(UX1, UY0 + 200, BLACK, 9)
ku((UX0 + UX1) / 2, UY1 + 30, "بەری گرێدانێ: پیچا زەر بزڤڕینە هەتا 5.0V", 28, RED)
ku((UX0 + UX1) / 2, UY1 + 72, "(ب مالتیمیتەری)", 24, GREY)

# =====================================================================
# 5V rail -> 4 servos + ESP32
# =====================================================================
RAIL_R, RAIL_B = 1020, 1080        # y of the red and black rails
d.rounded_rectangle([60, RAIL_R - 30, W - 60, RAIL_B + 30], radius=14, fill=(255, 255, 255), outline=(200, 200, 200), width=3)
d.line([(90, RAIL_R), (W - 90, RAIL_R)], fill=RED, width=14)
d.line([(90, RAIL_B), (W - 90, RAIL_B)], fill=BLACK, width=14)
en(W - 100, RAIL_R - 24, "+5V", 22, RED, anchor="ra")
en(W - 100, RAIL_B + 8, "GND", 22, INK, anchor="ra")
# buck OUT -> rails
wire([(UX0, UY0 + 120), (110, UY0 + 120), (110, RAIL_R)], RED)
wire([(UX0, UY0 + 200), (160, UY0 + 200), (160, RAIL_B)], BLACK)
dot(110, RAIL_R, RED)
dot(160, RAIL_B, BLACK)
dot(UX0, UY0 + 120, RED, 9)
dot(UX0, UY0 + 200, BLACK, 9)


def small_servo(cx, top, kind):
    body = MG_DARK if kind == "MG90S" else SG_BLUE
    d.rounded_rectangle([cx - 70, top, cx + 70, top + 110], radius=8, fill=body, outline=INK, width=4)
    d.rounded_rectangle([cx - 50, top - 22, cx + 10, top + 4], radius=10, fill=body, outline=INK, width=3)
    en(cx, top + 40, kind, 24, (255, 255, 255))


loads = [
    (300, "SG90", "کەمەرا چەپ"),
    (480, "SG90", "کەمەرا ڕاست"),
    (660, "MG90S", "پێیێ چەپ"),
    (840, "MG90S", "پێیێ ڕاست"),
]
LOAD_TOP = 1220
for cx, kind, name in loads:
    wire([(cx - 18, RAIL_R), (cx - 18, LOAD_TOP)], RED, 8)
    wire([(cx + 18, RAIL_B), (cx + 18, LOAD_TOP)], BROWN := (120, 70, 35), 8)
    dot(cx - 18, RAIL_R, RED, 8)
    dot(cx + 18, RAIL_B, BLACK, 8)
    small_servo(cx, LOAD_TOP, kind)
    ku(cx, LOAD_TOP + 122, name, 22, GREY)
# ESP32
ex = 130
d.rectangle([ex - 60, LOAD_TOP - 10, ex + 60, LOAD_TOP + 130], fill=(30, 30, 30), outline=INK, width=4)
d.rectangle([ex - 38, LOAD_TOP + 5, ex + 38, LOAD_TOP + 50], fill=(200, 200, 205), outline=INK, width=2)
en(ex, LOAD_TOP + 70, "ESP32", 22, (255, 255, 255))
en(ex, LOAD_TOP + 100, "VIN", 20, ORANGE)
wire([(ex - 18, RAIL_R), (ex - 18, LOAD_TOP - 10)], RED, 8)
wire([(ex + 18, RAIL_B), (ex + 18, LOAD_TOP - 10)], BLACK, 8)
dot(ex - 18, RAIL_R, RED, 8)
dot(ex + 18, RAIL_B, BLACK, 8)

ku(W / 2, LOAD_TOP + 170, "هەمی سۆر ← +5V  ،  هەمی ڕەش و قاوەیی ← GND", 28, INK)

# =====================================================================
# Tips + lighter option
# =====================================================================
TY = 1470
d.rounded_rectangle([40, TY, W - 40, TY + 420], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, TY + 20, "بۆچی ئەڤە باشە؟", 36, GREEN, anchor="ra")
tips = [
    "18650 ب هێزە، دشێت 4 سێرڤۆیان پێکڤە بلڤینیت",
    "دووبارە شارژ دبیت، ب TP4056 ئێک ب ئێک",
    "Buck دڤێت 3A بیت، نە یێ بچووک (Mini-360 نە)",
    "باتریێ ل ناڤەڕاستا لەشی دانە، دا ڕۆبۆت نەکەڤیت",
    "دەمێ Upload دکەی، سویچێ بگرە",
]
for k, t in enumerate(tips):
    ku(W - 80, TY + 82 + k * 64, "•  " + t, 27, INK, anchor="ra")

AY = TY + 450
d.rounded_rectangle([40, AY, W - 40, H - 30], radius=22, fill=(240, 246, 255), outline=SG_BLUE, width=4)
ku(W - 80, AY + 20, "یان، ڕێکا سڤکتر و ساناهیتر:", 34, SG_BLUE, anchor="ra")
ku(W - 80, AY + 82, "•  4 باتریێن AA یێن شارژ دبن (NiMH) = 4.8V", 27, INK, anchor="ra")
ku(W - 80, AY + 140, "•  Buck پێدڤی ناکەت! ڕاستەوخۆ ب 5V ڤە", 27, INK, anchor="ra")
ku(W - 80, AY + 198, "•  بەس زووتر خلاس دبیت", 27, GREY, anchor="ra")
# little 4xAA pack icon
for k in range(4):
    x = 90 + k * 52
    d.rounded_rectangle([x, AY + 90, x + 44, AY + 210], radius=10, fill=(90, 190, 90), outline=INK, width=3)
    d.rectangle([x + 14, AY + 80, x + 30, AY + 92], fill=(200, 200, 200), outline=INK, width=2)
en(190, AY + 220, "4x AA", 24, GREY)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
