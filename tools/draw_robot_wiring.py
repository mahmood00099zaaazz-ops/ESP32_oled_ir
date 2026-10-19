"""Draw the wiring diagram for the ESP32 robot car (eyes + servo head + 2 DC motors).

Output: images/robot_wiring.png   Usage: python3 tools/draw_robot_wiring.py (needs Pillow)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "robot_wiring.png"
W, H = 1700, 1180
BG = (250, 250, 247)
INK = (30, 30, 34)
RED = (215, 40, 40)
BLACK = (20, 20, 20)
ORANGE = (240, 140, 20)
BLUE = (40, 110, 220)
GREEN = (30, 150, 70)
PURPLE = (140, 70, 190)
TEAL = (20, 150, 160)
BROWN = (130, 80, 40)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


F_TITLE, F_BOX, F_PIN, F_NOTE = font(34, True), font(22, True), font(17), font(18)


def box(x0, y0, x1, y1, title, fill, sub=None, left=False, color=INK):
    d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=fill, outline=INK, width=3)
    tw = d.textlength(title, font=F_BOX)
    tx = x0 + 14 if left else (x0 + x1 - tw) / 2
    d.text((tx, y0 + 10), title, fill=color, font=F_BOX)
    if sub:
        sw = d.textlength(sub, font=F_PIN)
        sx = x0 + 14 if left else (x0 + x1 - sw) / 2
        d.text((sx, y0 + 38), sub, fill=(70, 70, 70) if color == INK else (200, 220, 255), font=F_PIN)


def pin(x, y, label, side):
    """Pin dot on a box edge; label drawn inside the box."""
    d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=INK)
    if side == "right":
        tw = d.textlength(label, font=F_PIN)
        d.text((x - 14 - tw, y - 11), label, fill=INK, font=F_PIN)
    elif side == "left":
        d.text((x + 14, y - 11), label, fill=INK, font=F_PIN)
    elif side == "top":
        tw = d.textlength(label, font=F_PIN)
        d.text((x - tw / 2, y + 12), label, fill=INK, font=F_PIN)
    elif side == "bottom":
        tw = d.textlength(label, font=F_PIN)
        d.text((x - tw / 2, y - 32), label, fill=INK, font=F_PIN)


def wire(points, color, width=5):
    d.line(points, fill=color, width=width, joint="curve")


def dot(x, y, color):
    d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=color)


def gnd(x, y, direction):
    """Ground symbol attached to (x, y). direction: 'left', 'right' or 'down'."""
    if direction == "down":
        wire([(x, y), (x, y + 26)], BLACK, 4)
        bx, by = x, y + 26
    else:
        dx = -40 if direction == "left" else 40
        wire([(x, y), (x + dx, y), (x + dx, y + 18)], BLACK, 4)
        bx, by = x + dx, y + 18
    for i, half in enumerate((16, 10, 4)):
        d.line([(bx - half, by + i * 6), (bx + half, by + i * 6)], fill=BLACK, width=3)


# ---------------- Title ----------------
d.text((40, 24), "ESP32 Robot - Wiring Diagram", fill=INK, font=F_TITLE)
d.text((40, 70), "OLED eyes + IR sensor + SG90 servo head + 2 DC motors (L298N) + 2x18650 battery",
       fill=(80, 80, 80), font=F_NOTE)

# ---------------- ESP32 ----------------
EX0, EX1 = 640, 880
box(EX0, 230, EX1, 860, "ESP32", (210, 230, 250), "DevKit")
left_pins = {"3V3": 300, "GND": 345, "GPIO21": 400, "GPIO22": 440, "GPIO34": 520, "GPIO18": 650, "VIN (5V)": 760}
right_pins = {"GPIO25": 400, "GPIO26": 440, "GPIO27": 480, "GPIO14": 520, "GPIO13": 560, "GPIO33": 600, "GND": 760}
for n, y in left_pins.items():
    pin(EX0, y, n, "left")
for n, y in right_pins.items():
    pin(EX1, y, n, "right")
# USB port
d.rounded_rectangle([730, 840, 790, 880], radius=6, fill=(180, 180, 185), outline=INK, width=2)
d.text((735, 885), "USB", fill=INK, font=F_PIN)

# ---------------- OLED ----------------
box(60, 230, 340, 470, "OLED 128x64", (40, 50, 70), "SSD1306 I2C", left=True, color=(255, 255, 255))
d.rounded_rectangle([80, 330, 230, 400], radius=4, fill=(10, 15, 25))
d.rounded_rectangle([100, 345, 140, 385], radius=7, fill=(90, 200, 255))
d.rounded_rectangle([170, 345, 210, 385], radius=7, fill=(90, 200, 255))
oled = {"VCC": 300, "GND": 345, "SDA": 400, "SCL": 440}
for n, y in oled.items():
    d.ellipse([340 - 6, y - 6, 340 + 6, y + 6], fill=(230, 230, 230))
    tw = d.textlength(n, font=F_PIN)
    d.text((340 - 14 - tw, y - 11), n, fill=(230, 230, 230), font=F_PIN)
wire([(340, 300), (640, 300)], ORANGE)          # VCC -> 3V3
wire([(340, 345), (640, 345)], BLACK)           # GND -> GND
wire([(340, 400), (640, 400)], BLUE)            # SDA -> 21
wire([(340, 440), (640, 440)], GREEN)           # SCL -> 22

# ---------------- IR sensor ----------------
box(60, 490, 340, 610, "IR sensor", (225, 245, 225), left=True)
pin(340, 520, "OUT", "right")
pin(340, 555, "VCC", "right")
pin(340, 585, "GND", "right")
wire([(340, 520), (640, 520)], PURPLE)          # OUT -> 34
wire([(340, 555), (560, 555), (560, 300)], ORANGE)  # VCC -> 3V3 line
dot(560, 300, ORANGE)
gnd(340, 585, "right")

# ---------------- SG90 servo ----------------
box(60, 630, 340, 790, "SG90 servo", (215, 225, 255), "head", left=True)
pin(340, 650, "SIG (orange)", "right")
pin(340, 700, "5V (red)", "right")
pin(340, 750, "GND (brown)", "right")
wire([(340, 650), (640, 650)], ORANGE, 5)       # signal -> 18
gnd(340, 750, "right")

# ---------------- Buck converter ----------------
box(40, 880, 360, 1050, "Buck converter", (255, 240, 210), "LM2596 / Mini-360 -> 5.0V", left=True)
pin(360, 950, "OUT+ 5V", "right")
pin(360, 990, "IN+", "right")
pin(360, 1025, "GND", "right")
# 5V rail: buck OUT+ -> lane x=520 -> SG90 red and ESP32 VIN
wire([(360, 950), (520, 950), (520, 700)], RED)
wire([(340, 700), (520, 700)], RED)
dot(520, 760, RED)
wire([(520, 760), (640, 760)], RED)
gnd(360, 1025, "right")

# ---------------- L298N ----------------
LX0, LX1 = 1060, 1300
box(LX0, 330, LX1, 740, "L298N", (255, 215, 215), "motor driver", left=True)
l_in = {"ENA": 400, "IN1": 440, "IN2": 480, "IN3": 520, "IN4": 560, "ENB": 600}
for n, y in l_in.items():
    pin(LX0, y, n, "left")
colors = [TEAL, BLUE, GREEN, PURPLE, BROWN, TEAL]
for (n, y), c in zip(l_in.items(), colors):
    wire([(EX1, y), (LX0, y)], c, 4)
d.text((LX0 + 80, 625), "remove ENA/ENB", fill=RED, font=F_PIN)
d.text((LX0 + 80, 645), "jumpers", fill=RED, font=F_PIN)
# power pins at bottom
pin(1110, 740, "12V", "bottom")
pin(1180, 740, "GND", "bottom")
pin(1250, 740, "5V", "bottom")
d.text((1215, 752), "(not used)", fill=(120, 120, 120), font=F_PIN)
gnd(1180, 740, "down")
# ESP32 right GND
gnd(EX1, 760, "right")
# motor outputs
pin(LX1, 420, "OUT1", "right")
pin(LX1, 470, "OUT2", "right")
pin(LX1, 570, "OUT3", "right")
pin(LX1, 620, "OUT4", "right")


def motor(y0, label):
    d.rounded_rectangle([1440, y0, 1580, y0 + 90], radius=10, fill=(255, 220, 60), outline=INK, width=3)
    d.rounded_rectangle([1580, y0 + 30, 1610, y0 + 60], radius=4, fill=(240, 240, 240), outline=INK, width=2)
    d.text((1452, y0 + 10), "TT motor", fill=INK, font=F_BOX)
    d.text((1452, y0 + 50), label, fill=INK, font=F_PIN)
    d.ellipse([1434, y0 + 19, 1446, y0 + 31], fill=INK)
    d.ellipse([1434, y0 + 59, 1446, y0 + 71], fill=INK)


motor(400, "LEFT wheel")
motor(550, "RIGHT wheel")
wire([(LX1, 420), (1370, 420), (1370, 425), (1440, 425)], RED, 4)
wire([(LX1, 470), (1390, 470), (1390, 465), (1440, 465)], BLACK, 4)
wire([(LX1, 570), (1370, 570), (1370, 575), (1440, 575)], RED, 4)
wire([(LX1, 620), (1390, 620), (1390, 615), (1440, 615)], BLACK, 4)

# ---------------- Battery + switch ----------------
d.rounded_rectangle([1300, 920, 1600, 1060], radius=14, fill=(60, 60, 66), outline=INK, width=3)
for i, x in enumerate((1320, 1460)):
    d.rounded_rectangle([x, 950, x + 120, 1000], radius=20, fill=(60, 140, 220), outline=INK, width=2)
    d.text((x + 22, 963), "18650", fill=(255, 255, 255), font=F_PIN)
d.text((1330, 1010), "2x 18650 = 7.4V", fill=(255, 255, 255), font=F_BOX)
d.ellipse([1300 - 6, 935 - 6, 1300 + 6, 935 + 6], fill=RED)
d.text((1270, 905), "+", fill=RED, font=F_BOX)
d.ellipse([1300 - 6, 1045 - 6, 1300 + 6, 1045 + 6], fill=BLACK)
d.text((1272, 1050), "-", fill=BLACK, font=F_BOX)

# switch
d.rounded_rectangle([1000, 905, 1100, 965], radius=8, fill=(240, 240, 240), outline=INK, width=3)
d.text((1012, 920), "SWITCH", fill=INK, font=F_PIN)
wire([(1300, 935), (1100, 935)], RED)
# from switch to L298N 12V and buck IN+
wire([(1000, 935), (960, 935)], RED)
dot(960, 935, RED)
wire([(960, 935), (960, 820), (1110, 820), (1110, 740)], RED)
wire([(960, 935), (960, 1070), (440, 1070), (440, 990), (360, 990)], RED)
gnd(1300, 1045, "left")

# ---------------- Legend / notes ----------------
notes = [
    "All GND symbols must be connected together (battery -, L298N, buck, ESP32, IR, OLED, servo).",
    "Set the buck converter output to 5.0V with a multimeter BEFORE connecting the ESP32.",
    "Turn the battery switch OFF while uploading code over USB.",
]
for i, t in enumerate(notes):
    d.text((40, 1095 + i * 26), "- " + t, fill=INK, font=F_NOTE)

# ground symbol legend
d.text((1300, 112), "= GND (common)", fill=INK, font=F_NOTE)
for i, half in enumerate((16, 10, 4)):
    d.line([(1275 - half, 120 + i * 6), (1275 + half, 120 + i * 6)], fill=BLACK, width=3)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT)
