"""Robot body (chassis) design: side view, both floors from above, and a parts list.

Kurdish (Badini) labels. Output: images/robot_body.png
Usage: python3 tools/draw_robot_body.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "robot_body.png"
W, H = 1080, 2160
BG = (250, 250, 246)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
PLATE = (170, 215, 235)
PLATE_EDGE = (60, 120, 150)
YELLOW = (255, 208, 30)
TIRE = (40, 40, 42)
PCB_BLUE = (35, 80, 170)
PCB_RED = (200, 40, 40)
SERVO = (60, 100, 220)
EYE = (90, 200, 255)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def leader(px, py, tx, ty, text, side, color=INK, size=28):
    """Line from a part (px, py) to a label at (tx, ty). side: 'left' or 'right' of the drawing."""
    if side == "right":
        # keep the label inside the picture: right-align it to the page margin
        tw = d.textlength(text, font=font(size), direction="rtl")
        tx = min(tx, W - 30 - tw - 8)
    d.line([(px, py), (tx, ty)], fill=color, width=3)
    d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=color)
    if side == "left":
        ku(tx - 8, ty - size // 2 - 2, text, size, color, anchor="ra")
    else:
        ku(tx + 8, ty - size // 2 - 2, text, size, color, anchor="la")


def dashed_rect(box, color, dash=12, width=3):
    x0, y0, x1, y1 = box
    for x in range(int(x0), int(x1), dash * 2):
        d.line([(x, y0), (min(x + dash, x1), y0)], fill=color, width=width)
        d.line([(x, y1), (min(x + dash, x1), y1)], fill=color, width=width)
    for y in range(int(y0), int(y1), dash * 2):
        d.line([(x0, y), (x0, min(y + dash, y1))], fill=color, width=width)
        d.line([(x1, y), (x1, min(y + dash, y1))], fill=color, width=width)


def section_title(y, text):
    d.line([(40, y + 30), (W - 40, y + 30)], fill=(210, 210, 205), width=2)
    tw = d.textlength(text, font=font(40), direction="rtl")
    d.rectangle([W / 2 - tw / 2 - 20, y, W / 2 + tw / 2 + 20, y + 60], fill=BG)
    ku(W / 2, y + 6, text, 40)


# =====================================================================
# Title
# =====================================================================
ku(W / 2, 26, "لەشێ ڕۆبۆتی", 66)
ku(W / 2, 112, "2 قات: خوارێ کارەبە و مۆتۆر، سەرێ مێشک و سەر", 30, GREY)

# =====================================================================
# 1) Side view (front of the robot is on the RIGHT)
# =====================================================================
section_title(170, "١. ژ لایێ ڤە")

LOW_Y, UP_Y = 700, 560              # top of the lower / upper plate
PX0, PX1 = 260, 840                 # plate length
T = 16                              # plate thickness

# standoffs between the floors
for sx in (285, 520, 815):
    d.rectangle([sx - 7, UP_Y + T, sx + 7, LOW_Y], fill=(200, 170, 80), outline=INK, width=2)

# lower floor parts: L298N (rear) + battery holder (middle)
d.rectangle([300, LOW_Y - 52, 450, LOW_Y], fill=PCB_RED, outline=INK, width=3)
d.rectangle([330, LOW_Y - 80, 420, LOW_Y - 52], fill=(30, 30, 30), outline=INK, width=2)   # heatsink
d.rounded_rectangle([480, LOW_Y - 60, 760, LOW_Y], radius=10, fill=(50, 50, 56), outline=INK, width=3)
d.rounded_rectangle([495, LOW_Y - 50, 745, LOW_Y - 12], radius=18, fill=YELLOW, outline=INK, width=2)

# plates
for y in (UP_Y, LOW_Y):
    d.rounded_rectangle([PX0, y, PX1, y + T], radius=6, fill=PLATE, outline=PLATE_EDGE, width=3)

# motor under the rear of the lower plate, wheel on it
d.rectangle([290, LOW_Y + T, 450, LOW_Y + T + 46], fill=YELLOW, outline=INK, width=3)
WCX, WCY, WR = 360, LOW_Y + T + 23, 95
d.ellipse([WCX - WR, WCY - WR, WCX + WR, WCY + WR], fill=TIRE, outline=INK, width=3)
d.ellipse([WCX - 55, WCY - 55, WCX + 55, WCY + 55], fill=(255, 225, 90), outline=INK, width=3)
d.ellipse([WCX - 12, WCY - 12, WCX + 12, WCY + 12], fill=(240, 240, 240), outline=INK, width=2)
GROUND = WCY + WR

# caster wheel under the front
d.rectangle([760, LOW_Y + T, 800, GROUND - 52], fill=(180, 180, 185), outline=INK, width=3)
d.ellipse([750, GROUND - 60, 810, GROUND], fill=(210, 210, 215), outline=INK, width=3)

# ground line
d.line([(150, GROUND + 2), (930, GROUND + 2)], fill=(150, 150, 150), width=4)

# upper floor parts: ESP32 (middle) + buck converter (rear)
d.rectangle([300, UP_Y - 22, 380, UP_Y], fill=(70, 160, 220), outline=INK, width=2)      # buck
d.rectangle([420, UP_Y - 26, 640, UP_Y], fill=(30, 30, 30), outline=INK, width=2)         # ESP32
d.rectangle([470, UP_Y - 42, 560, UP_Y - 26], fill=(200, 200, 205), outline=INK, width=2)  # metal can

# IR sensor at the front edge, looking forward
d.rectangle([820, UP_Y - 30, 880, UP_Y], fill=PCB_BLUE, outline=INK, width=2)
for k, c in enumerate(((240, 240, 240), (40, 40, 40))):
    d.rounded_rectangle([878, UP_Y - 28 + k * 14, 900, UP_Y - 16 + k * 14], radius=5, fill=c, outline=INK)

# servo neck + OLED head
d.rectangle([690, UP_Y - 70, 760, UP_Y], fill=SERVO, outline=INK, width=3)
d.rectangle([712, UP_Y - 100, 738, UP_Y - 70], fill=(240, 240, 240), outline=INK, width=2)
HX0, HY0, HX1, HY1 = 640, 300, 810, UP_Y - 100
d.rounded_rectangle([HX0, HY0, HX1, HY1], radius=18, fill=(45, 50, 62), outline=INK, width=4)
d.rounded_rectangle([HX0 + 16, HY0 + 22, HX1 - 16, HY1 - 22], radius=8, fill=(10, 14, 22))
for ex in (HX0 + 40, HX0 + 100):
    d.rounded_rectangle([ex, HY0 + 48, ex + 34, HY0 + 92], radius=8, fill=EYE)

en(930, GROUND - 40, "→", 52, GREY, anchor="ra")
ku(930, GROUND - 90, "پێش", 30, GREY, anchor="ra")

# labels
leader(HX0, HY0 + 40, 600, 285, "سەر: OLED", "left")
leader(725, UP_Y - 40, 600, 420, "ستوو: SG90", "left")
leader(470, UP_Y - 13, 250, 470, "ESP32", "left")
leader(PX0, UP_Y + 8, 210, 540, "قاتێ سەرێ", "left", PLATE_EDGE)
leader(PX0, LOW_Y + 8, 210, 640, "قاتێ خوارێ", "left", PLATE_EDGE)
leader(620, LOW_Y - 30, 1000, 620, "باتری", "right")
leader(880, UP_Y - 20, 1000, 470, "IR", "right")
leader(780, GROUND - 30, 1000, 800, "چەرخا ئازاد", "right")
leader(WCX + 40, WCY + 70, 640, 880, "چەرخ + مۆتۆرا زەر", "left")

# =====================================================================
# 2) Both floors from above (front = UP)
# =====================================================================
TOP_Y0 = 940
section_title(TOP_Y0, "٢. ژ سەری ڤە")


def floor(cx, y0, title):
    x0, x1, y1 = cx - 180, cx + 180, y0 + 480
    d.rounded_rectangle([x0, y0, x1, y1], radius=26, fill=PLATE, outline=PLATE_EDGE, width=4)
    for hx, hy in ((x0 + 22, y0 + 22), (x1 - 22, y0 + 22), (x0 + 22, y1 - 22), (x1 - 22, y1 - 22), (cx, y0 + 240)):
        d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=(200, 170, 80), outline=INK, width=2)
    ku(cx, y1 + 18, title, 34, PLATE_EDGE)
    en(cx - 30, y0 - 50, "↑", 34, GREY)
    ku(cx + 10, y0 - 46, "پێش", 26, GREY, anchor="la")
    return x0, y0, x1, y1


# lower floor
LCX, FY0 = 280, TOP_Y0 + 120
x0, y0, x1, y1 = floor(LCX, FY0, "قاتێ خوارێ")
# wheels at the rear sides
for wx in (x0 - 52, x1 + 6):
    d.rounded_rectangle([wx, y1 - 190, wx + 46, y1 - 30], radius=10, fill=TIRE, outline=INK, width=3)
# motors under the plate (dashed)
dashed_rect([x0 + 10, y1 - 150, LCX - 20, y1 - 70], (180, 140, 0))
dashed_rect([LCX + 20, y1 - 150, x1 - 10, y1 - 70], (180, 140, 0))
# caster under the front (dashed circle)
for a in range(0, 360, 30):
    d.arc([LCX - 32, y0 + 38, LCX + 32, y0 + 102], start=a, end=a + 15, fill=GREY, width=4)
# battery in the middle, L298N at the rear, switch on the side
d.rounded_rectangle([LCX - 120, y0 + 140, LCX + 120, y0 + 280], radius=12, fill=(50, 50, 56), outline=INK, width=3)
d.rounded_rectangle([LCX - 105, y0 + 155, LCX + 105, y0 + 200], radius=20, fill=YELLOW, outline=INK, width=2)
d.rounded_rectangle([LCX - 105, y0 + 220, LCX + 105, y0 + 265], radius=20, fill=YELLOW, outline=INK, width=2)
d.rectangle([LCX - 75, y1 - 140, LCX + 75, y1 - 40], fill=PCB_RED, outline=INK, width=3)
en(LCX, y1 - 108, "L298N", 26, (255, 255, 255))
d.rounded_rectangle([x1 - 40, y0 + 180, x1 - 4, y0 + 230], radius=6, fill=(240, 240, 240), outline=INK, width=3)
ku(LCX, y0 + 290, "باتری", 26, INK)
ku(x1 - 22, y0 + 236, "سویچ", 20, INK)

# upper floor
UCX = 800
x0, y0, x1, y1 = floor(UCX, FY0, "قاتێ سەرێ")
# OLED head on the servo, at the front
d.rectangle([UCX - 40, y0 + 70, UCX + 40, y0 + 120], fill=SERVO, outline=INK, width=3)
d.rounded_rectangle([UCX - 85, y0 + 16, UCX + 85, y0 + 64], radius=10, fill=(45, 50, 62), outline=INK, width=3)
ku(UCX, y0 + 128, "SG90 + OLED", 22, INK)
# IR sensor at the front edge
d.rectangle([x1 - 90, y0 - 10, x1 - 30, y0 + 40], fill=PCB_BLUE, outline=INK, width=2)
en(x1 - 60, y0 + 46, "IR", 22, INK)
# ESP32 in the middle
d.rectangle([UCX - 60, y0 + 180, UCX + 60, y0 + 360], fill=(30, 30, 30), outline=INK, width=3)
d.rectangle([UCX - 35, y0 + 190, UCX + 35, y0 + 250], fill=(200, 200, 205), outline=INK, width=2)
en(UCX, y0 + 290, "ESP32", 24, (255, 255, 255))
d.rectangle([UCX - 18, y0 + 352, UCX + 18, y0 + 372], fill=(170, 170, 175), outline=INK, width=2)  # USB at the rear
# buck converter at the rear
d.rectangle([x0 + 30, y1 - 120, x0 + 130, y1 - 40], fill=(70, 160, 220), outline=INK, width=3)
en(x0 + 80, y1 - 96, "5V", 26, INK)
# cable hole
d.ellipse([UCX + 90, y1 - 110, UCX + 150, y1 - 50], fill=(230, 240, 245), outline=INK, width=3)
ku(UCX + 120, y1 - 44, "کونا وایەران", 18, GREY)

# =====================================================================
# 3) What you need + tips
# =====================================================================
BY0 = 1640
d.rounded_rectangle([40, BY0, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, BY0 + 20, "چ پێدڤیە؟", 40, INK, anchor="ra")
items = [
    "2 پلێت، درێژی 20 و پانی 15 سانتیم",
    "پلێت: ئەکریلیک، تەختە، یان کارتۆنێ ستویر",
    "4 ستوینێن 4cm (Standoff) + پیچێن M3",
    "شریتێ دو ڕوو + بەستکێن پلاستیکی (Zip tie)",
]
for k, t in enumerate(items):
    ku(W - 80, BY0 + 82 + k * 50, "•  " + t, 28, INK, anchor="ra")
BY0 += 50
ku(W - 80, BY0 + 250, "ئامۆژگاری:", 34, RED, anchor="ra")
tips = [
    "باتریێ گران ل قاتێ خوارێ و ل ناڤەڕاستێ دانە",
    "USB یا ESP32 بەرەڤ پشتێ بیت، دا ب ساناهی Upload بکەی",
]
for k, t in enumerate(tips):
    ku(W - 80, BY0 + 300 + k * 46, "•  " + t, 27, INK, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT)
