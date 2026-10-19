"""Draw the battery pack (2x18650 + holder + switch) and where its wires go.

Output: images/battery_wiring.png   Usage: python3 tools/draw_battery_wiring.py (needs Pillow)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "battery_wiring.png"
W, H = 1500, 1060
BG = (250, 250, 247)
INK = (30, 30, 34)
RED = (215, 40, 40)
BLACK = (20, 20, 20)
YELLOW = (255, 210, 40)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=False):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


F_T, F_B, F_P, F_BIG = font(32, True), font(22, True), font(18), font(30, True)


def wire(pts, color, w=7):
    d.line(pts, fill=color, width=w, joint="curve")


def pdot(x, y, color=INK):
    d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=color)


def cell(x, y, flip):
    """One 18650 cell, 260x80. flip=False: + on the right."""
    d.rounded_rectangle([x, y, x + 260, y + 80], radius=30, fill=YELLOW, outline=INK, width=3)
    d.rectangle([x + 60, y + 3, x + 200, y + 77], fill=(255, 225, 90))
    d.text((x + 95, y + 14), "18650", fill=INK, font=F_B)
    d.text((x + 100, y + 44), "3.7V", fill=INK, font=F_P)
    # positive nub
    nx = x + 258 if not flip else x - 14
    d.rectangle([nx, y + 28, nx + 16, y + 52], fill=(200, 200, 200), outline=INK, width=2)
    px = x + 232 if not flip else x + 14
    mx = x + 14 if not flip else x + 232
    d.text((px, y + 22), "+", fill=RED, font=F_BIG)
    d.text((mx + 3, y + 20), "-", fill=INK, font=F_BIG)


# ---------------- Title ----------------
d.text((40, 24), "Battery pack - 2x 18650 (7.4V)", fill=INK, font=F_T)
d.text((40, 68), "How to put the batteries in, and where the red and black wires go", fill=(80, 80, 80), font=F_P)

# ---------------- Holder with 2 cells ----------------
HX0, HY0, HX1, HY1 = 80, 150, 520, 450
d.rounded_rectangle([HX0, HY0, HX1, HY1], radius=16, fill=(55, 55, 60), outline=INK, width=4)
d.text((HX0 + 20, HY0 + 12), "2x 18650 battery holder", fill=(255, 255, 255), font=F_P)
# springs (-) and plates (+)
cell(140, 200, flip=False)      # top cell: + on the right
cell(140, 330, flip=True)       # bottom cell: + on the left (holder connects them in series)
for (sx, sy) in ((HX0 + 18, 215), (HX1 - 28, 345)):
    for k in range(5):
        d.line([(sx, sy + k * 10), (sx + 12, sy + 5 + k * 10)], fill=(200, 200, 200), width=3)
d.text((HX0 + 20, HY1 - 32), "Follow the + / - marks inside the holder!", fill=(255, 220, 120), font=F_P)

# holder wires: red (+) and black (-)
RP = (HX1, 240)
BP = (HX1, 410)
pdot(*RP, RED)
pdot(*BP, BLACK)

# ---------------- Switch ----------------
SX0, SY0 = 660, 200
d.rounded_rectangle([SX0, SY0, SX0 + 140, SY0 + 80], radius=10, fill=(240, 240, 240), outline=INK, width=3)
d.rounded_rectangle([SX0 + 45, SY0 + 20, SX0 + 95, SY0 + 60], radius=6, fill=(60, 60, 60))
d.text((SX0 + 30, SY0 + 88), "ON / OFF", fill=INK, font=F_P)
d.text((SX0 + 22, SY0 + 112), "switch", fill=INK, font=F_P)
wire([RP, (SX0, RP[1])], RED)

# junctions after the switch
J = (900, 240)
wire([(SX0 + 140, RP[1]), J], RED)
pdot(*J, RED)

# ---------------- Destinations ----------------
# L298N
LX0, LY0 = 1080, 150
d.rounded_rectangle([LX0, LY0, LX0 + 340, LY0 + 230], radius=14, fill=(255, 215, 215), outline=INK, width=3)
d.text((LX0 + 16, LY0 + 12), "L298N", fill=INK, font=F_B)
d.text((LX0 + 16, LY0 + 42), "(motors)", fill=(70, 70, 70), font=F_P)
d.text((LX0 + 16, LY0 + 80), "12V", fill=INK, font=F_P)
d.text((LX0 + 16, LY0 + 160), "GND", fill=INK, font=F_P)
pdot(LX0, LY0 + 90)
pdot(LX0, LY0 + 170)
wire([J, (LX0, J[1])], RED)   # -> L298N 12V

# Buck converter
BX0, BY0 = 1080, 560
d.rounded_rectangle([BX0, BY0, BX0 + 340, BY0 + 230], radius=14, fill=(255, 240, 210), outline=INK, width=3)
d.text((BX0 + 16, BY0 + 12), "Buck converter", fill=INK, font=F_B)
d.text((BX0 + 16, BY0 + 42), "(5V for ESP32 + servo)", fill=(70, 70, 70), font=F_P)
d.text((BX0 + 16, BY0 + 80), "IN+", fill=INK, font=F_P)
d.text((BX0 + 16, BY0 + 160), "IN- / GND", fill=INK, font=F_P)
pdot(BX0, BY0 + 90)
pdot(BX0, BY0 + 170)

# red: switch -> buck IN+
wire([J, (900, BY0 + 90), (BX0, BY0 + 90)], RED)

# black: holder (-) -> L298N GND and buck GND (hops over the red wire)
K = (980, BP[1])
wire([BP, (885, BP[1])], BLACK)
d.arc([885, BP[1] - 15, 915, BP[1] + 15], start=180, end=360, fill=BLACK, width=7)
wire([(915, BP[1]), K], BLACK)
pdot(*K, BLACK)
wire([K, (980, LY0 + 170), (LX0, LY0 + 170)], BLACK)
wire([K, (980, BY0 + 170), (BX0, BY0 + 170)], BLACK)
d.text((560, 420), "black = -  (GND)", fill=INK, font=F_B)
d.text((560, 160), "red = +", fill=RED, font=F_B)
d.text((1060, 805), "then: buck OUT+ 5V -> ESP32 VIN + servo red", fill=INK, font=F_P)

# ---------------- Notes ----------------
notes = [
    ("1. Buy 2 real 18650 cells (Samsung / LG / Sony) - 3.7V each, together 7.4V.", INK),
    ("2. Put them in the holder following the + and - marks. Wrong way = nothing works.", INK),
    ("3. Red wire = +  ->  switch  ->  L298N 12V and buck converter IN+.", RED),
    ("4. Black wire = -  ->  L298N GND and buck converter GND.", INK),
    ("5. NEVER touch red and black together (short circuit = heat / fire).", RED),
    ("6. Charge only with an 18650 charger, never with a phone charger.", INK),
]
for k, (t, c) in enumerate(notes):
    d.text((40, 860 + k * 30), t, fill=c, font=F_P)

# full-charge / low voltage hint
d.rounded_rectangle([80, 520, 520, 790], radius=14, fill=(255, 255, 255), outline=INK, width=2)
d.text((100, 535), "Voltage (multimeter):", fill=INK, font=F_B)
for k, (v, t, c) in enumerate([("8.4V", "full", (30, 150, 70)), ("7.4V", "normal", INK),
                               ("6.4V", "low - charge now!", RED)]):
    d.text((110, 585 + k * 60), v, fill=c, font=F_BIG)
    d.text((220, 593 + k * 60), t, fill=c, font=F_P)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT)
