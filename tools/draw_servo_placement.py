"""Where to put the MG90S and SG90 servos on the walking robot, with Kurdish (Badini) labels.

Output: images/servo_placement.png
Usage: python3 tools/draw_servo_placement.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "servo_placement.png"
W, H = 1080, 2120
BG = (250, 250, 246)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BROWN = (120, 70, 35)
ORANGE = (245, 145, 20)
SG_BLUE = (50, 95, 225)
SG_LIGHT = (120, 160, 245)
MG_DARK = (55, 52, 58)
MG_LABEL = (200, 40, 150)
SHELL = (245, 245, 240)
SHELL_EDGE = (70, 70, 75)
EYE = (90, 200, 255)
PCB_BLUE = (35, 80, 170)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def section_title(y, text):
    d.line([(40, y + 30), (W - 40, y + 30)], fill=(210, 210, 205), width=2)
    tw = d.textlength(text, font=font(40), direction="rtl")
    d.rectangle([W / 2 - tw / 2 - 20, y, W / 2 + tw / 2 + 20, y + 60], fill=BG)
    ku(W / 2, y + 6, text, 40)


def servo(x, y, s, kind, wires=True):
    """Draw a micro servo (side view). (x, y) = top-left of the body, s = scale. kind: 'MG90S' or 'SG90'."""
    body = MG_DARK if kind == "MG90S" else SG_BLUE
    light = (90, 88, 95) if kind == "MG90S" else SG_LIGHT
    bw, bh = 230 * s, 200 * s
    # mounting ears
    d.rectangle([x - 40 * s, y + 40 * s, x + bw + 40 * s, y + 75 * s], fill=body, outline=INK, width=3)
    for ex in (x - 22 * s, x + bw + 22 * s):
        d.ellipse([ex - 8 * s, y + 50 * s, ex + 8 * s, y + 66 * s], fill=BG, outline=INK, width=2)
    # body
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=10 * s, fill=body, outline=INK, width=3)
    # top bump + output shaft
    d.rounded_rectangle([x + 20 * s, y - 40 * s, x + 130 * s, y + 4], radius=16 * s, fill=light, outline=INK, width=3)
    d.rectangle([x + 55 * s, y - 75 * s, x + 95 * s, y - 38 * s],
                fill=(30, 30, 30) if kind == "MG90S" else (245, 245, 245), outline=INK, width=2)
    # label
    lab_fill = MG_LABEL if kind == "MG90S" else (250, 240, 170)
    d.rectangle([x + 25 * s, y + 95 * s, x + bw - 25 * s, y + 170 * s], fill=lab_fill, outline=INK, width=2)
    d.text((x + bw / 2, y + 112 * s), kind, font=font(int(40 * s)),
           fill=(255, 255, 255) if kind == "MG90S" else INK, anchor="ma")
    if wires:
        wy = y + 150 * s
        for k, c in enumerate((BROWN, RED, ORANGE)):
            yy = wy + (k - 1) * 14 * s
            d.line([(x + bw, yy), (x + bw + 110 * s, yy)], fill=c, width=max(4, int(10 * s)))
        d.rectangle([x + bw + 110 * s, wy - 28 * s, x + bw + 150 * s, wy + 28 * s], fill=(30, 30, 30), outline=INK, width=2)


# =====================================================================
# Title
# =====================================================================
ku(W / 2, 24, "MG90S و SG90 ل کیرێ؟", 60)
ku(W / 2, 110, "بۆ ڕۆبۆتێ ب پێیان", 32, GREY)

# =====================================================================
# 1) The two servos side by side
# =====================================================================
section_title(170, "١. هەردو سێرڤۆ")
servo(600, 330, 1.0, "MG90S")
servo(110, 330, 1.0, "SG90")
ku(760, 560, "MG90S", 34, MG_DARK)
ku(760, 604, "دەندکێن ئاسن، ب هێزترە", 26, INK)
ku(270, 560, "SG90", 34, SG_BLUE)
ku(270, 604, "دەندکێن پلاستیک، سڤکترە", 26, INK)

# wire colours (same for both)
d.rounded_rectangle([70, 660, W - 70, 840], radius=18, fill=(255, 255, 255), outline=INK, width=3)
ku(W - 100, 676, "وایەر ل هەردوکان ئێکن:", 30, INK, anchor="ra")
rows = [(BROWN, "قاوەیی", "GND"), (RED, "سۆر", "5V"), (ORANGE, "پرتەقاڵی", "GPIO")]
for k, (c, name, dest) in enumerate(rows):
    cx = W - 190 - k * 300
    d.rounded_rectangle([cx - 20, 740, cx + 40, 770], radius=6, fill=c, outline=INK, width=2)
    ku(cx - 34, 734, name, 28, INK, anchor="ra")
    en(cx + 10, 784, "→ " + dest, 26, GREY)

# =====================================================================
# 2) Placement on the robot (seen from the front)
# =====================================================================
PY = 890
section_title(PY, "٢. ل سەر ڕۆبۆتی")
CX = 540
HX0, HY0, HX1, HY1 = CX - 210, PY + 110, CX + 210, PY + 470
d.rounded_rectangle([HX0, HY0, HX1, HY1], radius=36, fill=SHELL, outline=SHELL_EDGE, width=6)
d.rounded_rectangle([CX - 140, HY0 + 36, CX + 140, HY0 + 186], radius=16, fill=(45, 50, 62), outline=INK, width=4)
d.rounded_rectangle([CX - 124, HY0 + 52, CX + 124, HY0 + 170], radius=10, fill=(10, 14, 22))
for ex in (CX - 85, CX + 30):
    d.rounded_rectangle([ex, HY0 + 74, ex + 55, HY0 + 150], radius=14, fill=EYE)
d.rectangle([CX - 46, HY0 + 205, CX + 46, HY0 + 243], fill=PCB_BLUE, outline=INK, width=3)

# hip servos (SG90) at the bottom of the body
hip_boxes = []
for sx in (CX - 170, CX + 40):
    box = [sx, HY1 - 100, sx + 130, HY1 - 25]
    d.rounded_rectangle(box, radius=8, fill=SG_BLUE, outline=INK, width=4)
    en(sx + 65, HY1 - 78, "SG90", 24, (255, 255, 255))
    hip_boxes.append(box)

# legs with foot servos (MG90S)
LEG_W = 110
legs = (CX - 160, CX + 50)
LY0, LY1 = HY1, HY1 + 250
foot_boxes = []
for lx in legs:
    d.rounded_rectangle([lx, LY0, lx + LEG_W, LY1], radius=14, fill=SHELL, outline=SHELL_EDGE, width=5)
    box = [lx + 10, LY1 - 110, lx + LEG_W - 10, LY1 - 30]
    d.rounded_rectangle(box, radius=8, fill=MG_DARK, outline=INK, width=4)
    en((box[0] + box[2]) / 2, box[1] + 10, "MG90S", 20, (255, 255, 255))
    foot_boxes.append(box)
FY0, FY1 = LY1, LY1 + 40
d.rounded_rectangle([legs[0] - 60, FY0, legs[0] + LEG_W + 10, FY1], radius=12, fill=SHELL, outline=SHELL_EDGE, width=5)
d.rounded_rectangle([legs[1] - 10, FY0, legs[1] + LEG_W + 60, FY1], radius=12, fill=SHELL, outline=SHELL_EDGE, width=5)
d.line([(150, FY1 + 4), (930, FY1 + 4)], fill=(150, 150, 150), width=4)


def tag(box, side, title, pin, color):
    """Label a servo on the robot: line to the side, title + pin."""
    py_ = (box[1] + box[3]) / 2
    if side == "left":
        px_, tx = box[0], 250
        d.line([(px_, py_), (tx, py_)], fill=color, width=4)
        ku(tx - 10, py_ - 36, title, 26, color, anchor="ra")
        en(tx - 10, py_ + 2, pin, 26, ORANGE, anchor="ra")
    else:
        px_, tx = box[2], 830
        d.line([(px_, py_), (tx, py_)], fill=color, width=4)
        ku(tx + 10, py_ - 36, title, 26, color, anchor="la")
        en(tx + 10, py_ + 2, pin, 26, ORANGE, anchor="la")


# From the front, the robot's LEFT is on the viewer's RIGHT.
tag(hip_boxes[1], "right", "کەمەرا چەپێ", "GPIO13", SG_BLUE)
tag(hip_boxes[0], "left", "کەمەرا ڕاستێ", "GPIO14", SG_BLUE)
tag(foot_boxes[1], "right", "پێیێ چەپێ", "GPIO27", MG_DARK)
tag(foot_boxes[0], "left", "پێیێ ڕاستێ", "GPIO26", MG_DARK)
ku(W / 2, FY1 + 24, "ژ پێشیێ ڤە: چەپێ ڕۆبۆتی ل ڕاستا تە یە", 24, GREY)

# =====================================================================
# 3) Why + table
# =====================================================================
TY = 1760
d.rounded_rectangle([40, TY, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, TY + 20, "بۆچی؟", 38, INK, anchor="ra")
lines = [
    ("سێرڤۆیێن پێیان هەمی گرانیا ڕۆبۆتی هەلدگرن", INK),
    ("لەو MG90S یێ ب هێز ل پێیان دانە", MG_DARK),
    ("سێرڤۆیێن کەمەرێ کارێ سڤکتر دکەن، لەو SG90 بەسە", SG_BLUE),
    ("ئەگەر 4 دانە MG90S هەبن، هەر 4 بکار بینە", GREY),
]
for k, (t, c) in enumerate(lines):
    ku(W - 80, TY + 84 + k * 56, "•  " + t, 28, c, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
