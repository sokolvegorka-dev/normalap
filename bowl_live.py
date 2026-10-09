# -*- coding: utf-8 -*-
"""Корм падает из воронки и раскладывается по миске. Четыре тайминга, один за нажатие."""
from __future__ import annotations

import copy
import math
import random

import flet as ft
import flet.canvas as cv

from bowl_draw import KIBBLE_SET, PATE_SET

SRC_W = 700.0
SRC_H = 520.0
VIEW_W = 308
SCALE = VIEW_W / SRC_W
VIEW_H = int(round(SRC_H * SCALE))

CX = 350.0
FLOOR_Y = 473.0
RIM_Y = 330.0
WALL_R = 14.0
R_BOT = 103.0
R_TOP = 173.0
GROUND = FLOOR_Y + WALL_R
INNER_FLOOR = FLOOR_Y - WALL_R
SR = 7.0
DX = 14.5
DY = 12.4
N_ROWS = 10
MOUND = 6
G = 0.3
SPILL_MAX = 42
FLOOR_BASE = 205.0
FLOOR_DX = 15.0
RATES = (0.5, 0.5, 0.5, 0.5)
HEAP_R = 6.8       # средний радиус гранулы при укладке кучи
HEAP_BIN = 16.0    # ширина корзины для быстрого поиска соседей
REST_ANG = -2.36   # блик у покоящейся гранулы смотрит вверх-влево
BOUNCE_K = 0.36    # сколько скорости остаётся после удара
MEALS = ("Утро", "День", "Вечер", "Лишнее")
LABELS = (
    "Утро — первая треть миски",
    "День — вторая треть миски",
    "Вечер — миска до краёв",
    "Больше максимума — сыплется мимо",
)


def _clamp(v, a, b):
    return max(a, min(b, v))


def _rest_angle(x, y):
    """Каждая гранула лежит «своим боком»: блик чуть гуляет, но свет остаётся сверху."""
    h = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return REST_ANG + (h - math.floor(h) - 0.5) * 1.5


def _fill(color):
    return ft.Paint(color=color, style=ft.PaintingStyle.FILL)


def _stroke(color, width):
    paint = ft.Paint(color=color, style=ft.PaintingStyle.STROKE, stroke_width=width)
    paint.stroke_cap = ft.StrokeCap.ROUND
    paint.stroke_join = ft.StrokeJoin.ROUND
    return paint


class _Piece:
    def __init__(self, x, y, r, color):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.r = r
        self.c = color
        self.tx = x
        self.ty = y
        self.fx = x
        self.fy = y
        self.bounces = 0
        self.rest_ang = _rest_angle(x, y)
        self.ang = self.rest_ang
        self.spin = 0.0
        self.mode = "rest"
        self.leg = 1
        self.spill = False
        self.sg = 1
        self.fs = None
        self.settle = 99
        self.dot = None
        self.hi = None


class BowlLive:
    """Та же геометрия и физика, что в «Насыпаем корм в миску», но по нажатиям."""

    def __init__(self, wet=False, seed="bowl"):
        self.wet = bool(wet)
        self.seed = str(seed)
        self.colors = PATE_SET if self.wet else KIBBLE_SET
        self.scale = SCALE
        self.rng = random.Random(self.seed)
        self.pieces = []
        self.slots = []
        self.rows = []
        self.row_start = []
        self.end_idx = [0, 0, 0]
        self.mound_end = 0
        self.next_slot = 0
        self.floor_pile = {-1: [], 1: []}
        self.spill_spawned = 0
        self.spill_landed = 0
        self.stage = 0
        self.done = 0
        self.phase = "idle"
        self.wait_f = 0
        self.acc = 0.0
        self._back = []
        self._front = []
        self.canvas = cv.Canvas(width=VIEW_W, height=VIEW_H, shapes=[])
        self._build_static()
        self._rebuild_shapes()

    def label(self):
        if 0 <= self.stage < len(LABELS) and self.phase != "idle":
            return LABELS[self.stage]
        if self.done <= 0:
            return "Нажмите, чтобы насыпать"
        if self.done >= 4:
            return "Четыре горсти уже в миске"
        return LABELS[self.done - 1]

    def settle(self, steps):
        """Поставить уже насыпанные горсти на место, без падения."""
        self.rng = random.Random(self.seed)
        self.pieces = []
        self.next_slot = 0
        self.floor_pile = {-1: [], 1: []}
        self.spill_spawned = 0
        self.spill_landed = 0
        self.acc = 0.0
        self.wait_f = 0
        self.phase = "idle"
        self._build_slots()
        steps = max(0, min(4, int(steps)))
        for stage in range(steps):
            self.stage = stage
            guard = 0
            while guard < 5000 and self._spawn_one(False):
                guard += 1
        self.done = steps
        self.stage = min(steps, 3)
        self._rebuild_shapes()

    def export_state(self):
        return {
            "done": self.done,
            "stage": self.stage,
            "next_slot": self.next_slot,
            "spill_spawned": self.spill_spawned,
            "spill_landed": self.spill_landed,
            "rng": self.rng.getstate(),
            "floor_pile": copy.deepcopy(self.floor_pile),
            "slots": self.slots,
            "rows": self.rows,
            "row_start": self.row_start,
            "end_idx": list(self.end_idx),
            "mound_end": self.mound_end,
            "pieces": [
                {"x": piece.x, "y": piece.y, "r": piece.r, "c": piece.c}
                for piece in self.pieces
            ],
        }

    def restore(self, state):
        self.slots = state["slots"]
        self.rows = state["rows"]
        self.row_start = state["row_start"]
        self.end_idx = list(state["end_idx"])
        self.mound_end = state["mound_end"]
        self.next_slot = state["next_slot"]
        self.spill_spawned = state["spill_spawned"]
        self.spill_landed = state["spill_landed"]
        self.floor_pile = copy.deepcopy(state["floor_pile"])
        self.rng.setstate(state["rng"])
        self.stage = state["stage"]
        self.done = state["done"]
        self.phase = "idle"
        self.acc = 0.0
        self.wait_f = 0
        self.pieces = []
        for item in state["pieces"]:
            self._rest_piece(item["x"], item["y"], item["r"], item["c"])
        self._rebuild_shapes()

    def begin(self):
        if self.done >= 4 or self.phase != "idle":
            return False
        self.stage = self.done
        self.phase = "pour"
        self.acc = 0.0
        self.wait_f = 0
        return True

    def commit(self):
        if self.done < 4:
            self.done += 1
        self.phase = "idle"

    def force_rest(self):
        for piece in self.pieces:
            piece.x = piece.fx
            piece.y = piece.fy
            piece.tx = piece.fx
            piece.ty = piece.fy
            piece.mode = "rest"
            piece.settle = 99
            if piece.spill and piece.fs is not None:
                piece.fs["landed"] = True
        self.phase = "idle"

    @property
    def busy(self):
        return self.phase != "idle"

    def tick(self):
        if self.phase == "idle":
            return
        for piece in self.pieces:
            if piece.mode == "rest":
                piece.settle += 1
                continue
            piece.vy += G
            piece.vx *= 0.998
            piece.x += piece.vx
            piece.y += piece.vy
            piece.ang += piece.spin
            if piece.vy > 0 and piece.y >= piece.ty:
                self._land(piece)
        if self.phase == "pour":
            self.acc += RATES[min(self.stage, 3)] * self.rng.uniform(0.45, 1.55)
            while self.acc >= 1:
                if self._quota_met():
                    break
                self.acc -= 1
                if not self._spawn_one(True):
                    self.acc += 1
                    break
            if self._quota_met():
                self.phase = "wait"
                self.wait_f = 0
            return
        if any(piece.mode == "fall" for piece in self.pieces):
            self.wait_f = 0
            return
        self.wait_f += 1
        if self.wait_f > 18:
            self.phase = "idle"

    def _land(self, piece):
        """Удар о поверхность: отскок с потерей энергии и перекат к своему месту."""
        if piece.spill and piece.leg == 1 and piece.fs is not None:
            # упала на край миски: подпрыгнула и покатилась наружу к полу
            piece.leg = 2
            piece.x = piece.tx
            piece.y = piece.ty
            piece.vy = -self.rng.uniform(1.6, 2.4)
            piece.spin = piece.sg * self.rng.uniform(0.18, 0.32)
            piece.bounces = self.rng.choice((1, 2, 2))
            off = piece.sg * -self.rng.uniform(2, 5)
            self._aim(piece, piece.fs["x"], piece.fs["y"], off)
            if piece.sg * piece.vx < 0.8:
                piece.vx = piece.sg * 0.8
            return
        if piece.bounces > 0:
            left = piece.bounces
            piece.bounces -= 1
            vyb = max(1.1, abs(piece.vy) * BOUNCE_K)
            t = 2 * vyb / G
            piece.x = piece.tx
            piece.y = piece.ty
            dest = piece.x + (piece.fx - piece.x) / left
            piece.vy = -vyb
            piece.vx = (dest - piece.x) / t
            piece.tx = dest
            piece.spin *= 0.5
            return
        piece.x = piece.fx
        piece.y = piece.fy
        piece.tx = piece.fx
        piece.ty = piece.fy
        piece.vx = 0.0
        piece.vy = 0.0
        piece.mode = "rest"
        piece.settle = 99
        piece.rest_ang = _rest_angle(piece.fx, piece.fy)
        if piece.spill and piece.fs is not None:
            piece.fs["landed"] = True
            self.spill_landed += 1

    def _place(self, piece):
        scale = self.scale
        piece.dot.x = piece.x * scale
        piece.dot.y = piece.y * scale
        reach = piece.r * 0.42
        piece.hi.x = (piece.x + math.cos(piece.ang) * reach) * scale
        piece.hi.y = (piece.y + math.sin(piece.ang) * reach) * scale

    def apply(self):
        for piece in self.pieces:
            if piece.mode == "rest" and abs(piece.ang - piece.rest_ang) > 0.01:
                delta = (piece.rest_ang - piece.ang + math.pi) % (2 * math.pi) - math.pi
                piece.ang += delta * 0.3
            self._place(piece)
        self._rebuild_shapes()

    def _rebuild_shapes(self):
        shapes = list(self._back)
        for piece in self.pieces:
            if piece.dot is not None:
                shapes.append(piece.dot)
                shapes.append(piece.hi)
        shapes.extend(self._front)
        self.canvas.shapes = shapes

    def _wall_x(self, y):
        span = FLOOR_Y - RIM_Y
        k = _clamp((FLOOR_Y - y) / span, 0, 1)
        return R_BOT + k * (R_TOP - R_BOT)

    # ---- укладка корма: каждая гранула падает, скатывается в ямку и упирается в соседей ----

    def _heap_limit(self, y):
        """Насколько далеко от центра может стоять гранула на высоте y, чтобы не влезть в стенку."""
        return self._wall_x(y) - (WALL_R + HEAP_R) / 0.9 + 1.0

    def _heap_height(self, grid, x):
        """Где окажется центр гранулы, опущенной в x: на дне или поверх соседей."""
        y = INNER_FLOOR - HEAP_R
        reach = 2 * HEAP_R * 0.97
        b = int(x // HEAP_BIN)
        for key in (b - 1, b, b + 1):
            for ox, oy in grid.get(key, ()):
                dx = abs(x - ox)
                if dx < reach:
                    cy = oy - math.sqrt(reach * reach - dx * dx)
                    if cy < y:
                        y = cy
        return y

    def _heap_fit(self, grid, x):
        """Гранула не может стоять в стенке: сдвигаем в сторону и ищем высоту заново."""
        y = self._heap_height(grid, x)
        for _ in range(3):
            lim = self._heap_limit(y)
            x = _clamp(x, CX - lim, CX + lim)
            y = self._heap_height(grid, x)
        return x, y

    def _heap_drop(self, grid, x0):
        x, y = self._heap_fit(grid, x0)
        for _ in range(70):
            best_x, best_y = x, y
            for step in (-2.2, 2.2):
                nx, ny = self._heap_fit(grid, x + step)
                if ny > best_y + 0.25:
                    best_x, best_y = nx, ny
            if best_x == x:
                break
            x, y = best_x, best_y
        return x, y

    def _build_slots(self):
        """Вся «полная миска» с куполом укладывается один раз, потом делится на три равные доли."""
        grid = {}
        slots = []
        peak, edge = 284.0, 336.0   # высота вершины и краёв купола для центров гранул
        side = _clamp(self._heap_limit(edge), 40, 160)
        misses = 0
        while misses < 70 and len(slots) < 420:
            # из нескольких мест берём самое низкое: слои поднимаются ровно, без столбиков у стенок
            best = None
            for _ in range(6):
                x0 = CX + self.rng.uniform(-side, side)
                x, y = self._heap_drop(grid, x0)
                dome = peak + (edge - peak) * min(1.0, abs(x - CX) / side) ** 1.3
                if y < dome - 0.5:
                    continue
                if best is None or y > best[1]:
                    best = (x, y)
            if best is None:
                misses += 1
                continue
            misses = 0
            x, y = best
            x += self.rng.uniform(-0.5, 0.5)
            grid.setdefault(int(x // HEAP_BIN), []).append((x, y))
            slots.append({"x": x, "y": y})
        total = len(slots)
        self.rows = []
        self.row_start = [0, total]
        self.slots = slots
        self.mound_end = total
        # утро, день и вечер — ровно по трети; четвёртое нажатие уже выше максимума
        self.end_idx = [round(total / 3), round(total * 2 / 3), total]

    def _quota_met(self):
        if self.stage >= 3:
            return self.spill_spawned >= SPILL_MAX
        limit = self.end_idx[self.stage]
        return self.next_slot >= limit

    def _spawn_one(self, falling):
        if self.stage < 3:
            if self.next_slot >= self.end_idx[self.stage]:
                return False
            slot = self.slots[self.next_slot]
            self.next_slot += 1
            self._new_piece(slot["x"], slot["y"], falling)
            return True
        if self.spill_spawned < SPILL_MAX and self._spawn_spill(falling):
            return True
        return False

    def _spawn_spill(self, falling):
        sg = 1 if self.spill_spawned % 2 else -1
        spot = self._pick_floor(sg)
        if spot is None:
            return False
        cap_x = CX + sg * (R_TOP + 21 * 0.77)
        cap_y = RIM_Y - 21 * 0.64
        piece = self._new_piece(cap_x, cap_y, falling)
        piece.spill = True
        piece.sg = sg
        piece.fs = spot
        self.spill_spawned += 1
        if not falling:
            piece.x = spot["x"]
            piece.y = spot["y"]
            piece.tx = spot["x"]
            piece.ty = spot["y"]
            piece.fx = spot["x"]
            piece.fy = spot["y"]
            piece.mode = "rest"
            piece.settle = 99
            spot["landed"] = True
            self.spill_landed += 1
            self._place(piece)
        return True

    def _rest_height(self, pile, x):
        """Где окажется центр гранулы, упавшей в точку x: на полу или поверх соседей."""
        y = GROUND - SR
        for other in pile:
            dx = abs(x - other["x"])
            reach = 2 * SR * 0.96
            if dx < reach:
                y = min(y, other["y"] - math.sqrt(reach * reach - dx * dx))
        return y

    def _pick_floor(self, sg):
        """Россыпь, а не пирамида: гранула падает в случайную точку и скатывается в ямку."""
        pile = self.floor_pile[sg]
        if len(pile) >= 90:
            return None
        spread = min(115.0, abs(self.rng.gauss(0, 48)))
        x = CX + sg * (FLOOR_BASE + spread)
        best_x, best_y = x, self._rest_height(pile, x)
        for step in range(1, 9):
            for direction in (-1, 1):
                cx = x + direction * step * 2.5
                if sg * (cx - CX) < FLOOR_BASE - 6:
                    continue
                cy = self._rest_height(pile, cx)
                if cy > best_y + 0.4:
                    best_x, best_y = cx, cy
        best_x += self.rng.uniform(-0.8, 0.8)
        spot = {
            "key": f"{len(pile)}",
            "landed": False,
            "x": best_x,
            "y": best_y,
        }
        pile.append(spot)
        return spot

    def _new_piece(self, tx, ty, falling):
        x = CX + _clamp((tx - CX) * 0.45 + self.rng.uniform(-5, 5), -42, 42)
        vy = self.rng.uniform(1, 2.5)
        radius = self.rng.uniform(6.2, 7.2)
        color = self.colors[int(self.rng.random() * len(self.colors))]
        piece = _Piece(x, self.rng.uniform(46, 58) if falling else ty, radius, color)
        piece.vy = vy
        if falling:
            piece.mode = "fall"
            piece.settle = 0
            piece.ang = self.rng.uniform(-math.pi, math.pi)
            piece.spin = self.rng.choice((-1, 1)) * self.rng.uniform(0.12, 0.34)
            if tx > CX + R_TOP * 0.9 or tx < CX - R_TOP * 0.9:
                piece.bounces = 0
                off = 0.0
            else:
                piece.bounces = self.rng.choice((1, 2, 2, 3))
                # падает ближе к центру и скатывается к своему месту
                side = 1 if tx >= CX else -1
                off = -side * self.rng.uniform(5, 15)
            self._aim(piece, tx, ty, off)
        else:
            piece.x = tx
            piece.y = ty
            piece.tx = tx
            piece.ty = ty
            piece.fx = tx
            piece.fy = ty
            piece.mode = "rest"
            piece.settle = 99
        self._paint_piece(piece)
        self.pieces.append(piece)
        return piece

    def _rest_piece(self, x, y, radius, color):
        piece = _Piece(x, y, radius, color)
        piece.mode = "rest"
        piece.settle = 99
        self._paint_piece(piece)
        self.pieces.append(piece)
        return piece

    def _paint_piece(self, piece):
        scale = self.scale
        piece.dot = cv.Circle(
            piece.x * scale, piece.y * scale, piece.r * scale, paint=_fill(piece.c),
        )
        piece.hi = cv.Circle(0, 0, piece.r * 0.3 * scale, paint=_fill("#47FFFFFF"))
        self._place(piece)

    def _aim(self, piece, fx, fy, off=0.0):
        """Первый удар приходится на fx+off, потом отскоки докатывают гранулу до (fx, fy)."""
        piece.fx = fx
        piece.fy = fy
        lx = fx + off
        dy = fy - piece.y
        disc = piece.vy * piece.vy + 2 * G * dy
        if dy <= 0 or disc < 0:
            piece.x = fx
            piece.y = fy
            piece.tx = fx
            piece.ty = fy
            piece.vx = 0
            piece.mode = "rest"
            return
        t = (-piece.vy + math.sqrt(disc)) / G
        if t < 0.5:
            t = 0.5
        piece.vx = (lx - piece.x) / t
        piece.tx = lx
        piece.ty = fy

    def _s(self, v):
        return v * self.scale

    def _bowl_path(self):
        return [
            cv.Path.MoveTo(self._s(CX - R_TOP), self._s(RIM_Y)),
            cv.Path.LineTo(self._s(CX - R_BOT), self._s(FLOOR_Y)),
            cv.Path.LineTo(self._s(CX + R_BOT), self._s(FLOOR_Y)),
            cv.Path.LineTo(self._s(CX + R_TOP), self._s(RIM_Y)),
        ]

    def _build_static(self):
        s = self._s
        self._back = [
            cv.Rect(
                0, 0, VIEW_W, VIEW_H,
                paint=ft.Paint(
                    style=ft.PaintingStyle.FILL,
                    gradient=ft.PaintLinearGradient(
                        begin=(0, 0),
                        end=(0, VIEW_H),
                        colors=["#FBF4EA", "#EFE3D2"],
                    ),
                ),
            ),
            cv.Rect(0, s(GROUND), VIEW_W, VIEW_H - s(GROUND), paint=_fill("#D8C3A5")),
            cv.Oval(s(CX - 150), s(GROUND + 2), s(300), s(14), paint=_fill("#1F000000")),
            cv.Path([*self._bowl_path(), cv.Path.Close()], paint=_fill("#66FFFFFF")),
            cv.Path(
                [
                    cv.Path.MoveTo(s(CX - 100), 0),
                    cv.Path.LineTo(s(CX + 100), 0),
                    cv.Path.LineTo(s(CX + 46), s(44)),
                    cv.Path.LineTo(s(CX - 46), s(44)),
                    cv.Path.Close(),
                ],
                paint=_fill("#8A8F98"),
            ),
            cv.Rect(s(CX - 46), s(40), s(92), s(6), paint=_fill("#6D727B")),
        ]
        self._front = [
            cv.Path(self._bowl_path(), paint=_stroke("#4A7FB5", s(WALL_R * 2))),
            cv.Path(
                [
                    cv.Path.MoveTo(s(CX - R_TOP - 2), s(RIM_Y + 2)),
                    cv.Path.LineTo(s(CX - R_BOT - 4), s(FLOOR_Y - 4)),
                ],
                paint=_stroke("#4DFFFFFF", max(1.5, s(4))),
            ),
        ]
        self.canvas.shapes = [*self._back, *self._front]
