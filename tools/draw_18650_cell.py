"""Realistic-looking 18650 cell with its printed markings explained in Kurdish (Badini).

Output: images/battery_18650.png   Usage: python3 tools/draw_18650_cell.py
(needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "battery_18650.png"
W, H = 1080, 1700
BG = (250, 250, 246)
INK = (25, 25, 30)
RED = (215, 35, 35)
GREEN = (25, 145, 65)
GREY = (90, 90, 90)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size,
                              layout_engine=ImageFont.Layout.RAQM)


def ku(x, y, text, size=40, color=INK, anchor="ma"):
    d.text((x, y), text, font=font(size), fill=color, anchor=anchor, direction="rtl")


def en(x, y, text, size=40, color=INK, anchor="ma", draw=None):
    (draw or d).text((x, y), text, font=font(size), fill=color, anchor=anchor)


def shaded_cylinder(x0, y0, x1, y1, base, highlight=0.55):
    """Horizontal cylinder: brightness varies top->bottom to look round."""
    layer = Image.new("RGB", (x1 - x0, y1 - y0), base)
    ld = ImageDraw.Draw(layer)
    h = y1 - y0
    for yy in range(h):
        t = yy / (h - 1)
        # bright band near the top, darker at the bottom
        k = 1.0 + highlight * max(0.0, 1 - abs(t - 0.28) / 0.28) - 0.45 * max(0.0, t - 0.55) / 0.45
        c = tuple(max(0, min(255, int(v * k))) for v in base)
        ld.line([(0, yy), (x1 - x0, yy)], fill=c)
    return layer


# ---------------- Title ----------------
ku(W / 2, 30, "باتریا 18650", 66)
ku(W / 2, 118, "ئەڤە ب ڕاستی ب ڤی ڕەنگی دیار دبیت", 36, GREY)

# ---------------- The cell (side view) ----------------
CX0, CY0, CX1, CY1 = 150, 300, 900, 520          # wrapped body
# metal ends
mask_r = 34
body = shaded_cylinder(CX0, CY0, CX1, CY1, (40, 110, 200))
mask = Image.new("L", body.size, 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, body.size[0] - 1, body.size[1] - 1], radius=mask_r, fill=255)
# shadow
shadow = Image.new("L", (W, H), 0)
ImageDraw.Draw(shadow).rounded_rectangle([CX0 + 10, CY1 - 10, CX1 + 50, CY1 + 25], radius=30, fill=110)
shadow = shadow.filter(ImageFilter.GaussianBlur(16))
img.paste((170, 170, 165), (0, 0), shadow)
d = ImageDraw.Draw(img)

# negative end (flat metal) on the left
neg = shaded_cylinder(CX0 - 26, CY0 + 8, CX0 + 20, CY1 - 8, (175, 175, 180), 0.35)
img.paste(neg, (CX0 - 26, CY0 + 8))
# positive end (metal + raised button) on the right
pos = shaded_cylinder(CX1 - 20, CY0 + 8, CX1 + 24, CY1 - 8, (175, 175, 180), 0.35)
img.paste(pos, (CX1 - 20, CY0 + 8))
button = shaded_cylinder(CX1 + 24, CY0 + 70, CX1 + 46, CY1 - 70, (195, 195, 200), 0.35)
img.paste(button, (CX1 + 24, CY0 + 70))
img.paste(body, (CX0, CY0), mask)
d = ImageDraw.Draw(img)
d.rounded_rectangle([CX0, CY0, CX1, CY1], radius=mask_r, outline=INK, width=4)
d.rectangle([CX1 + 24, CY0 + 70, CX1 + 46, CY1 - 70], outline=INK, width=3)
d.rectangle([CX0 - 26, CY0 + 8, CX0, CY1 - 8], outline=INK, width=3)

# printed label on the wrapper
en((CX0 + CX1) / 2, CY0 + 28, "Li-ion  18650", 52, (255, 255, 255))
en((CX0 + CX1) / 2, CY0 + 100, "3.7V   2500mAh", 44, (255, 235, 120))
en((CX0 + CX1) / 2, CY0 + 160, "Rechargeable", 30, (220, 230, 255))
en(CX1 - 60, CY0 + 70, "+", 86, (255, 255, 255))
en(CX0 + 55, CY0 + 66, "-", 96, (255, 255, 255))
en((CX0 + CX1) / 2, CY1 + 40, "65 mm", 30, GREY)
d.line([(CX0 - 26, CY1 + 30), (CX1 + 46, CY1 + 30)], fill=GREY, width=2)

# ---------------- Callouts ----------------
def callout(px, py, tx, ty, lines, color):
    d.line([(px, py), (tx, ty)], fill=color, width=4)
    d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=color)
    for k, (t, s) in enumerate(lines):
        ku(tx, ty + 6 + k * (s + 12), t, s, color, anchor="ma")


# + end
callout(CX1 + 40, CY0 + 110, 880, 640, [("+  سەرێ زێدە", 42), ("دوگمەیەکا بلند هەیە", 30)], RED)
# - end
callout(CX0 - 15, CY0 + 110, 200, 640, [("-  سەرێ کێم", 42), ("تەخت و ڕاستە", 30)], INK)

# ---------------- End views ----------------
ku(W / 2, 800, "ژ سەری ڤە:", 40)


def end_view(cx, cy, raised, label, color):
    d.ellipse([cx - 110, cy - 110, cx + 110, cy + 110], fill=(40, 110, 200), outline=INK, width=4)
    d.ellipse([cx - 92, cy - 92, cx + 92, cy + 92], fill=(185, 185, 190), outline=INK, width=3)
    if raised:
        d.ellipse([cx - 45, cy - 45, cx + 45, cy + 45], fill=(215, 215, 220), outline=INK, width=3)
        for a in range(6):
            pass
    en(cx, cy - 32, label, 70, color)


end_view(780, 990, True, "+", RED)
end_view(300, 990, False, "-", INK)
ku(780, 1120, "دوگمە هەیە", 34, RED)
ku(300, 1120, "تەختە", 34, INK)

# ---------------- What the text means ----------------
d.rounded_rectangle([40, 1190, W - 40, 1660], radius=22, fill=(255, 255, 255), outline=INK, width=4)
ku(W - 80, 1212, "نڤیسینا ل سەر باتریێ چ دبێژیت؟", 40, INK, anchor="ra")
rows = [
    ("18650", "قەبارێ باتریێ"),
    ("3.7V", "ڤۆڵتێ وێ"),
    ("2500mAh", "چەند کارەبێ تێدا هەیە"),
    ("Li-ion", "دووبارە شارژ دبیت"),
]
for k, (code, mean) in enumerate(rows):
    y = 1290 + k * 70
    en(90, y, code, 40, (40, 110, 200), anchor="la")
    ku(W - 80, y + 4, mean, 36, INK, anchor="ra")
ku(W / 2, 1585, "⚠ ئەگەر باتری نەفخ بوو یان شکەستی بوو، بکار نەئینە!", 32, RED)

OUT.parent.mkdir(exist_ok=True)
img.save(OUT)
print("saved", OUT)
