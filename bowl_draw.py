# -*- coding: utf-8 -*-
"""Миска из файла «Насыпаем корм в миску»: тот же чертёж, уменьшенный под карточку."""
from __future__ import annotations

import flet as ft
import flet.canvas as cv

# Исходник: холст 700×520, CX 350, край 330, дно 473, стенка 14, верх 173, низ 103.
_SRC_W = 374.0  # внешняя ширина миски
_SCALE = 268.0 / _SRC_W

SCENE_W = 308
SCENE_H = 248
FILL_MAX = 70
POUR_SECONDS = 1.7

CX = 154.0
WALL = 14.0 * _SCALE
R_TOP = 173.0 * _SCALE
R_BOT = 103.0 * _SCALE
RIM_Y = 86.0
FLOOR_Y = RIM_Y + 143.0 * _SCALE
INNER_FLOOR = FLOOR_Y - WALL
GROUND = FLOOR_Y + WALL
SR = 7.0 * _SCALE
DX = 14.5 * _SCALE
DY = 12.4 * _SCALE
N_ROWS = 10
MOUND = 6
BOWL = "#4A7FB5"

KIBBLE = "#A0612B"
KIBBLE_DARK = "#7A431A"
KIBBLE_LIGHT = "#C58A4A"
PATE = "#C48A6A"
PATE_DARK = "#8A5340"
PATE_LIGHT = "#E2B39A"

KIBBLE_SET = (
    "#A0612B", "#8C4F20", "#B87333", "#7A431A", "#C58A4A",
)
PATE_SET = (
    "#8A5340", "#C48A6A", "#A86B52", "#E2B39A",
    "#7A4636", "#D4A08A", "#9A5C48", "#C48A6A",
)

LIP_Y = RIM_Y
WELL_CX = CX
WELL_CY = (RIM_Y + INNER_FLOOR) / 2


def _fill(color):
    return ft.Paint(color=color, style=ft.PaintingStyle.FILL)


def _stroke(color, width, cap=None):
    p = ft.Paint(color=color, style=ft.PaintingStyle.STROKE, stroke_width=width)
    if cap is not None:
        p.stroke_cap = cap
    p.stroke_join = ft.StrokeJoin.ROUND
    return p


def _mix(a, b, t):
    ar, ag, ab = _hex_rgb(a)
    br, bg, bb = _hex_rgb(b)
    return "#{:02X}{:02X}{:02X}".format(
        int(ar + (br - ar) * t),
        int(ag + (bg - ag) * t),
        int(ab + (bb - ab) * t),
    )


def _hex_rgb(color):
    c = color.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def fill_colors(wet=False):
    if wet:
        return PATE, PATE_DARK, PATE_LIGHT
    return KIBBLE, KIBBLE_DARK, KIBBLE_LIGHT


def _wall_half(y):
    span = FLOOR_Y - RIM_Y
    k = max(0.0, min(1.0, (FLOOR_Y - y) / span))
    return R_BOT + k * (R_TOP - R_BOT)


def _centerline():
    return [
        cv.Path.MoveTo(CX - R_TOP, RIM_Y),
        cv.Path.LineTo(CX - R_BOT, FLOOR_Y),
        cv.Path.LineTo(CX + R_BOT, FLOOR_Y),
        cv.Path.LineTo(CX + R_TOP, RIM_Y),
    ]


def _funnel():
    half = 100.0 * _SCALE
    mouth = 46.0 * _SCALE
    lip = 44.0 * _SCALE
    return [
        cv.Path.MoveTo(CX - half, 0),
        cv.Path.LineTo(CX + half, 0),
        cv.Path.LineTo(CX + mouth, lip),
        cv.Path.LineTo(CX - mouth, lip),
        cv.Path.Close(),
    ]


def bowl_back_canvas(is_cat=True):
    return cv.Canvas(
        width=SCENE_W,
        height=SCENE_H,
        shapes=[
            cv.Rect(0, 0, SCENE_W, SCENE_H, paint=_fill("#FBF4EA")),
            cv.Rect(0, GROUND, SCENE_W, SCENE_H - GROUND, paint=_fill("#D8C3A5")),
            cv.Oval(CX - 100 * _SCALE, GROUND + 1, 200 * _SCALE, 14 * _SCALE, paint=_fill("#1F000000")),
            cv.Path([*_centerline(), cv.Path.Close()], paint=_fill("#F7F1E6")),
            cv.Path(_funnel(), paint=_fill("#8A8F98")),
            cv.Rect(CX - 46 * _SCALE, 40 * _SCALE, 92 * _SCALE, 6 * _SCALE, paint=_fill("#6D727B")),
        ],
    )


def bowl_front_canvas(is_cat=True):
    return cv.Canvas(
        width=SCENE_W,
        height=SCENE_H,
        shapes=[
            cv.Path(_centerline(), paint=_stroke(BOWL, WALL * 2, cap=ft.StrokeCap.ROUND)),
            cv.Path(
                [
                    cv.Path.MoveTo(CX - R_TOP - 2 * _SCALE, RIM_Y + 2 * _SCALE),
                    cv.Path.LineTo(CX - R_BOT - 4 * _SCALE, FLOOR_Y - 4 * _SCALE),
                ],
                paint=_stroke("#4DFFFFFF", 4 * _SCALE, cap=ft.StrokeCap.ROUND),
            ),
        ],
    )


def heap_layout():
    """Те же ряды, что в файле: десять внутри и горка над краем."""
    specs = []
    rows = []
    prev = 0
    inset = 8.0 * _SCALE
    for k in range(N_ROWS + MOUND):
        y = INNER_FLOOR - SR - k * DY
        if k < N_ROWS:
            hw = _wall_half(y) - WALL / 0.9 - inset
            cnt = int(2 * hw / DX) + 1
            want_odd = k % 2 == 0
            if (cnt % 2 == 1) != want_odd:
                cnt -= 1
        else:
            cnt = prev - 3
        if cnt < 2:
            break
        prev = cnt
        rows.append((y, cnt, k))
    full_rows = N_ROWS + 2
    idx = 0
    for y, cnt, k in rows:
        if k < full_rows:
            base = 0.04 + (k + 0.55) / full_rows * 0.94
        else:
            base = 1.04 + (k - full_rows) * 0.08
        for i in range(cnt):
            x = CX + (i - (cnt - 1) / 2.0) * DX
            specs.append({
                "x": x - SR,
                "y": y - SR,
                "r": SR,
                "color": KIBBLE_SET[idx % len(KIBBLE_SET)],
                "t": base,
                "seed": idx,
            })
            idx += 1
    return specs


def spill_layout():
    spots = []
    gap = WALL + SR + 3
    idx = 0
    for sg in (-1, 1):
        n = 0
        for level in range(3):
            for col in range(4 - level):
                x = CX + sg * (R_BOT + gap + (col + level * 0.5) * DX)
                y = GROUND - SR - level * DY
                spots.append({
                    "x": x - SR,
                    "y": y - SR,
                    "r": SR,
                    "color": KIBBLE_SET[idx % len(KIBBLE_SET)],
                    "t": 1.06 + n * 0.03,
                    "seed": 40 + idx,
                })
                idx += 1
                n += 1
    return spots


HEAP = heap_layout()
SPILLS = spill_layout()

_heap_left = min(spec["x"] for spec in HEAP) - 1
_heap_top = min(spec["y"] for spec in HEAP) - 1
_heap_right = max(spec["x"] + spec["r"] * 2 for spec in HEAP) + 1
_heap_bottom = max(spec["y"] + spec["r"] * 2 for spec in HEAP) + 1
WELL_X = _heap_left
WELL_Y = _heap_top
WELL_W = _heap_right - _heap_left
WELL_H = _heap_bottom - _heap_top


def kibble_dot(color, size=14, seed=0):
    s = float(size)
    hi = s * 0.34
    return ft.Stack(
        [
            ft.Container(
                width=s,
                height=s,
                bgcolor=color,
                border_radius=s,
                border=ft.Border.all(1, "#59000000"),
            ),
            ft.Container(
                width=hi,
                height=hi,
                left=s * 0.2,
                top=s * 0.16,
                bgcolor="#47FFFFFF",
                border_radius=hi,
            ),
        ],
        width=s,
        height=s,
    )


def kibble_piece(color, w=11, h=8, radius=4, seed=0):
    return kibble_dot(color, max(w, h), seed=seed)


def palette_for(wet=False):
    return PATE_SET if wet else KIBBLE_SET


def export_scene(path, is_cat=True, ratio=1.0, scale=3):
    from PIL import Image, ImageDraw

    w, h = SCENE_W * scale, SCENE_H * scale
    img = Image.new("RGB", (w, h), _hex_rgb("#FBF4EA"))
    d = ImageDraw.Draw(img)

    def pellet(x, y, r, color):
        d.ellipse(
            (x * scale, y * scale, (x + r * 2) * scale, (y + r * 2) * scale),
            fill=_hex_rgb(color),
            outline=(70, 50, 30),
            width=max(1, scale // 2),
        )
        d.ellipse(
            ((x + r * 0.35) * scale, (y + r * 0.28) * scale,
             (x + r * 1.05) * scale, (y + r * 0.95) * scale),
            fill=(255, 255, 255, 70),
        )

    d.rectangle((0, GROUND * scale, w, h), fill=_hex_rgb("#D8C3A5"))
    d.ellipse(
        ((CX - 100 * _SCALE) * scale, (GROUND + 1) * scale,
         (CX + 100 * _SCALE) * scale, (GROUND + 1 + 14 * _SCALE) * scale),
        fill=(210, 190, 165),
    )
    inner = [
        ((CX - R_TOP) * scale, RIM_Y * scale),
        ((CX - R_BOT) * scale, FLOOR_Y * scale),
        ((CX + R_BOT) * scale, FLOOR_Y * scale),
        ((CX + R_TOP) * scale, RIM_Y * scale),
    ]
    d.polygon(inner, fill=_hex_rgb("#F7F1E6"))
    for spec in HEAP:
        if ratio >= spec["t"]:
            pellet(spec["x"], spec["y"], spec["r"], spec["color"])
    wall = [
        ((CX - R_TOP) * scale, RIM_Y * scale),
        ((CX - R_BOT) * scale, FLOOR_Y * scale),
        ((CX + R_BOT) * scale, FLOOR_Y * scale),
        ((CX + R_TOP) * scale, RIM_Y * scale),
    ]
    d.line(wall, fill=_hex_rgb(BOWL), width=max(1, int(WALL * 2 * scale)), joint="curve")
    for spec in SPILLS:
        if ratio >= spec["t"]:
            pellet(spec["x"], spec["y"], spec["r"], spec["color"])
    img.save(path)
    return path
