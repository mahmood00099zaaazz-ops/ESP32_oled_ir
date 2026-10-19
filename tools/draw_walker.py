"""Two-legged walking robot (4 servos, no wheels) with Kurdish (Badini) labels.

Front view, what each servo does, servo/power wiring, and a parts list.
Output: images/robot_walker.png
Usage: python3 tools/draw_walker.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "robot_walker.png"
W, H = 1080, 2720
BG = (250, 250, 246)
INK = (25, 25, 30)
GREY = (95, 95, 95)
RED = (215, 35, 35)
BLACK = (15, 15, 15)
GREEN = (25, 145, 65)
ORANGE = (240, 140, 20)
SHELL = (245, 245, 240)
SHELL_EDGE = (70, 70, 75)
SERVO = (60, 100, 220)
EYE = (90, 200, 255)
PCB_BLUE = (35, 80, 170)
ARROW = (255, 120, 0)

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


def servo_block(x0, y0, x1, y1):
    d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=SERVO, outline=INK, width=3)
    for k in (0.25, 0.5, 0.75):                 # mounting ears look
        pass


def curved_arrow(box, start, end, color=ARROW, width=7):
    """Arc with an arrow head at the end angle."""
    import math
    d.arc(box, start=start, end=end, fill=color, width=width)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    rx, ry = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    a = math.radians(end)
    px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
    # tangent direction (increasing angle)
    tx, ty = -rx * math.sin(a), ry * math.cos(a)
    n = math.hypot(tx, ty)
    tx, ty = tx / n, ty / n
    nx, ny = -ty, tx
    size = 18
    d.polygon([(px + tx * size, py + ty * size), (px - nx * size * 0.7, py - ny * size * 0.7),
               (px + nx * size * 0.7, py + ny * size * 0.7)], fill=color)


# =====================================================================
# Title
# =====================================================================
ku(W / 2, 24, "ڕۆبۆتێ ب پێیان", 68)
ku(W / 2, 112, "بێ تایە، ب 4 سێرڤۆیان دچیت", 32, GREY)

# =====================================================================
# 1) Front view
# =====================================================================
section_title(180, "١. ژ پێشیێ ڤە")
CX = 540
# head/body box
HX0, HY0, HX1, HY1 = CX - 200, 290, CX + 200, 640
d.rounded_rectangle([HX0, HY0, HX1, HY1], radius=36, fill=SHELL, outline=SHELL_EDGE, width=6)
# OLED face
d.rounded_rectangle([CX - 140, HY0 + 40, CX + 140, HY0 + 200], radius=16, fill=(45, 50, 62), outline=INK, width=4)
d.rounded_rectangle([CX - 124, HY0 + 56, CX + 124, HY0 + 184], radius=10, fill=(10, 14, 22))
for ex in (CX - 85, CX + 30):
    d.rounded_rectangle([ex, HY0 + 80, ex + 55, HY0 + 160], radius=14, fill=EYE)
# IR sensor under the face
d.rectangle([CX - 50, HY0 + 225, CX + 50, HY0 + 265], fill=PCB_BLUE, outline=INK, width=3)
d.ellipse([CX - 36, HY0 + 230, CX - 6, HY0 + 260], fill=(240, 240, 240), outline=INK, width=2)
d.ellipse([CX + 6, HY0 + 230, CX + 36, HY0 + 260], fill=(40, 40, 40), outline=INK, width=2)
# hip servos inside the bottom of the body (shown through)
for sx in (CX - 150, CX + 50):
    servo_block(sx, HY1 - 70, sx + 100, HY1 - 20)
    d.ellipse([sx + 40, HY1 - 25, sx + 60, HY1 - 5], fill=(240, 240, 240), outline=INK, width=2)

# legs
LEG_W = 90
legs = (CX - 145, CX + 55)
LY0, LY1 = HY1, HY1 + 190
for lx in legs:
    d.rounded_rectangle([lx, LY0, lx + LEG_W, LY1], radius=14, fill=SHELL, outline=SHELL_EDGE, width=5)
    # ankle servo inside the leg
    servo_block(lx + 12, LY1 - 80, lx + LEG_W - 12, LY1 - 20)
# feet
FY0, FY1 = LY1, LY1 + 36
feet = ((legs[0] - 50, legs[0] + LEG_W + 10), (legs[1] - 10, legs[1] + LEG_W + 50))
for fx0, fx1 in feet:
    d.rounded_rectangle([fx0, FY0, fx1, FY1], radius=12, fill=SHELL, outline=SHELL_EDGE, width=5)
GROUND = FY1 + 4
d.line([(160, GROUND), (920, GROUND)], fill=(150, 150, 150), width=4)

# motion arrows: hip turns the leg, ankle tilts the foot
curved_arrow([legs[1] - 10, LY0 + 30, legs[1] + LEG_W + 10, LY0 + 90], 200, 340)
curved_arrow([feet[0][0] - 20, FY0 - 40, feet[0][0] + 60, FY1 + 30], 120, 230)

leader(CX - 140, HY0 + 120, 300, 300, "ڕوو: OLED", "left")
leader(CX - 50, HY0 + 245, 300, 420, "IR", "left")
leader(CX - 100, HY1 - 45, 300, 560, "سێرڤۆیا کەمەرێ", "left", color=SERVO)
leader(legs[0] + 20, LY1 - 50, 300, 700, "سێرڤۆیا پێ", "left", color=SERVO)
leader(HX1 - 20, HY0 + 300, 1000, 540, "لەش (سندوق)", "right")
leader(legs[1] + LEG_W, LY0 + 60, 1000, 690, "زڤڕینا لاقی", "right", color=ARROW)
leader(feet[1][1] - 20, FY0 + 18, 1000, 800, "پێ", "right")
ku(feet[0][0] - 30, FY0 - 70, "خوارکرنا پێ", 24, ARROW, anchor="ra")

# =====================================================================
# 2) How it walks (4 small frames: tilt, step, tilt, step)
# =====================================================================
WY0 = 960
section_title(WY0, "٢. چاوا دچیت؟")


def mini(cx, cy, tilt, step):
    """Tiny front view. tilt: -1 lean left / 0 / 1 lean right. step: which foot is forward (drawn larger)."""
    s = 0.32
    off = tilt * 14
    d.rounded_rectangle([cx - 200 * s + off, cy - 350 * s, cx + 200 * s + off, cy], radius=10,
                        fill=SHELL, outline=SHELL_EDGE, width=3)
    d.rounded_rectangle([cx - 120 * s + off, cy - 300 * s, cx + 120 * s + off, cy - 180 * s], radius=5, fill=(10, 14, 22))
    for k, lx in enumerate((cx - 110 * s, cx + 30 * s)):
        lift = 18 if (tilt == 1 and k == 0) or (tilt == -1 and k == 1) else 0
        grow = 1.25 if step == k else 1.0
        d.rectangle([lx, cy, lx + 80 * s, cy + 150 * s - lift], fill=SHELL, outline=SHELL_EDGE, width=3)
        fw = 130 * s * grow
        d.rectangle([lx + 40 * s - fw / 2, cy + 150 * s - lift, lx + 40 * s + fw / 2, cy + 175 * s - lift],
                    fill=(200, 200, 195), outline=SHELL_EDGE, width=3)
    d.line([(cx - 90, cy + 175 * s + 2), (cx + 90, cy + 175 * s + 2)], fill=(150, 150, 150), width=3)


frames = [
    (1, None, "١", ("خوار دبیت", "بۆ ڕاستێ")),
    (1, 0, "٢", ("پێیێ چەپێ", "دچیتە پێش")),
    (-1, 0, "٣", ("خوار دبیت", "بۆ چەپێ")),
    (-1, 1, "٤", ("پێیێ ڕاستێ", "دچیتە پێش")),
]
for k, (tilt, step, num, lines) in enumerate(frames):
    cx = W - 150 - k * 250
    mini(cx, WY0 + 230, tilt, step)
    en(cx, WY0 + 300, num, 34, ARROW)
    for j, t in enumerate(lines):
        ku(cx, WY0 + 346 + j * 34, t, 26, INK)
ku(W / 2, WY0 + 430, "دووبارە دکەت... و ب ڤی ڕەنگی ب ڕێڤە دچیت!", 28, GREY)

# =====================================================================
# 3) Wiring
# =====================================================================
WR0 = 1480
section_title(WR0, "٣. وایەر")

rows = [
    ("سێرڤۆیا کەمەرێ چەپێ", "GPIO13"),
    ("سێرڤۆیا کەمەرێ ڕاستێ", "GPIO14"),
    ("سێرڤۆیا پێیێ چەپێ", "GPIO27"),
    ("سێرڤۆیا پێیێ ڕاستێ", "GPIO26"),
    ("OLED (SDA / SCL)", "GPIO21 / 22"),
    ("IR (OUT)", "GPIO34"),
]
TX0, TX1 = 70, W - 70
ty = WR0 + 90
d.rounded_rectangle([TX0, ty, TX1, ty + 60 + len(rows) * 60], radius=16, fill=(255, 255, 255), outline=INK, width=3)
d.rectangle([TX0 + 3, ty + 3, TX1 - 3, ty + 60], fill=(235, 240, 250))
ku(TX1 - 30, ty + 14, "پارچە", 28, INK, anchor="ra")
ku(TX0 + 200, ty + 14, "پینا ESP32", 28, INK)
for k, (part, pin) in enumerate(rows):
    y = ty + 60 + k * 60
    d.line([(TX0, y), (TX1, y)], fill=(220, 220, 220), width=2)
    # Kurdish part names may contain English words; draw them right-aligned as one RTL run
    if k < 4:
        ku(TX1 - 30, y + 14, part, 26, INK, anchor="ra")
    else:
        en(TX1 - 30, y + 14, part, 26, INK, anchor="ra")
    en(TX0 + 200, y + 12, pin, 28, ORANGE if k < 4 else PCB_BLUE)

# power chain
py = ty + 60 + len(rows) * 60 + 50
ku(W - 80, py, "کارەبە:", 30, RED, anchor="ra")
chain = ["2x 18650", "SWITCH", "Buck 5V", "4 servo + ESP32 VIN"]
bx = 70
for k, t in enumerate(chain):
    fnt = font(24)
    tw = d.textlength(t, font=fnt)
    d.rounded_rectangle([bx, py + 52, bx + tw + 30, py + 102], radius=10,
                        fill=(255, 235, 235) if k < 3 else (235, 245, 255), outline=INK, width=3)
    d.text((bx + 15, py + 62), t, font=fnt, fill=INK)
    bx += tw + 30
    if k < len(chain) - 1:
        d.line([(bx + 6, py + 77), (bx + 34, py + 77)], fill=RED, width=6)
        d.polygon([(bx + 44, py + 77), (bx + 30, py + 67), (bx + 30, py + 87)], fill=RED)
        bx += 50
ku(W / 2, py + 120, "وایەرێ سۆر یێ هەر سێرڤۆیەکێ ← 5V، یێ قاوەیی ← GND", 26, INK)

# =====================================================================
# 4) Parts + tips
# =====================================================================
PY0 = 2230
d.rounded_rectangle([40, PY0, W - 40, H - 30], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, PY0 + 20, "چ پێدڤیە؟", 38, INK, anchor="ra")
items = [
    "4 سێرڤۆ: MG90S باشترە ژ SG90، چونکی دەندکێن وێ ئاسنن",
    "لەش: سندوقەکێ سڤک، نێزیکی 10 سانتیم",
    "L298N و مۆتۆرێن زەر پێدڤی نینن!",
]
for k, t in enumerate(items):
    ku(W - 80, PY0 + 80 + k * 48, "•  " + t, 26, INK, anchor="ra")
ku(W - 80, PY0 + 240, "ئامۆژگاری:", 32, RED, anchor="ra")
tips = [
    "ڕۆبۆتی سڤک بکە، دا سێرڤۆ بشێن هەلگرن",
    "Buck دڤێت 3A بیت، چونکی 4 سێرڤۆ پێکڤە کار دکەن",
]
for k, t in enumerate(tips):
    ku(W - 80, PY0 + 292 + k * 48, "•  " + t, 26, INK, anchor="ra")

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
