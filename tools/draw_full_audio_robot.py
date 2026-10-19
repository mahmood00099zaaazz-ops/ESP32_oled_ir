"""Full wiring for the parrot/AI robot: OLED + IR + INMP441 mic + MAX98357A amp + speaker on the ESP32.

Signal wires are drawn; power pins are shown as coloured tags (3V3 / 5V / GND) to keep it readable.
Kurdish (Badini) labels. Output: images/full_audio_robot_wiring.png
Usage: python3 tools/draw_full_audio_robot.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "full_audio_robot_wiring.png"
W, H = 1080, 2400
BG = (252, 252, 248)
INK = (25, 25, 30)
GREY = (110, 110, 110)
RED = (215, 35, 35)
ORANGE = (240, 130, 20)
BLACK = (15, 15, 15)
PURPLE = (90, 50, 150)
PAD = (225, 190, 80)
C = {"SDA": (40, 110, 220), "SCL": (30, 160, 90), "OUT": (150, 70, 200), "WS": (0, 150, 170),
     "SCK": (110, 160, 30), "SD": (200, 60, 160), "LRC": (0, 150, 170), "BCLK": (110, 160, 30),
     "DIN": (200, 60, 160)}

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def wire(pts, color, w=9):
    d.line(pts, fill=color, width=w, joint="curve")


def dot(x, y, color=PAD, r=10):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=INK, width=2)


def tag(x, y, net):
    """Power tag hanging below a pin: 3V3 / 5V / GND."""
    col = {"3V3": ORANGE, "5V": RED, "GND": BLACK}[net]
    wire([(x, y), (x, y + 34)], col, 6)
    tw = d.textlength(net, font=font(20))
    d.rounded_rectangle([x - tw / 2 - 8, y + 34, x + tw / 2 + 8, y + 64], radius=8, fill=col)
    en(x, y + 37, net, 20, (255, 255, 255))


def bottom_pins(x0, y, names):
    """Pins along the bottom edge of a module, each with a power tag."""
    for i, (name, net) in enumerate(names):
        x = x0 + i * 74
        dot(x, y)
        en(x, y - 34, name, 18, (235, 235, 235))
        tag(x, y, net)


# ---------------- Title ----------------
ku(W / 2, 22, "وایەرێن هەمی ڕۆبۆتی", 60)
en(W / 2, 104, "OLED + IR + INMP441 + MAX98357A", 30, GREY)

# ---------------- ESP32 (centre) ----------------
EX0, EX1, EY0, EY1 = 380, 700, 200, 1260
d.rounded_rectangle([EX0, EY0, EX1, EY1], radius=20, fill=(28, 28, 32), outline=INK, width=5)
en((EX0 + EX1) / 2, EY0 + 26, "ESP32", 42, (220, 220, 225))
left = {300: ("GPIO21", "SDA"), 370: ("GPIO22", "SCL"), 640: ("GPIO34", "OUT"),
        900: ("GPIO33", "WS"), 970: ("GPIO32", "SCK"), 1040: ("GPIO35", "SD")}
right = {360: ("GPIO25", "LRC"), 430: ("GPIO26", "BCLK"), 500: ("GPIO27", "DIN")}
for y, (n, _) in left.items():
    dot(EX0, y)
    en(EX0 + 16, y - 15, n, 26, (240, 240, 240), "la")
for y, (n, _) in right.items():
    dot(EX1, y)
    en(EX1 - 16, y - 15, n, 26, (240, 240, 240), "ra")
# ESP32 power pins along the bottom
bottom_pins(EX0 + 60, EY1 - 40, [("3V3", "3V3"), ("5V", "5V"), ("GND", "GND"), ("GND", "GND")])

# ---------------- OLED (top left) ----------------
OX0, OX1, OY0, OY1 = 30, 300, 220, 500
d.rounded_rectangle([OX0, OY0, OX1, OY1], radius=14, fill=(40, 50, 70), outline=INK, width=4)
en(OX0 + 16, OY0 + 12, "OLED", 26, (255, 255, 255), "la")
d.rectangle([OX0 + 16, OY0 + 150, OX0 + 120, OY0 + 210], fill=(10, 14, 22))
d.rounded_rectangle([OX0 + 28, OY0 + 162, OX0 + 58, OY0 + 198], radius=6, fill=(90, 200, 255))
d.rounded_rectangle([OX0 + 78, OY0 + 162, OX0 + 108, OY0 + 198], radius=6, fill=(90, 200, 255))
for y, n in ((300, "SDA"), (370, "SCL")):
    dot(OX1, y)
    en(OX1 - 16, y - 15, n, 24, (240, 240, 240), "ra")
    wire([(OX1, y), (EX0, y)], C[n])
bottom_pins(OX0 + 150, OY1, [("VCC", "3V3"), ("GND", "GND")])

# ---------------- IR sensor (middle left) ----------------
IX0, IX1, IY0, IY1 = 30, 300, 580, 760
d.rounded_rectangle([IX0, IY0, IX1, IY1], radius=14, fill=(30, 80, 160), outline=INK, width=4)
en(IX0 + 16, IY0 + 12, "IR", 26, (255, 255, 255), "la")
d.ellipse([IX0 + 20, IY0 + 60, IX0 + 56, IY0 + 96], fill=(240, 240, 240), outline=INK, width=2)
d.ellipse([IX0 + 66, IY0 + 60, IX0 + 102, IY0 + 96], fill=(40, 40, 40), outline=INK, width=2)
dot(IX1, 640)
en(IX1 - 16, 625, "OUT", 24, (240, 240, 240), "ra")
wire([(IX1, 640), (EX0, 640)], C["OUT"])
bottom_pins(IX0 + 150, IY1, [("VCC", "3V3"), ("GND", "GND")])

# ---------------- INMP441 mic (bottom left) ----------------
MX0, MX1, MY0, MY1 = 30, 300, 840, 1180
d.rounded_rectangle([MX0, MY0, MX1, MY1], radius=60, fill=(20, 20, 24), outline=(200, 160, 60), width=5)
en(MX0 + 30, MY0 + 14, "INMP441", 24, (255, 255, 255), "la")
d.ellipse([MX0 + 34, MY0 + 60, MX0 + 70, MY0 + 96], fill=(70, 70, 75), outline=(200, 160, 60), width=3)
for y, n in ((900, "WS"), (970, "SCK"), (1040, "SD")):
    dot(MX1, y)
    en(MX1 - 16, y - 15, n, 24, (240, 240, 240), "ra")
    wire([(MX1, y), (EX0, y)], C[n])
bottom_pins(MX0 + 66, MY1, [("VDD", "3V3"), ("GND", "GND"), ("L/R", "GND")])

# ---------------- MAX98357A (right) ----------------
AX0, AX1, AY0, AY1 = 780, 1050, 220, 640
d.rounded_rectangle([AX0, AY0, AX1, AY1], radius=14, fill=PURPLE, outline=INK, width=4)
en((AX0 + AX1) / 2, AY0 + 14, "MAX98357A", 22, (235, 225, 255))
for y, n in ((360, "LRC"), (430, "BCLK"), (500, "DIN")):
    dot(AX0, y)
    en(AX0 + 16, y - 15, n, 24, (240, 240, 240), "la")
    wire([(EX1, y), (AX0, y)], C[n])
en(AX1 - 14, 556, "GAIN, SD", 20, (220, 210, 240), "ra")
ku(AX1 - 14, 584, "بەتال بهێلە", 20, (220, 210, 240), anchor="ra")
bottom_pins(AX0 + 40, AY1, [("Vin", "5V"), ("GND", "GND")])
# speaker terminal on the right edge -> speaker
d.rectangle([AX1 - 70, AY0 + 70, AX1 - 10, AY0 + 170], fill=(40, 170, 110), outline=INK, width=3)
en(AX1 - 40, AY0 + 76, "+", 28, (255, 255, 255))
en(AX1 - 40, AY0 + 124, "-", 32, (255, 255, 255))
SCX, SCY, SR = 940, 880, 95
wire([(AX1 - 10, AY0 + 95), (1065, AY0 + 95), (1065, SCY - 30), (SCX + SR - 6, SCY - 30)], RED, 7)
wire([(AX1 - 10, AY0 + 145), (1052, AY0 + 145), (1052, SCY + 30), (SCX + SR - 6, SCY + 30)], BLACK, 7)
d.ellipse([SCX - SR, SCY - SR, SCX + SR, SCY + SR], fill=(200, 200, 205), outline=INK, width=5)
d.ellipse([SCX - 50, SCY - 50, SCX + 50, SCY + 50], fill=(160, 160, 165), outline=INK, width=3)
en(SCX, SCY - 18, "8Ω", 30, INK)
ku(SCX, SCY + SR + 10, "بلندگۆ", 30, INK)

# ---------------- Rule for the tags ----------------
RY = 1400
d.rounded_rectangle([40, RY, W - 40, RY + 200], radius=18, fill=(255, 255, 255), outline=INK, width=3)
ku(W - 70, RY + 16, "نیشانێن ڕەنگی ب ئێکڤە گرێ بدە:", 30, INK, anchor="ra")
for k, (net, col, txt) in enumerate((("3V3", ORANGE, "هەمی پێکڤە ← 3V3 یا ESP32"),
                                     ("5V", RED, "← 5V یا ESP32"),
                                     ("GND", BLACK, "هەمی پێکڤە ← GND"))):
    y = RY + 70 + k * 42
    tw = d.textlength(net, font=font(22))
    d.rounded_rectangle([W - 90 - tw - 16, y, W - 90, y + 32], radius=8, fill=col)
    en(W - 98, y + 4, net, 22, (255, 255, 255), "ra")
    ku(W - 120 - tw, y + 4, txt, 24, INK, anchor="ra")

# ---------------- Full table ----------------
TY = 1640
rows = [
    ("OLED", "SDA ← GPIO21", "SCL ← GPIO22", "VCC ← 3V3"),
    ("IR", "OUT ← GPIO34", "VCC ← 3V3", ""),
    ("INMP441", "WS ← GPIO33", "SCK ← GPIO32", "SD ← GPIO35"),
    ("", "VDD ← 3V3 ⚠", "L/R ← GND", ""),
    ("MAX98357A", "LRC ← GPIO25", "BCLK ← GPIO26", "DIN ← GPIO27"),
    ("", "Vin ← 5V", "+ / - ← 8Ω speaker", ""),
]
d.rounded_rectangle([40, TY, W - 40, TY + 40 + len(rows) * 100], radius=18, fill=(255, 255, 255), outline=INK, width=3)
for k, (part, a, b, c) in enumerate(rows):
    y = TY + 26 + k * 100
    if part:
        en(W - 70, y + 4, part, 26, PURPLE if "MAX" in part else INK, "ra")
        if k:
            d.line([(60, y - 14), (W - 60, y - 14)], fill=(225, 225, 225), width=2)
    for j, t in enumerate((a, b, c)):
        if not t:
            continue
        x = 790 - j * 290
        if t[0].isascii():
            en(x, y + 46, t.replace("←", "→"), 22, INK, "ma")
        else:
            ku(x, y + 46, t, 22, INK)
ku(W / 2, TY + 40 + len(rows) * 100 + 20, "⚠ مایک INMP441 ب 5V ڤە نە!", 28, RED)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
