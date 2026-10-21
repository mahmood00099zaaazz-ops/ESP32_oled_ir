"""One clear picture per part: OLED, IR, INMP441 mic, MAX98357A amp + speaker.

Each picture shows the same 38-pin USB-C ESP32 and ONLY that part, with EVERY wire drawn all the
way to the ESP32 pin (power included, no tags). Kurdish (Badini) titles.
Output: images/part_1_oled.png, part_2_ir.png, part_3_mic.png, part_4_amp.png
Usage: python3 tools/draw_part_panels.py  (needs Pillow built with libraqm for right-to-left text)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "images"
W, H = 1080, 1720
BG = (246, 243, 236)
INK = (25, 25, 30)
GREY = (105, 105, 105)
RED = (215, 35, 35)
ORANGE = (240, 130, 20)
BLACK = (20, 20, 20)
GOLD = (222, 184, 80)

LEFT = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12",
        "GND", "13", "D2", "D3", "CMD", "5V"]
RIGHT = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4",
         "0", "2", "15", "D1", "D0", "CLK"]


def font(size):
    return ImageFont.truetype("DejaVuSans-Bold.ttf", size, layout_engine=ImageFont.Layout.RAQM)


class Panel:
    def __init__(self, bx0):
        self.img = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.img)
        self.bx0, self.bx1 = bx0, bx0 + 270
        self.by0, self.by1 = 200, 1180

    # ---- text ----
    def ku(self, x, y, t, size, color=INK, anchor="ma"):
        self.d.text((x, y), t, font=font(size), fill=color, anchor=anchor, direction="rtl")

    def en(self, x, y, t, size, color=INK, anchor="ma"):
        self.d.text((x, y), t, font=font(size), fill=color, anchor=anchor)

    # ---- ESP32 ----
    def pin_xy(self, side, name, which=0):
        names = LEFT if side == "L" else RIGHT
        idx = [i for i, n in enumerate(names) if n == name][which]
        pitch = (self.by1 - self.by0 - 80) / 18
        x = self.bx0 + 18 if side == "L" else self.bx1 - 18
        return x, self.by0 + 40 + idx * pitch, idx + 1

    def draw_esp(self, used):
        d = self.d
        bx0, bx1, by0, by1 = self.bx0, self.bx1, self.by0, self.by1
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=(24, 24, 28), outline=INK, width=4)
        d.rounded_rectangle([bx0 + 70, by0 + 20, bx1 - 70, by0 + 270], radius=6, fill=(196, 196, 200), outline=(90, 90, 95), width=3)
        self.en((bx0 + bx1) / 2, by0 + 120, "ESP32", 26, (70, 70, 75))
        d.rounded_rectangle([(bx0 + bx1) / 2 - 38, by1 - 36, (bx0 + bx1) / 2 + 38, by1 + 16], radius=9,
                            fill=(200, 200, 205), outline=INK, width=3)
        self.en((bx0 + bx1) / 2, by1 + 22, "USB-C", 20, GREY)
        for side, names in (("L", LEFT), ("R", RIGHT)):
            for i, n in enumerate(names):
                x, y, num = self.pin_xy(side, n, [k for k, m in enumerate(names[:i + 1]) if m == n].__len__() - 1)
                hot = (side, n, num) in used
                d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=GOLD if hot else (110, 100, 70), outline=INK, width=2)
                col = (255, 255, 255) if hot else (110, 110, 115)
                if side == "L":
                    self.en(x + 15, y - 11, n, 17, col, "la")
                else:
                    self.en(x - 15, y - 11, n, 17, col, "ra")

    # ---- wires ----
    def wire(self, p0, p3, color, bend):
        (x0, y0), (x3, y3) = p0, p3
        if isinstance(bend, list):                      # explicit path through these points
            pts = [p0] + bend + [p3]
            dark = tuple(max(0, v - 70) for v in color)
            self.d.line(pts, fill=dark, width=13, joint="curve")
            self.d.line(pts, fill=color, width=8, joint="curve")
            for q in (p0, p3):
                self.d.rectangle([q[0] - 8, q[1] - 8, q[0] + 8, q[1] + 8], fill=(30, 30, 30))
            return [p0] + bend + [p3]
        p1 = (x0 + bend[0], y0 + bend[1])
        p2 = (x3 + bend[2], y3 + bend[3])
        pts = []
        for i in range(41):
            t = i / 40
            a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
            pts.append((a * x0 + b * p1[0] + c * p2[0] + e * x3, a * y0 + b * p1[1] + c * p2[1] + e * y3))
        dark = tuple(max(0, v - 70) for v in color)
        self.d.line(pts, fill=dark, width=13, joint="curve")
        self.d.line(pts, fill=color, width=8, joint="curve")
        for p in (p0, p3):
            self.d.rectangle([p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8], fill=(30, 30, 30))
        return pts

    def badge(self, x, y, n, color):
        self.d.ellipse([x - 21, y - 21, x + 21, y + 21], fill=color, outline=INK, width=2)
        self.en(x, y - 14, str(n), 24, (255, 255, 255))

    def table(self, rows, y0):
        d = self.d
        d.rounded_rectangle([40, y0, W - 40, y0 + 30 + len(rows) * 66], radius=20, fill=(255, 255, 255), outline=INK, width=4)
        for k, (n, col, part_pin, esp_pin, where) in enumerate(rows):
            y = y0 + 22 + k * 66
            self.badge(W - 90, y + 20, n, col)
            self.en(W - 130, y + 4, part_pin, 28, INK, "ra")
            self.en(640, y + 2, "→", 32, col)
            self.en(590, y + 4, esp_pin, 28, col, "ra")
            self.ku(300, y + 8, where, 22, GREY, anchor="ra")

    def save(self, name):
        self.img.save(OUT_DIR / name)
        print("saved", name)


def where_text(side, num):
    return ("چەپ" if side == "L" else "ڕاست") + "، پینا " + str(num)


def build(file, title, sub, bx0, draw_module, conns, notes):
    """conns: list of (part_pin_label, (x, y) on module, esp side, esp pin name, which, colour, bend)."""
    p = Panel(bx0)
    p.ku(W / 2, 22, title, 56)
    p.ku(W / 2, 100, sub, 28, GREY)
    used = set()
    resolved = []
    for label, mp, side, epin, which, col, bend in conns:
        x, y, num = p.pin_xy(side, epin, which)
        used.add((side, epin, num))
        resolved.append((label, mp, (x, y), side, epin, num, col, bend))
    p.draw_esp(used)
    draw_module(p)
    rows = []
    for n, (label, mp, ep, side, epin, num, col, bend) in enumerate(resolved, 1):
        pts = p.wire(mp, ep, col, bend)
        mid = pts[len(pts) // 2]
        p.badge(mid[0], mid[1], n, col)
        esp_label = epin if not epin.isdigit() else "GPIO" + epin
        rows.append((n, col, label, esp_label, where_text(side, num)))
    p.table(rows, 1290)
    ny = 1290 + 30 + len(rows) * 66 + 24
    for k, t in enumerate(notes):
        p.ku(W / 2, ny + k * 44, t, 26, RED if k == 0 else GREY)
    p.save(file)


# =====================================================================
# 1) OLED (module on the right, uses right-column pins + 3V3 over the top)
# =====================================================================
def oled(p):
    d = p.d
    x0, y0, x1, y1 = 760, 190, 1010, 560
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(30, 70, 160), outline=INK, width=4)
    d.rectangle([x0 + 90, y0 + 20, x1 - 20, y1 - 20], fill=(8, 10, 16), outline=(60, 60, 70), width=3)
    for ey in (y0 + 80, y0 + 200):                       # eyes (screen is turned sideways)
        d.rounded_rectangle([x0 + 125, ey, x0 + 205, ey + 60], radius=12, fill=(90, 200, 255))
    for n, y in OLED_PINS.items():
        d.ellipse([x0 + 9, y - 9, x0 + 27, y + 9], fill=GOLD, outline=INK, width=2)
        p.en(x0 + 34, y - 11, n, 17, (255, 255, 255), "la")
    p.ku((x0 + x1) / 2, y1 + 14, "(شاشە ب لاڤە زڤڕاندیە)", 20, GREY)
    p.ku((x0 + x1) / 2, y1 + 44, "ڕێزبەندیا پینان دبیت جودا بیت", 18, GREY)


OLED_PINS = {"VCC": 240, "GND": 290, "SCL": 340, "SDA": 390}
OX = 778
build("part_1_oled.png", "١. شاشە OLED", "4 وایەر", 380, oled, [
    ("VCC", (OX, OLED_PINS["VCC"]), "L", "3V3", 0, ORANGE,
     [(720, 240), (720, 168), (345, 168), (345, 240)]),
    ("GND", (OX, OLED_PINS["GND"]), "R", "GND", 0, BLACK, (-70, 0, 70, 0)),
    ("SCL", (OX, OLED_PINS["SCL"]), "R", "22", 0, (30, 160, 90), (-50, 0, 50, 0)),
    ("SDA", (OX, OLED_PINS["SDA"]), "R", "21", 0, (40, 110, 220), (-70, 0, 70, 0)),
], ["VCC ب 3V3 ڤە، نە 5V", "ناڤێ پینان ل سەر شاشێ بخوینە"])


# =====================================================================
# 2) IR sensor (module on the left)
# =====================================================================
def ir(p):
    d = p.d
    x0, y0, x1, y1 = 40, 470, 300, 690
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(30, 85, 170), outline=INK, width=4)
    d.ellipse([x0 + 20, y0 + 20, x0 + 80, y0 + 80], fill=(245, 245, 245), outline=INK, width=2)
    d.ellipse([x0 + 20, y0 + 100, x0 + 80, y0 + 160], fill=(30, 30, 30), outline=INK, width=2)
    d.rectangle([x0 + 100, y0 + 30, x0 + 150, y0 + 80], fill=(60, 110, 230), outline=INK, width=2)
    for n, y in IR_PINS.items():
        d.ellipse([x1 - 27, y - 9, x1 - 9, y + 9], fill=GOLD, outline=INK, width=2)
        p.en(x1 - 36, y - 11, n, 18, (255, 255, 255), "ra")


IR_PINS = {"VCC": 520, "GND": 580, "OUT": 640}
build("part_2_ir.png", "٢. سێنسەرێ IR", "3 وایەر", 560, ir, [
    ("VCC", (282, IR_PINS["VCC"]), "L", "3V3", 0, ORANGE, (120, 0, -140, 0)),
    ("GND", (282, IR_PINS["GND"]), "L", "GND", 0, BLACK, (160, 0, -160, 0)),
    ("OUT", (282, IR_PINS["OUT"]), "L", "34", 0, (150, 70, 200), (140, 0, -140, 0)),
], ["VCC ب 3V3 ڤە", "ناڤێ پینان ل سەر سێنسەری بخوینە"])


# =====================================================================
# 3) INMP441 microphone (module on the left)
# =====================================================================
def mic(p):
    d = p.d
    cx, cy, r = 165, 600, 170
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(18, 18, 22), outline=(200, 160, 60), width=6)
    d.ellipse([cx - 22, cy - 90, cx + 22, cy - 46], fill=(80, 80, 85), outline=(200, 160, 60), width=3)
    p.en(cx - 30, cy - 26, "INMP441", 20, (230, 230, 230))
    for n, (x, y) in MIC_PINS.items():
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=GOLD, outline=INK, width=2)
        p.en(x - 16, y - 11, n, 18, (255, 255, 255), "ra")


MIC_PINS = {"VDD": (300, 470), "SD": (318, 530), "SCK": (325, 590), "WS": (318, 650),
            "GND": (300, 710), "L/R": (270, 765)}
build("part_3_mic.png", "٣. مایک INMP441", "6 وایەر", 560, mic, [
    ("VDD", MIC_PINS["VDD"], "L", "3V3", 0, ORANGE, (110, 0, -110, 0)),
    ("SD", MIC_PINS["SD"], "L", "35", 0, (220, 60, 160), (110, 0, -110, 0)),
    ("SCK", MIC_PINS["SCK"], "L", "32", 0, (110, 170, 30), (100, 0, -100, 0)),
    ("WS", MIC_PINS["WS"], "L", "33", 0, (0, 160, 180), (110, 0, -110, 0)),
    ("GND", MIC_PINS["GND"], "L", "GND", 0, BLACK, (120, 0, -120, 0)),
    ("L/R", MIC_PINS["L/R"], "L", "GND", 0, (90, 90, 90), (150, 30, -150, 20)),
], ["⚠ VDD ب 3V3 ڤە، نە 5V!", "L/R و GND هەردو دچنە GND"])


# =====================================================================
# 4) MAX98357A amplifier + speaker (module on the left)
# =====================================================================
def amp(p):
    d = p.d
    x0, y0, x1, y1 = 60, 760, 300, 1130
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(95, 55, 155), outline=INK, width=4)
    p.en(x0 + 80, y0 + 20, "MAX98357", 18, (230, 220, 255))
    d.rectangle([x0 + 50, y0 + 150, x0 + 110, y0 + 210], fill=(20, 20, 24))
    for n, y in AMP_PINS.items():
        d.ellipse([x1 - 27, y - 9, x1 - 9, y + 9], fill=GOLD, outline=INK, width=2)
        p.en(x1 - 36, y - 11, n, 18, (255, 255, 255) if n not in ("GAIN", "SD") else (180, 170, 200), "ra")
        if n in ("GAIN", "SD"):
            d.line([(x1 + 4, y - 9), (x1 + 22, y + 9)], fill=GREY, width=4)
            d.line([(x1 + 4, y + 9), (x1 + 22, y - 9)], fill=GREY, width=4)
    # terminal + speaker
    d.rectangle([x0 - 25, y0 + 260, x0 + 20, y0 + 340], fill=(40, 170, 110), outline=INK, width=3)
    p.en(x0 - 2, y0 + 266, "+", 22, (255, 255, 255))
    p.en(x0 - 2, y0 + 302, "-", 26, (255, 255, 255))
    scx, scy, sr = 150, 1200, 70
    d.line([(x0 - 25, y0 + 280), (22, y0 + 280), (22, scy - 20), (scx - sr + 4, scy - 20)], fill=RED, width=7)
    d.line([(x0 - 25, y0 + 320), (34, y0 + 320), (34, scy + 20), (scx - sr + 2, scy + 20)], fill=BLACK, width=7)
    d.ellipse([scx - sr, scy - sr, scx + sr, scy + sr], fill=(205, 205, 210), outline=INK, width=5)
    d.ellipse([scx - 45, scy - 45, scx + 45, scy + 45], outline=(150, 150, 155), width=4)
    p.en(scx, scy - 16, "8Ω", 26, INK)
    p.ku(scx + sr + 20, scy - 16, "بلندگۆ", 28, INK, anchor="la")


AMP_PINS = {"LRC": 800, "BCLK": 845, "DIN": 890, "GAIN": 935, "SD": 980, "GND": 1025, "Vin": 1070}


class AmpPanel:
    pass


build("part_4_amp.png", "٤. ئامپلیفایەر و بلندگۆ", "5 وایەر + بلندگۆ", 560, amp, [
    ("LRC", (282, AMP_PINS["LRC"]), "L", "25", 0, (0, 160, 180), (140, 0, -140, 0)),
    ("BCLK", (282, AMP_PINS["BCLK"]), "L", "26", 0, (110, 170, 30), (150, 0, -150, 0)),
    ("DIN", (282, AMP_PINS["DIN"]), "L", "27", 0, (220, 60, 160), (160, 0, -160, 0)),
    ("GND", (282, AMP_PINS["GND"]), "L", "GND", 0, BLACK, (170, 0, -170, 0)),
    ("Vin", (282, AMP_PINS["Vin"]), "L", "5V", 0, RED, (170, 0, -170, 0)),
], ["GAIN و SD بەتال بهێلە (✕)", "بلندگۆ ← پیچا کەسک (+ و -)"])
