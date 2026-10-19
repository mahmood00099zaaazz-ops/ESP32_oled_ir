"""Wiring for the INMP441 I2S microphone + MAX98357A I2S amplifier + speaker on the ESP32.

Microphone on the left, amplifier on the right, ESP32 in the middle; pins chosen so they don't
clash with the OLED (21/22) and IR sensor (34). Kurdish (Badini) labels.
Output: images/mic_speaker_wiring.png
Usage: python3 tools/draw_mic_speaker.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "mic_speaker_wiring.png"
W, H = 1080, 2200
BG = (252, 252, 248)
INK = (25, 25, 30)
GREY = (110, 110, 110)
RED = (215, 35, 35)
ORANGE = (240, 130, 20)
BLACK = (15, 15, 15)
PURPLE = (90, 50, 150)
PAD = (225, 190, 80)
SIG = {"WS": (30, 140, 200), "SCK": (40, 160, 90), "SD": (200, 60, 160),
       "LRC": (30, 140, 200), "BCLK": (40, 160, 90), "DIN": (200, 60, 160)}

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=34, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def wire(pts, color, w=10):
    d.line(pts, fill=color, width=w, joint="curve")


def dot(x, y, color=PAD, r=11):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=INK, width=2)


# ---------------- Title ----------------
ku(W / 2, 22, "مایک و بلندگۆ", 62)
en(W / 2, 108, "INMP441  +  MAX98357A", 32, GREY)

ROWS = [400, 480, 560, 640, 720, 800, 880]       # shared row heights

# ---------------- ESP32 (middle) ----------------
EX0, EX1, EY0, EY1 = 345, 735, 250, 960
d.rounded_rectangle([EX0, EY0, EX1, EY1], radius=18, fill=(28, 28, 32), outline=INK, width=5)
en((EX0 + EX1) / 2, EY0 + 30, "ESP32", 40, (220, 220, 225))
esp_left = {400: ("3V3", ORANGE), 480: ("GND", BLACK), 640: ("GPIO33", SIG["WS"]),
            720: ("GPIO32", SIG["SCK"]), 800: ("GPIO35", SIG["SD"])}
esp_right = {400: ("5V", RED), 480: ("GND", BLACK), 560: ("GPIO25", SIG["LRC"]),
             640: ("GPIO26", SIG["BCLK"]), 720: ("GPIO27", SIG["DIN"])}
for y, (n, c) in esp_left.items():
    dot(EX0, y)
    en(EX0 + 18, y - 15, n, 26, (240, 240, 240), "la")
for y, (n, c) in esp_right.items():
    dot(EX1, y)
    en(EX1 - 18, y - 15, n, 26, (240, 240, 240), "ra")

# ---------------- INMP441 microphone (left) ----------------
MX0, MX1 = 40, 270
d.rounded_rectangle([MX0, 330, MX1, 860], radius=110, fill=(20, 20, 24), outline=(200, 160, 60), width=6)
d.ellipse([(MX0 + MX1) / 2 - 22, 360, (MX0 + MX1) / 2 + 22, 404], fill=(70, 70, 75), outline=(200, 160, 60), width=3)
en((MX0 + MX1) / 2, 870, "INMP441", 28, INK)
ku((MX0 + MX1) / 2, 910, "مایک (گوهـ)", 28, GREY)
mic = [(400, "VDD", ORANGE), (480, "GND", BLACK), (560, "L/R", BLACK),
       (640, "WS", SIG["WS"]), (720, "SCK", SIG["SCK"]), (800, "SD", SIG["SD"])]
for y, n, c in mic:
    dot(MX1, y)
    en(MX1 - 18, y - 15, n, 26, (240, 240, 240), "ra")
for y, n, c in mic:
    if n == "L/R":
        wire([(MX1, y), (305, y), (305, 480)], BLACK)
        dot(305, 480, BLACK, 9)
    else:
        wire([(MX1, y), (EX0, y)], c)

# ---------------- MAX98357A amplifier (right) ----------------
AX0, AX1 = 810, 1040
d.rounded_rectangle([AX0, 330, AX1, 960], radius=14, fill=PURPLE, outline=INK, width=5)
en((AX0 + AX1) / 2 + 20, 344, "MAX98357", 24, (235, 225, 255))
amp = [(400, "Vin", RED), (480, "GND", BLACK), (560, "LRC", SIG["LRC"]), (640, "BCLK", SIG["BCLK"]),
       (720, "DIN", SIG["DIN"]), (800, "GAIN", GREY), (880, "SD", GREY)]
for y, n, c in amp:
    dot(AX0, y)
    en(AX0 + 18, y - 15, n, 26, (240, 240, 240), "la")
    if n in ("GAIN", "SD"):
        # leave unconnected
        d.line([(AX0 - 50, y - 14), (AX0 - 22, y + 14)], fill=GREY, width=5)
        d.line([(AX0 - 50, y + 14), (AX0 - 22, y - 14)], fill=GREY, width=5)
    else:
        wire([(EX1, y), (AX0, y)], c)
ku(AX0 - 8, 900, "بەتال", 24, GREY, anchor="ra")
# green speaker terminal at the bottom of the amp
d.rectangle([AX0 + 60, 930, AX1 - 60, 1010], fill=(40, 170, 110), outline=INK, width=4)
en(AX0 + 95, 950, "+", 34, (255, 255, 255))
en(AX1 - 95, 950, "-", 40, (255, 255, 255))
SP_P, SP_M = (AX0 + 95, 1010), (AX1 - 95, 1010)

# ---------------- Speaker ----------------
SCX, SCY, SR = 880, 1180, 110
wire([SP_P, (SP_P[0], 1060), (SCX - 50, 1060), (SCX - 50, SCY - SR + 30)], RED, 8)
wire([SP_M, (SP_M[0], 1060), (SCX + 50, 1060), (SCX + 50, SCY - SR + 30)], BLACK, 8)
d.ellipse([SCX - SR, SCY - SR, SCX + SR, SCY + SR], fill=(200, 200, 205), outline=INK, width=5)
d.ellipse([SCX - 60, SCY - 60, SCX + 60, SCY + 60], fill=(160, 160, 165), outline=INK, width=3)
en(SCX, SCY - 20, "8Ω", 34, INK)
ku(SCX - SR - 20, SCY - 20, "بلندگۆ", 34, INK, anchor="ra")

# ---------------- Tables ----------------
def table(y0, title, title_color, rows):
    d.rounded_rectangle([40, y0, W - 40, y0 + 70 + len(rows) * 58], radius=18, fill=(255, 255, 255),
                        outline=INK, width=3)
    ku(W - 70, y0 + 16, title, 32, title_color, anchor="ra")
    for k, (a, b, note, c) in enumerate(rows):
        y = y0 + 70 + k * 58
        d.line([(60, y), (W - 60, y)], fill=(225, 225, 225), width=2)
        en(W - 70, y + 12, a, 28, c, "ra")
        en(640, y + 10, "←", 30, c, "ma")
        en(580, y + 12, b, 28, INK, "ra")
        if note:
            ku(250, y + 14, note, 22, RED if "!" in note else GREY, anchor="ma")


table(1330, "مایک INMP441", INK, [
    ("VDD", "3V3", "نە پێنج ڤۆڵت!", ORANGE),
    ("GND", "GND", "", BLACK),
    ("L/R", "GND", "", BLACK),
    ("WS", "GPIO33", "", SIG["WS"]),
    ("SCK", "GPIO32", "", SIG["SCK"]),
    ("SD", "GPIO35", "دەنگ ژ ڤێرێ", SIG["SD"]),
])
table(1760, "ئامپلیفایەر MAX98357A", PURPLE, [
    ("Vin", "5V", "", RED),
    ("GND", "GND", "", BLACK),
    ("LRC", "GPIO25", "", SIG["LRC"]),
    ("BCLK", "GPIO26", "", SIG["BCLK"]),
    ("DIN", "GPIO27", "", SIG["DIN"]),
    ("GAIN, SD", "—", "بەتال بهێلە", GREY),
])

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT, img.size)
