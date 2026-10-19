"""Simple, phone-friendly battery wiring picture with Kurdish (Badini) labels.

Output: images/battery_simple.png   Usage: python3 tools/draw_battery_simple.py
(needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "battery_simple.png"
W, H = 1080, 1760
BG = (252, 252, 248)
INK = (25, 25, 30)
RED = (220, 35, 35)
BLACK = (15, 15, 15)
YELLOW = (255, 208, 30)
GREEN = (25, 145, 65)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=40, color=INK, anchor="ma"):
    """Kurdish (right-to-left) text."""
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=40, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor)


def wire(pts, color, w=16):
    d.line(pts, fill=color, width=w, joint="curve")


def dot(x, y, color, r=16):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color)


# ---------------- Title ----------------
ku(W / 2, 30, "باتریا ڕۆبۆتی", 64)
en(W / 2, 112, "2 x 18650 = 7.4V", 46, (90, 90, 90))

# ---------------- Battery holder ----------------
HX0, HY0, HX1, HY1 = 170, 200, 910, 600
d.rounded_rectangle([HX0, HY0, HX1, HY1], radius=26, fill=(50, 50, 56), outline=INK, width=6)


def cell(y, plus_right):
    x0, x1 = 240, 840
    d.rounded_rectangle([x0, y, x1, y + 140], radius=60, fill=YELLOW, outline=INK, width=5)
    nub = x1 - 4 if plus_right else x0 - 26
    d.rectangle([nub, y + 45, nub + 30, y + 95], fill=(205, 205, 205), outline=INK, width=3)
    en((x0 + x1) / 2, y + 30, "18650", 52)
    en((x0 + x1) / 2, y + 90, "3.7V", 34, (90, 70, 0))
    px, mx = (x1 - 70, x0 + 70) if plus_right else (x0 + 70, x1 - 70)
    en(px, y + 28, "+", 84, RED)
    en(mx, y + 22, "-", 92, INK)


cell(240, plus_right=True)
cell(420, plus_right=False)

# ---------------- Wires from the holder ----------------
RX, BX = 1000, 80                       # red trunk on the right, black trunk on the left
dot(HX1, 310, RED)
dot(HX0, 490, BLACK)
wire([(HX1, 310), (RX, 310), (RX, 1360)], RED)
wire([(HX0, 490), (BX, 490), (BX, 1360)], BLACK)
ku(RX - 20, 640, "سۆر = +", 46, RED, anchor="ra")
ku(BX + 120, 640, "ڕەش = -", 46, BLACK, anchor="la")

# ---------------- Switch on the red wire ----------------
SY0, SY1 = 720, 860
d.rounded_rectangle([RX - 90, SY0, RX + 60, SY1], radius=16, fill=(240, 240, 240), outline=INK, width=6)
d.rounded_rectangle([RX - 50, SY0 + 35, RX + 20, SY1 - 35], radius=10, fill=(60, 60, 60))
ku(RX - 110, SY0 + 30, "سویچ", 48, INK, anchor="ra")
en(RX - 110, SY0 + 90, "ON / OFF", 34, (90, 90, 90), anchor="ra")


# ---------------- Destination boxes ----------------
def dest(y0, title, sub, left_pin, right_pin, fill):
    x0, x1 = 230, 850
    d.rounded_rectangle([x0, y0, x1, y0 + 200], radius=22, fill=fill, outline=INK, width=6)
    en((x0 + x1) / 2, y0 + 24, title, 52)
    ku((x0 + x1) / 2, y0 + 100, sub, 36, (70, 70, 70))
    py = y0 + 160
    en(x0 + 24, py - 20, left_pin, 34, INK, anchor="la")
    en(x1 - 24, py - 20, right_pin, 34, RED, anchor="ra")
    dot(x0, py, BLACK)
    dot(x1, py, RED)
    wire([(BX, py), (x0, py)], BLACK)
    wire([(x1, py), (RX, py)], RED)
    dot(BX, py, BLACK, 20)
    dot(RX, py, RED, 20)


dest(940, "L298N", "بۆ مۆتۆرێن زەر", "GND", "12V", (255, 215, 215))
dest(1200, "Buck converter", "5V بۆ ESP32 و SG90", "GND", "IN+", (255, 240, 205))

# ---------------- Bottom: voltage + safety ----------------
d.rounded_rectangle([40, 1440, W - 40, 1730], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, 1462, "ڤۆڵتێ باتریێ:", 42, INK, anchor="ra")
rows = [("8.4V", "تژیە", GREEN), ("7.4V", "باشە", INK), ("6.4V", "شارژ بکە!", RED)]
for k, (v, t, c) in enumerate(rows):
    x = W - 120 - k * 320
    en(x, 1530, v, 52, c, anchor="ra")
    ku(x, 1600, t, 38, c, anchor="ra")
ku(W / 2, 1668, "⚠ سۆر و ڕەش هەرگیز ب ئێکڤە نەدە!", 40, RED)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT)
