"""Generates printable STL parts for the talking robot shell.

Requires: pip install manifold3d numpy
Run:      python make_robot_stl.py   (STLs are written next to this file)

All sizes are in mm. X = width, Y = depth (front is -Y), Z = up.
"""
import os
import struct

import numpy as np
from manifold3d import Manifold

WALL = 2.0
SEG = 64
OUT = os.path.dirname(os.path.abspath(__file__))

# Head: holds the 0.96" OLED (27x27 module) and the INMP441 mic
HEAD = (80, 60, 66, 24)        # width, depth, height, corner radius
OLED_WINDOW = (26, 15)         # visible glass opening
# Body: holds ESP32 DevKit, MAX98357A and a 40 mm speaker
BODY = (76, 56, 80, 24)
SPEAKER_D = 36                 # grille diameter
NECK_HOLE = 14                 # wires pass from body to head
# Base: holds 18650 battery, TP4056 charger, MT3608 boost and switch
BASE_D, BASE_H = 110, 26


def rounded_box(w, d, h, r):
    """Box centered on the origin with fully rounded corners."""
    x, y, z = w / 2 - r, d / 2 - r, h / 2 - r
    balls = [Manifold.sphere(r, SEG).translate((sx * x, sy * y, sz * z))
             for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    return Manifold.batch_hull(balls)


def shell(w, d, h, r):
    return rounded_box(w, d, h, r) - rounded_box(w - 2 * WALL, d - 2 * WALL, h - 2 * WALL, r - WALL)


def cyl(d, h, center=True):
    return Manifold.cylinder(h, d / 2, d / 2, SEG, center)


def box(w, d, h):
    return Manifold.cube((w, d, h), True)


def split_front_back(m):
    """Cuts a closed shell at Y=0 so each half prints open side down."""
    front = m - box(400, 400, 400).translate((0, 200, 0))
    back = m - box(400, 400, 400).translate((0, -200, 0))
    return front, back


def head():
    w, d, h, r = HEAD
    m = shell(w, d, h, r)
    m -= box(OLED_WINDOW[0], 20, OLED_WINDOW[1]).translate((0, -d / 2, 4))   # eye window
    m -= cyl(3, 20).translate((0, -10, h / 2))                    # mic hole on top
    m -= cyl(NECK_HOLE, 20).translate((0, 0, -h / 2))             # neck
    # OLED ledge: a frame behind the window the module rests against
    frame = box(31, 3, 31) - box(OLED_WINDOW[0] + 1, 4, OLED_WINDOW[1] + 8)
    m += frame.translate((0, -d / 2 + WALL + 4.5, 4))
    return split_front_back(m)


def body():
    w, d, h, r = BODY
    m = shell(w, d, h, r)
    m -= cyl(NECK_HOLE, 20).translate((0, 0, h / 2))              # neck
    m -= cyl(20, 20).translate((0, 0, -h / 2))                    # wires to base
    # speaker grille: rings of 3 mm holes on the front
    cz = -6
    holes = [cyl(3, 20).rotate((90, 0, 0)).translate((0, -d / 2, cz))]
    for ring, n in ((8, 8), (15, 14)):
        for i in range(n):
            a = 2 * np.pi * i / n
            holes.append(cyl(3, 20).rotate((90, 0, 0))
                         .translate((ring * np.cos(a), -d / 2, cz + ring * np.sin(a))))
    for hole in holes:
        m -= hole
    # side holes for SG90 servo shafts (arms)
    m -= cyl(7, w + 20).rotate((0, 90, 0)).translate((0, 0, 14))
    return split_front_back(m)


def arm():
    a = Manifold.sphere(10, SEG).scale((0.7, 1.0, 2.2))
    a = a - box(40, 40, 40).translate((20 + 2, 0, 0))             # flat side against body
    a -= cyl(4.8, 12).rotate((0, 90, 0)).translate((0, 0, 12))    # servo horn spline
    return a.rotate((0, -90, 0))                                   # flat side down


def base():
    m = cyl(BASE_D, BASE_H, False) - cyl(BASE_D - 2 * WALL, BASE_H - WALL, False)
    # soft top edge
    m -= (cyl(BASE_D + 10, 4, False) - Manifold.cylinder(4, BASE_D / 2 + 0.01, BASE_D / 2 - 3, SEG)).translate((0, 0, BASE_H - 4))
    m -= cyl(20, 10).translate((0, 0, BASE_H))                    # wires to body
    m -= box(13, 20, 7).translate((0, BASE_D / 2, 9))             # USB charge port (back)
    m -= box(20, 13, 7).translate((BASE_D / 2, 0, 9))             # power switch (side)
    # printed upside down: top surface on the bed, open bottom facing up
    return m.rotate((180, 0, 0)).translate((0, 0, BASE_H))


def base_lid():
    lid = cyl(BASE_D - 2 * WALL - 0.4, 2, False)
    lid += cyl(BASE_D - 2 * WALL - 4.4, 4, False) - cyl(BASE_D - 2 * WALL - 8.4, 4, False)
    return lid


def neck_ring():
    return cyl(NECK_HOLE + 6, 8, False) - cyl(NECK_HOLE - 2, 8, False) + \
        (cyl(NECK_HOLE - 0.4, 14, False) - cyl(NECK_HOLE - 4, 14, False)).translate((0, 0, -3))


def save_stl(m, name):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(b"talking robot".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        for k in range(len(t)):
            f.write(struct.pack("<12fH", *n[k], *tri[k].ravel(), 0))
    return v, t


def lay_flat_half(m, front):
    """Rotates a front/back half so its open cut face sits on the bed."""
    m = m.rotate((-90 if front else 90, 0, 0))
    z0 = m.bounding_box()[2]
    return m.translate((0, 0, -z0))


def parts():
    hf, hb = head()
    bf, bb = body()
    return {
        "head_front.stl": lay_flat_half(hf, True),
        "head_back.stl": lay_flat_half(hb, False),
        "body_front.stl": lay_flat_half(bf, True),
        "body_back.stl": lay_flat_half(bb, False),
        "arm_x2.stl": arm().translate((0, 0, 7)),
        "base.stl": base(),
        "base_lid.stl": base_lid(),
        "neck_ring.stl": neck_ring().translate((0, 0, 3)),
    }, (hf + hb, bf + bb)


if __name__ == "__main__":
    ps, _ = parts()
    for name, m in ps.items():
        _, t = save_stl(m, name)
        b = m.bounding_box()
        print(f"{name:16s} {b[3]-b[0]:6.1f} x {b[4]-b[1]:6.1f} x {b[5]-b[2]:6.1f} mm  {len(t)} tris  ok={m.status()}")
