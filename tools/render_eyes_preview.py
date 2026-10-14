"""Render a preview of the robot eyes drawn by OLED_IR_CODE.ino.

Re-creates the U8g2 drawing calls on a 128x64 pixel buffer and saves:
  images/robot_eyes_preview.png  - the three eye states side by side
  images/robot_eyes_animation.gif - the blink / look-up animation

Usage: python3 tools/render_eyes_preview.py   (requires Pillow)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 128, 64
SCALE = 4
PIXEL_ON = (90, 200, 255)
PIXEL_OFF = (8, 12, 20)
OUT = Path(__file__).resolve().parent.parent / "images"


class Oled:
    def __init__(self):
        self.px = [[0] * W for _ in range(H)]

    def draw_box(self, x, y, w, h):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if 0 <= xx < W and 0 <= yy < H:
                    self.px[yy][xx] = 1

    def draw_filled_ellipse(self, x0, y0, rx, ry):
        # U8g2 takes integer arguments, so the sketch's 99.5 / 19.5 are truncated.
        x0, y0, rx, ry = int(x0), int(y0), int(rx), int(ry)
        for yy in range(y0 - ry, y0 + ry + 1):
            for xx in range(x0 - rx, x0 + rx + 1):
                if ((xx - x0) / rx) ** 2 + ((yy - y0) / ry) ** 2 <= 1.0:
                    if 0 <= xx < W and 0 <= yy < H:
                        self.px[yy][xx] = 1

    def to_image(self):
        img = Image.new("RGB", (W * SCALE, H * SCALE), PIXEL_OFF)
        d = ImageDraw.Draw(img)
        for y in range(H):
            for x in range(W):
                if self.px[y][x]:
                    d.rectangle(
                        [x * SCALE, y * SCALE, x * SCALE + SCALE - 2, y * SCALE + SCALE - 2],
                        fill=PIXEL_ON,
                    )
        return img


# Same drawing calls as the functions in OLED_IR_CODE.ino
def eye_up():
    o = Oled()
    o.draw_box(80, 12, 40, 20)
    o.draw_box(10, 12, 40, 20)
    o.draw_filled_ellipse(99.5, 13, 19.5, 11)
    o.draw_filled_ellipse(29.5, 13, 19.5, 11)
    return o.to_image()


def eye_open():
    o = Oled()
    o.draw_box(14, 13, 36, 36)
    o.draw_box(78, 13, 36, 36)
    return o.to_image()


def eye_close():
    o = Oled()
    o.draw_box(14, 27, 36, 7)
    o.draw_box(78, 27, 36, 7)
    return o.to_image()


def framed(screen, label, font):
    pad, label_h = 24, 40
    img = Image.new("RGB", (screen.width + 2 * pad, screen.height + 2 * pad + label_h), (30, 30, 36))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, img.width - 5, screen.height + 2 * pad - 5], radius=14, fill=(0, 0, 0))
    img.paste(screen, (pad, pad))
    tw = d.textlength(label, font=font)
    d.text(((img.width - tw) / 2, screen.height + 2 * pad + 6), label, fill=(230, 230, 230), font=font)
    return img


def main():
    OUT.mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()

    states = [
        (eye_open(), "eye_open()  - IR = 1"),
        (eye_close(), "eye_close() - blink"),
        (eye_up(), "eye_up()  - IR = 0"),
    ]
    panels = [framed(s, label, font) for s, label in states]
    gap = 16
    sheet = Image.new(
        "RGB",
        (sum(p.width for p in panels) + gap * (len(panels) + 1), panels[0].height + 2 * gap),
        (20, 20, 24),
    )
    x = gap
    for p in panels:
        sheet.paste(p, (x, gap))
        x += p.width + gap
    sheet.save(OUT / "robot_eyes_preview.png")

    # Timing follows the sketch: open 1000 ms, closed 300 ms, then look up.
    open_, close, up = (s for s, _ in states)
    frames = [open_, close, open_, close, open_, up]
    durations = [1000, 300, 1000, 300, 1000, 1500]
    frames[0].save(
        OUT / "robot_eyes_animation.gif",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
    )


if __name__ == "__main__":
    main()
