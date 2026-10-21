"""Everything in one picture: the all-in-one wiring (images/all_in_one.png) plus the battery,
charger, switch and 5V boost feeding the ESP32. Kurdish (Badini) text.
Output: images/complete_robot.png, or images/complete_no_ir.png with the argument "noir"
(run tools/draw_all_in_one.py / tools/draw_all_no_ir.py first)
Usage: python3 tools/draw_complete.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import sys

IMG = Path(__file__).resolve().parent.parent / "images"
# with IR (default) or without IR:  python3 tools/draw_complete.py noir
SRC, DST, N0 = ("all_no_ir.png", "complete_no_ir.png", 16) if sys.argv[1:] == ["noir"] else \
    ("all_in_one.png", "complete_robot.png", 19)
top = Image.open(IMG / SRC)
W, PH = top.width, 1330
img = Image.new("RGB", (W, top.height + PH), (245, 242, 235))
img.paste(top, (0, 0))
d = ImageDraw.Draw(img)
Y0 = top.height
INK, RED, BLACK, GREY = (25, 25, 30), (215, 35, 35), (15, 15, 15), (110, 110, 110)


def font(s):
    return ImageFont.truetype("DejaVuSans-Bold.ttf", s, layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, t, s, c=INK, a="ma"):
    d.text((x, y), t, font=font(s), fill=c, anchor=a, direction="rtl")


def en(x, y, t, s, c=INK, a="ma"):
    d.text((x, y), t, font=font(s), fill=c, anchor=a)


def wire(pts, c):
    d.line(pts, fill=c, width=12, joint="curve")


def badge(x, y, n, c):
    d.ellipse([x - 27, y - 27, x + 27, y + 27], fill=c, outline=INK, width=3)
    en(x, y - 17, str(n), 28, (255, 255, 255))


def box(x0, y0, x1, y1, fill, title, sub=None):
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=fill, outline=INK, width=4)
    en((x0 + x1) / 2, y0 + (y1 - y0) / 2 - (26 if sub else 16), title, 32, (255, 255, 255))
    if sub:
        en((x0 + x1) / 2, y0 + (y1 - y0) / 2 + 12, sub, 22, (225, 225, 225))


d.line([(40, Y0 + 10), (W - 40, Y0 + 10)], fill=(200, 200, 200), width=3)
ku(W / 2, Y0 + 30, "کارەبا ڕۆبۆتی: باتری", 46)
ku(W / 2, Y0 + 92, "ب ڤی ڕەنگی، ڕۆبۆت بێ کێبلا USB کار دکەت", 26, GREY)

# blocks: battery -> TP4056 -> switch -> boost -> ESP32
by = Y0 + 160
d.rounded_rectangle([330, by, 750, by + 110], radius=16, fill=(40, 40, 45), outline=INK, width=4)
ku(540, by + 16, "باتری 18650", 32, (255, 255, 255)); en(540, by + 64, "3.7V", 24, (225, 225, 225))
en(360, by + 30, "-", 44, (255, 255, 255), "la"); en(720, by + 28, "+", 44, RED, "ra")

ty = by + 220
d.rounded_rectangle([330, ty, 750, ty + 140], radius=16, fill=(30, 80, 170), outline=INK, width=4)
en(540, ty + 30, "TP4056", 32, (255, 255, 255)); ku(540, ty + 80, "شارژکەر", 24, (225, 225, 225))
for x, y, t in ((350, ty + 30, "B-"), (730, ty + 30, "B+"), (350, ty + 110, "OUT-"), (730, ty + 110, "OUT+")):
    en(x, y - 12, t, 22, (255, 255, 255), "la" if x < 540 else "ra")

sy = ty + 250
d.rounded_rectangle([800, sy, 920, sy + 90], radius=12, fill=RED, outline=INK, width=4)
d.rectangle([830, sy + 22, 890, sy + 68], fill=(150, 15, 15))
ku(780, sy + 28, "سویچ", 28, INK, "ra")

boy = sy + 200
box(330, boy, 750, boy + 140, (25, 110, 70), "MT3608", "5V Boost")
for x, y, t in ((350, boy + 30, "IN-"), (730, boy + 30, "IN+"), (350, boy + 110, "OUT-"), (730, boy + 110, "OUT+")):
    en(x, y - 12, t, 22, (255, 255, 255), "la" if x < 540 else "ra")

ey = boy + 250
d.rounded_rectangle([250, ey, 830, ey + 110], radius=16, fill=(28, 28, 32), outline=INK, width=4)
en(540, ey + 14, "ESP32", 30, (200, 200, 200))
d.rounded_rectangle([630, ey + 55, 790, ey + 100], radius=8, fill=RED); en(710, ey + 62, "5V", 28, (255, 255, 255))
d.rounded_rectangle([290, ey + 55, 450, ey + 100], radius=8, fill=(90, 90, 95)); en(370, ey + 62, "GND", 28, (255, 255, 255))
ku(540, ey + 120, "چەپ، پینا 19 (هەمان پینا ئەمپلیفایەری)", 24, GREY)

# wires 19..24
wire([(750, by + 55), (900, by + 55), (900, ty + 30), (750, ty + 30)], RED); badge(900, (by + ty) / 2 + 40, N0 + 0, RED)
wire([(330, by + 55), (180, by + 55), (180, ty + 30), (330, ty + 30)], BLACK); badge(180, (by + ty) / 2 + 40, N0 + 1, BLACK)
wire([(750, ty + 110), (860, ty + 110), (860, sy)], RED); badge(860, ty + 185, N0 + 2, RED)
wire([(860, sy + 90), (860, boy + 30), (750, boy + 30)], RED); badge(860, sy + 145, N0 + 3, RED)
wire([(330, ty + 110), (180, ty + 110), (180, boy + 30), (330, boy + 30)], BLACK); badge(180, (ty + boy) / 2 + 60, N0 + 4, BLACK)
wire([(750, boy + 110), (900, boy + 110), (900, ey + 77), (790, ey + 77)], RED); badge(900, (boy + ey) / 2 + 70, N0 + 5, RED)
wire([(330, boy + 110), (180, boy + 110), (180, ey + 77), (290, ey + 77)], BLACK); badge(180, (boy + ey) / 2 + 70, N0 + 6, BLACK)

ku(W / 2, Y0 + PH - 95, "⚠ بەری وەستاندنا ESP32، پێچا MT3608 بزڤڕینە هەتا 5V", 26, RED)
ku(W / 2, Y0 + PH - 52, "⚠ دەمێ USB ب ڕۆبۆتی ڤە، سویچێ بگرە (OFF)", 26, RED)

img.save(IMG / DST)
print("saved", img.size)
