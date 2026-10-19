"""Draw a close-up wiring diagram for the two yellow TT motors (L298N + 2x18650 + ESP32).

Output: images/motor_wiring.png   Usage: python3 tools/draw_motor_wiring.py (needs Pillow)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "motor_wiring.png"
W, H = 1500, 1090
BG = (250, 250, 247)
INK = (30, 30, 34)
RED = (215, 40, 40)
BLACK = (20, 20, 20)
YELLOW = (255, 210, 40)
SIG = [(20, 150, 160), (40, 110, 220), (30, 150, 70), (140, 70, 190), (130, 80, 40), (20, 150, 160)]

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=False):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


F_T, F_B, F_P, F_N = font(32, True), font(22, True), font(18), font(18)


def wire(pts, color, w=6):
    d.line(pts, fill=color, width=w, joint="curve")


def pdot(x, y, color=INK):
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=color)


def label_left(x, y, t):
    d.text((x + 14, y - 11), t, fill=INK, font=F_P)


def label_right(x, y, t):
    d.text((x - 14 - d.textlength(t, font=F_P), y - 11), t, fill=INK, font=F_P)


def tt_motor(x, y, name, flip=False):
    """Yellow TT gear motor with wheel. (x, y) = top-left of the gearbox. Returns its 2 terminals."""
    # wheel
    wx = x - 70 if not flip else x + 250
    d.rounded_rectangle([wx, y - 40, wx + 60, y + 170], radius=18, fill=(40, 40, 40), outline=INK, width=3)
    for i in range(7):
        d.line([(wx + 4, y - 25 + i * 30), (wx + 56, y - 25 + i * 30)], fill=(90, 90, 90), width=3)
    # axle
    ax = x - 10 if not flip else x + 230
    d.rectangle([ax, y + 55, ax + 20, y + 75], fill=(240, 240, 240), outline=INK, width=2)
    # gearbox
    d.rounded_rectangle([x + 10, y, x + 230, y + 130], radius=10, fill=YELLOW, outline=INK, width=3)
    # metal motor can
    mx = x + 150 if not flip else x + 10
    d.rounded_rectangle([mx, y + 25, mx + 80, y + 105], radius=8, fill=(200, 200, 205), outline=INK, width=3)
    tx = x + 40 if not flip else x + 110
    d.text((tx, y + 10), "TT motor", fill=INK, font=F_B)
    d.text((tx, y + 92), name, fill=INK, font=F_P)
    # terminals on the can end
    ex = mx + 80 if not flip else mx
    t1, t2 = (ex, y + 45), (ex, y + 85)
    pdot(*t1)
    pdot(*t2)
    return t1, t2


# ---------------- Title ----------------
d.text((40, 24), "Yellow TT motors - wiring", fill=INK, font=F_T)
d.text((40, 68), "2x TT motor + L298N motor driver + ESP32 + 2x18650 battery", fill=(80, 80, 80), font=F_N)

# ---------------- ESP32 ----------------
d.rounded_rectangle([60, 200, 320, 700], radius=14, fill=(210, 230, 250), outline=INK, width=3)
d.text((140, 212), "ESP32", fill=INK, font=F_B)
esp = [("GPIO25", 300), ("GPIO26", 350), ("GPIO27", 400), ("GPIO14", 450), ("GPIO13", 500), ("GPIO33", 550), ("GND", 630)]
for n, y in esp:
    pdot(320, y)
    label_right(320, y, n)

# ---------------- L298N ----------------
LX0, LX1 = 600, 880
d.rounded_rectangle([LX0, 200, LX1, 760], radius=14, fill=(255, 215, 215), outline=INK, width=3)
d.text((LX0 + 14, 212), "L298N", fill=INK, font=F_B)
d.text((LX0 + 14, 240), "motor driver", fill=(70, 70, 70), font=F_P)
d.rectangle([LX0 + 150, 215, LX0 + 260, 265], fill=(20, 20, 20))      # heatsink
for i in range(6):
    d.line([(LX0 + 158 + i * 18, 215), (LX0 + 158 + i * 18, 265)], fill=(80, 80, 80), width=3)
lin = ["ENA", "IN1", "IN2", "IN3", "IN4", "ENB"]
for (n, (_, y)), c in zip(zip(lin, esp), SIG):
    pdot(LX0, y)
    label_left(LX0, y, n)
    wire([(320, y), (LX0, y)], c, 5)
d.text((LX0 + 90, 415), "remove the ENA", fill=RED, font=F_P)
d.text((LX0 + 90, 439), "and ENB jumpers", fill=RED, font=F_P)

# outputs
outs = [("OUT1", 300), ("OUT2", 360), ("OUT3", 520), ("OUT4", 580)]
for n, y in outs:
    pdot(LX1, y)
    label_right(LX1, y, n)

# power (bottom)
pw = [("12V", 660), ("GND", 740), ("5V", 820)]
for n, x in pw:
    pdot(x, 760)
    d.text((x - d.textlength(n, font=F_P) / 2, 728), n, fill=INK, font=F_P)
d.text((790, 772), "(not used)", fill=(120, 120, 120), font=F_P)

# ---------------- Motors ----------------
# flip=True: motor can (with its 2 terminals) faces the L298N, wheel on the right
lm = tt_motor(1060, 255, "LEFT wheel", flip=True)
rm = tt_motor(1060, 505, "RIGHT wheel", flip=True)
wire([(LX1, 300), (lm[0][0], 300)], RED, 5)
wire([(LX1, 360), (1000, 360), (1000, lm[1][1]), (lm[1][0], lm[1][1])], BLACK, 5)
wire([(LX1, 520), (1000, 520), (1000, rm[0][1]), (rm[0][0], rm[0][1])], RED, 5)
wire([(LX1, 580), (rm[1][0], 580)], BLACK, 5)
d.text((1060, 690), "Motor spins the wrong way?", fill=INK, font=F_P)
d.text((1060, 714), "Swap its 2 wires (OUT1 <-> OUT2).", fill=INK, font=F_P)

# ---------------- Battery + switch ----------------
BX0, BY0 = 1000, 800
d.rounded_rectangle([BX0, BY0, BX0 + 400, BY0 + 150], radius=14, fill=(60, 60, 66), outline=INK, width=3)
for x in (BX0 + 30, BX0 + 210):
    d.rounded_rectangle([x, BY0 + 25, x + 150, BY0 + 80], radius=24, fill=YELLOW, outline=INK, width=2)
    d.rectangle([x + 142, BY0 + 42, x + 156, BY0 + 63], fill=(200, 200, 200), outline=INK)
    d.text((x + 40, BY0 + 40), "18650", fill=INK, font=F_P)
d.text((BX0 + 80, BY0 + 100), "2x 18650 = 7.4V", fill=(255, 255, 255), font=F_B)
NEG, POS = (BX0, BY0 + 30), (BX0, BY0 + 115)
pdot(*NEG, BLACK)
d.text((BX0 + 8, BY0 - 2), "-", fill=(255, 255, 255), font=F_B)
pdot(*POS, RED)
d.text((BX0 + 8, BY0 + 118), "+", fill=(255, 120, 120), font=F_B)

# battery - -> L298N GND
wire([NEG, (740, NEG[1]), (740, 760)], BLACK)
# battery + -> switch -> L298N 12V
d.rounded_rectangle([840, POS[1] - 30, 940, POS[1] + 30], radius=8, fill=(240, 240, 240), outline=INK, width=3)
d.text((852, POS[1] - 11), "SWITCH", fill=INK, font=F_P)
wire([POS, (940, POS[1])], RED)
wire([(840, POS[1]), (660, POS[1]), (660, 760)], RED)

# ESP32 GND -> joins the GND wire (hops over the red 12V wire)
GY = 800
wire([(320, 630), (450, 630), (450, GY), (645, GY)], BLACK)
d.arc([645, GY - 15, 675, GY + 15], start=180, end=360, fill=BLACK, width=6)
wire([(675, GY), (740, GY)], BLACK)
pdot(740, GY, BLACK)
d.text((470, 808), "GND together!", fill=INK, font=F_P)

# ---------------- Notes ----------------
notes = [
    "1. Never connect a motor directly to the ESP32 - always through the L298N.",
    "2. Remove the ENA and ENB jumpers so the ESP32 can control the speed.",
    "3. ESP32 GND and battery - must both go to the L298N GND.",
    "4. Turn the switch OFF while uploading code.",
]
for k, t in enumerate(notes):
    d.text((40, 975 + k * 26), t, fill=INK, font=F_N)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT)
