"""Two-legged walking robot (4 servos, no wheels) with Kurdish (Badini) labels.

Front view, what each servo does, servo/power wiring, and a parts list.
Output: images/robot_walker.png
Usage: python3 tools/draw_walker.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "robot_walker.png"
W, H = 1080, 2830
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


def mini(cx, ground_y, lean):
    """Tiny BACK view (so the robot's left is on the left). lean: 'right' or 'left'.

    The robot leans over the standing foot; the other foot is lifted (orange).
    """
    LW, LH = 220, 230
    layer = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    bx = LW / 2
    ld.rounded_rectangle([bx - 62, 20, bx + 62, 130], radius=12, fill=SHELL, outline=SHELL_EDGE, width=3)
    ld.rectangle([bx - 30, 45, bx + 30, 75], fill=(215, 215, 210), outline=SHELL_EDGE, width=2)   # back panel
    for side in ("left", "right"):
        lx = bx - 48 if side == "left" else bx + 18
        lifted = side != lean
        lift = 26 if lifted else 0
        color = ARROW if lifted else SHELL_EDGE
        ld.rectangle([lx, 130, lx + 30, 190 - lift], fill=SHELL, outline=color, width=3)
        ld.rectangle([lx - 12, 190 - lift, lx + 42, 202 - lift], fill=(200, 200, 195), outline=color, width=3)
    # rotate around the standing foot
    pivot_x = bx + 33 if lean == "right" else bx - 33
    angle = -12 if lean == "right" else 12
    layer = layer.rotate(angle, center=(pivot_x, 202), resample=Image.BICUBIC)
    img.paste(layer, (int(cx - LW / 2), int(ground_y - 202)), layer)
    d.line([(cx - 95, ground_y + 2), (cx + 95, ground_y + 2)], fill=(150, 150, 150), width=3)


def footprints(cx, y, ahead, lifted):
    """Top view of both feet. ahead: which foot is in front. lifted: which foot is in the air."""
    for side in ("left", "right"):
        fx = cx - 46 if side == "left" else cx + 14
        fy = y - 26 if side == ahead else y
        if side == lifted:
            d.rounded_rectangle([fx, fy, fx + 32, fy + 54], radius=10, outline=ARROW, width=4)
        else:
            d.rounded_rectangle([fx, fy, fx + 32, fy + 54], radius=10, fill=(150, 150, 145), outline=INK, width=2)
    en(cx + 70, y - 30, "↑", 26, GREY)


# (lean, foot ahead, lifted foot, number, caption)
frames = [
    ("right", None, "left", "١", ("خوار دبیت", "بۆ ڕاستێ")),
    ("right", "left", "left", "٢", ("پێیێ چەپێ", "دچیتە پێش")),
    ("left", "left", "right", "٣", ("خوار دبیت", "بۆ چەپێ")),
    ("left", "right", "right", "٤", ("پێیێ ڕاستێ", "دچیتە پێش")),
]
ku(W / 2, WY0 + 70, "ژ پشتێ ڤە (چەپ ل چەپێ یە)", 24, GREY)
for k, (lean, ahead, lifted, num, lines) in enumerate(frames):
    cx = W - 150 - k * 250
    mini(cx, WY0 + 300, lean)
    footprints(cx, WY0 + 350, ahead, lifted)
    en(cx, WY0 + 420, num, 34, ARROW)
    for j, t in enumerate(lines):
        ku(cx, WY0 + 464 + j * 34, t, 26, INK)
ku(W / 2, WY0 + 545, "پێیێ پرتەقاڵی = د هەوا دا. دووبارە دکەت... و ب ڕێڤە دچیت!", 26, GREY)

# =====================================================================
# 3) Wiring
# =====================================================================
WR0 = 1590
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
PY0 = 2340
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
