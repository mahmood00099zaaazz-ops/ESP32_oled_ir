"""Step-by-step build guide for the robot body, with Kurdish (Badini) text.

Each step shows the same side view of the robot, built one stage further.
Output: images/robot_build_steps.png
Usage: python3 tools/draw_build_steps.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "robot_build_steps.png"
W = 1080
PANEL_H = 430
STEPS_Y0 = 190
N_STEPS = 6
H = STEPS_Y0 + N_STEPS * (PANEL_H + 24) + 260

BG = (250, 250, 246)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
GREEN = (25, 145, 65)
NEW = (255, 120, 0)            # outline colour for the parts added in this step
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


class Side:
    """Draws the robot side view in model coordinates, scaled into a panel.

    Model coordinates match tools/draw_robot_body.py (front of the robot on the right).
    """

    MX0, MY0 = 200, 240                  # model point mapped to the panel origin

    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def p(self, x, y):
        return (self.ox + (x - self.MX0) * self.s, self.oy + (y - self.MY0) * self.s)

    def box(self, x0, y0, x1, y1):
        (a, b), (c, e) = self.p(x0, y0), self.p(x1, y1)
        return [a, b, c, e]

    def rect(self, x0, y0, x1, y1, fill, new=False, r=0):
        outline, width = (NEW, 5) if new else (INK, 2)
        if r:
            d.rounded_rectangle(self.box(x0, y0, x1, y1), radius=r * self.s, fill=fill, outline=outline, width=width)
        else:
            d.rectangle(self.box(x0, y0, x1, y1), fill=fill, outline=outline, width=width)

    def ellipse(self, x0, y0, x1, y1, fill, new=False):
        outline, width = (NEW, 5) if new else (INK, 2)
        d.ellipse(self.box(x0, y0, x1, y1), fill=fill, outline=outline, width=width)


LOW_Y, UP_Y, T = 700, 560, 16
PX0, PX1 = 260, 840
WCX, WCY, WR = 360, LOW_Y + T + 23, 95
GROUND = WCY + WR


def draw_robot(sv, stage):
    """Draw everything up to `stage`; parts added at exactly `stage` get an orange outline."""
    n = lambda k: stage == k             # noqa: E731  (is this the step that adds the part?)

    d.line([sv.p(170, GROUND + 2), sv.p(930, GROUND + 2)], fill=(160, 160, 160), width=3)

    # 5: standoffs + upper plate (drawn first so the lower floor parts sit in front)
    if stage >= 5:
        for sx in (285, 520, 815):
            sv.rect(sx - 7, UP_Y + T, sx + 7, LOW_Y, (200, 170, 80), n(5))

    # 4: lower floor electronics
    if stage >= 4:
        sv.rect(300, LOW_Y - 52, 450, LOW_Y, PCB_RED, n(4))
        sv.rect(330, LOW_Y - 80, 420, LOW_Y - 52, (30, 30, 30), n(4))
        sv.rect(480, LOW_Y - 60, 760, LOW_Y, (50, 50, 56), n(4), r=10)
        sv.rect(495, LOW_Y - 50, 745, LOW_Y - 12, YELLOW, False, r=18)

    # 1: lower plate (in step 1 also show it from above, with its holes)
    if stage == 1:
        sv.rect(PX0, 360, PX1, 620, PLATE, True, r=24)
        for hx, hy in ((PX0 + 30, 390), (PX1 - 30, 390), (PX0 + 30, 590), (PX1 - 30, 590), ((PX0 + PX1) / 2, 490)):
            sv.ellipse(hx - 12, hy - 12, hx + 12, hy + 12, (250, 250, 246))
        x, y = sv.p((PX0 + PX1) / 2, 330)
        en(x, y - 30, "20 cm", 24, GREY)
        x, y = sv.p(PX0 - 12, 490)
        en(x, y - 12, "15", 24, GREY, anchor="ra")
    sv.rect(PX0, LOW_Y, PX1, LOW_Y + T, PLATE, n(1), r=6)

    # 2: motor + wheel
    if stage >= 2:
        sv.rect(290, LOW_Y + T, 450, LOW_Y + T + 46, YELLOW, n(2))
        sv.ellipse(WCX - WR, WCY - WR, WCX + WR, WCY + WR, TIRE, n(2))
        sv.ellipse(WCX - 55, WCY - 55, WCX + 55, WCY + 55, (255, 225, 90))
        sv.ellipse(WCX - 12, WCY - 12, WCX + 12, WCY + 12, (240, 240, 240))

    # 3: caster
    if stage >= 3:
        sv.rect(760, LOW_Y + T, 800, GROUND - 52, (180, 180, 185), n(3))
        sv.ellipse(750, GROUND - 60, 810, GROUND, (210, 210, 215), n(3))

    # 5: upper plate + its parts
    if stage >= 5:
        sv.rect(PX0, UP_Y, PX1, UP_Y + T, PLATE, n(5), r=6)
        sv.rect(300, UP_Y - 22, 380, UP_Y, (70, 160, 220), n(5))                 # buck
        sv.rect(420, UP_Y - 26, 640, UP_Y, (30, 30, 30), n(5))                   # ESP32
        sv.rect(470, UP_Y - 42, 560, UP_Y - 26, (200, 200, 205))
        sv.rect(820, UP_Y - 30, 880, UP_Y, PCB_BLUE, n(5))                       # IR
        sv.rect(878, UP_Y - 28, 900, UP_Y - 16, (240, 240, 240))
        sv.rect(878, UP_Y - 14, 900, UP_Y - 2, (40, 40, 40))

    # 6: servo + OLED head
    if stage >= 6:
        sv.rect(690, UP_Y - 70, 760, UP_Y, SERVO, n(6))
        sv.rect(712, UP_Y - 100, 738, UP_Y - 70, (240, 240, 240), n(6))
        sv.rect(640, 300, 810, UP_Y - 100, (45, 50, 62), n(6), r=18)
        sv.rect(656, 322, 794, UP_Y - 122, (10, 14, 22), False, r=8)
        for ex in (680, 740):
            sv.rect(ex, 348, ex + 34, 392, EYE, False, r=8)


STEPS = [
    ("پلێتا خوارێ ئامادە بکە",
     ["پلێتەکێ 20 ل سەر 15 سانتیم بڕە", "4 کونان ل سووچان بکە", "کونەکێ ب ناڤەڕاستێ ژی"]),
    ("مۆتۆر و چەرخان دانە",
     ["2 مۆتۆرێن زەر ل بن پلێتێ", "ل پشتێ، ئێک چەپ و ئێک ڕاست", "ب پیچ یان ب شریتێ دو ڕوو"]),
    ("چەرخا ئازاد دانە",
     ["ل بن پلێتێ، ل ناڤەڕاستا پێشیێ", "دڤێت ب بلنداهیا چەرخان بیت", "دا ڕۆبۆت ڕاست بڕاوەستیت"]),
    ("باتری و L298N دانە",
     ["باتری ل ناڤەڕاستێ، L298N ل پشتێ", "سویچێ ل لایەکی دانە", "وایەرێن مۆتۆران ب L298N ڤە بکە"]),
    ("قاتێ سەرێ دانە",
     ["4 ستوینێن 4cm ل سووچان دانە", "پلێتا دووێ ل سەر دانە", "ESP32، Buck و IR ل سەر دانە"]),
    ("سەرێ ڕۆبۆتی دانە",
     ["SG90 ل پێشیێ دانە", "OLED ل سەر SG90 دانە", "ڕۆبۆت ئامادەیە! ✓"]),
]

# ---------------- Title ----------------
ku(W / 2, 26, "چاوا ڕۆبۆتی چێ بکەی", 62)
ku(W / 2, 108, "6 گاڤ، ئێک ب ئێک", 34, GREY)
LEGEND = "پارچا نوو د ڤێ گاڤێ دا"
lw = d.textlength(LEGEND, font=font(26), direction="rtl")
ku(W / 2 + lw / 2 - 25, 150, LEGEND, 26, GREY, anchor="ra")
d.rectangle([W / 2 + lw / 2 - 10, 156, W / 2 + lw / 2 + 26, 176], fill=BG, outline=NEW, width=5)

# ---------------- Steps ----------------
for i, (title, lines) in enumerate(STEPS):
    stage = i + 1
    y0 = STEPS_Y0 + i * (PANEL_H + 24)
    done = stage == N_STEPS
    d.rounded_rectangle([40, y0, W - 40, y0 + PANEL_H], radius=24,
                        fill=(236, 248, 238) if done else (255, 255, 255),
                        outline=GREEN if done else INK, width=4)
    # step number
    cx, cy = W - 100, y0 + 64
    d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=GREEN if done else INK)
    en(cx, cy - 26, str(stage), 46, (255, 255, 255))
    # text (right side)
    ku(W - 160, y0 + 40, title, 38, INK, anchor="ra")
    for k, t in enumerate(lines):
        ku(W - 70, y0 + 140 + k * 62, "•  " + t, 28, INK, anchor="ra")
    # drawing (left side)
    draw_robot(Side(60, y0 + 30, 0.55), stage)

# ---------------- Bottom tips ----------------
TY = STEPS_Y0 + N_STEPS * (PANEL_H + 24) + 10
d.rounded_rectangle([40, TY, W - 40, H - 30], radius=22, fill=(255, 245, 230), outline=NEW, width=4)
ku(W - 80, TY + 22, "بۆ کو ڕۆبۆت ب هێز بیت:", 34, INK, anchor="ra")
tips = [
    "پیچان باش گرێ بدە، دا ل دەمێ ب ڕێڤەچوونێ نەلڤن",
    "وایەران ب Zip tie کۆم بکە، دا نەکەڤنە د ناڤ چەرخان دا",
]
for k, t in enumerate(tips):
    ku(W - 80, TY + 90 + k * 52, "•  " + t, 28, INK, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
