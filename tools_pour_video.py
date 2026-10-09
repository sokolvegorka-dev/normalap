# -*- coding: utf-8 -*-
"""Собрать видео падения корма из того же чертежа, что «Насыпаем корм в миску»."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "bowl" / "pour.mp4"
META = ROOT / "assets" / "bowl" / "pour.json"

W, H = 700, 520
CX, FLOOR_Y, RIM_Y = 350.0, 473.0, 330.0
WALL_R, R_BOT, R_TOP = 14.0, 103.0, 173.0
GROUND = FLOOR_Y + WALL_R
INNER_FLOOR = FLOOR_Y - WALL_R
DEPTH = INNER_FLOOR - RIM_Y
COLORS = ("#a0612b", "#8c4f20", "#b87333", "#7a431a", "#c58a4a")
SR, DX, DY = 7.0, 14.5, 12.4
N_ROWS, MOUND, G = 10, 6, 0.3
SPILL_MAX = 36
FLOOR_BASE, FLOOR_DX = 226.0, 15.0
FPS = 30
LOGIC_PER_FRAME = 2
HOLD = 8

rng = random.Random(4)


def clamp(v, a, b):
    return max(a, min(b, v))


def wall_x(y):
    k = clamp((FLOOR_Y - y) / (FLOOR_Y - RIM_Y), 0, 1)
    return R_BOT + k * (R_TOP - R_BOT)


def hex_rgb(color):
    c = color.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def build_slots():
    rows = []
    prev = 0
    for k in range(N_ROWS + MOUND):
        y = INNER_FLOOR - SR - k * DY
        if k < N_ROWS:
            hw = wall_x(y) - WALL_R / 0.9 - 8
            cnt = int(2 * hw / DX) + 1
            if (cnt % 2) != (1 if k % 2 == 0 else 0):
                cnt -= 1
        else:
            cnt = prev - 3
        prev = cnt
        row = []
        for i in range(max(0, cnt)):
            row.append({
                "x": CX + (i - (cnt - 1) / 2) * DX + rng.uniform(-1, 1),
                "y": y + rng.uniform(-0.8, 0.8),
            })
        for i in range(len(row) - 1, 0, -1):
            j = rng.randrange(i + 1)
            row[i], row[j] = row[j], row[i]
        rows.append(row)
    slots, row_start = [], []
    for row in rows:
        row_start.append(len(slots))
        slots.extend(row)
    row_start.append(len(slots))
    full = row_start[N_ROWS + 2]
    mound_end = row_start[min(N_ROWS + 5, len(row_start) - 1)]
    return slots, full, mound_end


def aim(p, tx, ty):
    dy = ty - p["y"]
    disc = p["vy"] * p["vy"] + 2 * G * dy
    t = (-p["vy"] + math.sqrt(max(disc, 0.01))) / G
    if t < 1:
        t = 1
    p["vx"] = (tx - p["x"]) / t
    p["tx"] = tx
    p["ty"] = ty


def new_piece(pieces, tx, ty):
    p = {
        "x": CX + clamp((tx - CX) * 0.45 + rng.uniform(-5, 5), -42, 42),
        "y": 52.0,
        "vx": 0.0,
        "vy": rng.uniform(1, 2.5),
        "r": rng.uniform(6.2, 7.2),
        "c": COLORS[rng.randrange(len(COLORS))],
        "mode": "fall",
        "leg": 1,
        "spill": False,
        "settle": 0,
        "sg": 0,
        "fs": None,
    }
    aim(p, tx, ty)
    pieces.append(p)
    return p


def pick_floor(pile, sg):
    cand = []
    for h in range(6):
        for j in range(6 - h):
            key = f"{h},{j}"
            if any(q["key"] == key for q in pile):
                continue
            if h > 0:
                under_l = any(q["key"] == f"{h - 1},{j}" and q["landed"] for q in pile)
                under_r = any(q["key"] == f"{h - 1},{j + 1}" and q["landed"] for q in pile)
                if not (under_l and under_r):
                    continue
            cand.append((h, j, key))
    if not cand:
        return None
    h, j, key = cand[rng.randrange(len(cand))]
    slot = {
        "key": key,
        "landed": False,
        "x": CX + sg * (FLOOR_BASE + j * FLOOR_DX + h * FLOOR_DX / 2),
        "y": GROUND - SR - h * DY,
    }
    pile.append(slot)
    return slot


def step_physics(pieces):
    for p in pieces:
        if p["mode"] == "rest":
            p["settle"] += 1
            continue
        p["vy"] += G
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        if p["vy"] > 0 and p["y"] >= p["ty"]:
            if p["spill"] and p["leg"] == 1:
                p["leg"] = 2
                p["x"] = p["tx"]
                p["y"] = p["ty"]
                p["vy"] = -1.5
                aim(p, p["fs"]["x"], p["fs"]["y"])
                if p["sg"] * p["vx"] < 0.8:
                    p["vx"] = p["sg"] * 0.8
            else:
                p["x"] = p["tx"]
                p["y"] = p["ty"]
                p["mode"] = "rest"
                p["settle"] = 0
                if p["spill"]:
                    p["fs"]["landed"] = True


def make_background():
    img = Image.new("RGB", (W, H))
    px = img.load()
    top, bot = hex_rgb("#fbf4ea"), hex_rgb("#efe3d2")
    for y in range(H):
        t = y / (H - 1)
        col = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = col
    d = ImageDraw.Draw(img)
    d.rectangle((0, GROUND, W, H), fill=hex_rgb("#d8c3a5"))
    d.ellipse((CX - 150, GROUND + 6 - 7, CX + 150, GROUND + 6 + 7), fill=(210, 196, 176))
    d.polygon(
        [(CX - R_TOP, RIM_Y), (CX - R_BOT, FLOOR_Y), (CX + R_BOT, FLOOR_Y), (CX + R_TOP, RIM_Y)],
        fill=(247, 241, 230),
    )
    y23 = INNER_FLOOR - DEPTH * 2 / 3
    ink = (74, 127, 181)
    for y, label, x0 in (
        (y23, "2/3", CX + wall_x(y23) + WALL_R + 8),
        (RIM_Y, "полная", CX + R_TOP + WALL_R + 8),
    ):
        for x in range(int(x0), int(x0 + 42), 8):
            d.line((x, y, min(x + 5, x0 + 42), y), fill=ink, width=1)
        d.text((x0 + 46, y - 6), label, fill=ink)
    d.polygon(
        [(CX - 100, 0), (CX + 100, 0), (CX + 46, 44), (CX - 46, 44)],
        fill=hex_rgb("#8a8f98"),
    )
    d.rectangle((CX - 46, 40, CX + 46, 46), fill=hex_rgb("#6d727b"))
    return img


def paint(base, pieces):
    img = base.copy()
    d = ImageDraw.Draw(img)
    for p in pieces:
        y = p["y"]
        if p["mode"] == "rest" and p["settle"] < 18:
            y -= 3 * math.exp(-p["settle"] / 5) * abs(math.sin(p["settle"] * 0.6))
        r = p["r"]
        col = hex_rgb(p["c"])
        d.ellipse((p["x"] - r, y - r, p["x"] + r, y + r), fill=col, outline=(40, 28, 16))
        hr = r * 0.3
        d.ellipse(
            (p["x"] - r * 0.3 - hr, y - r * 0.3 - hr, p["x"] - r * 0.3 + hr, y - r * 0.3 + hr),
            fill=(255, 248, 236),
        )
    d.line(
        [(CX - R_TOP, RIM_Y), (CX - R_BOT, FLOOR_Y), (CX + R_BOT, FLOOR_Y), (CX + R_TOP, RIM_Y)],
        fill=hex_rgb("#4a7fb5"),
        width=int(WALL_R * 2),
        joint="curve",
    )
    d.line(
        [(CX - R_TOP - 2, RIM_Y + 2), (CX - R_BOT - 4, FLOOR_Y - 4)],
        fill=(255, 255, 255),
        width=4,
    )
    return img


def falling(pieces):
    return any(p["mode"] == "fall" for p in pieces)


def main():
    slots, full, mound_end = build_slots()
    print("slots", len(slots), "full", full, "mound", mound_end)
    stops_ratio = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.35]
    base = make_background()
    pieces = []
    floor = {-1: [], 1: []}
    next_slot = 0
    spill_n = 0
    frames = []
    stops = []

    def push(im, repeats=1):
        arr = np.asarray(im)
        for _ in range(repeats):
            frames.append(arr)

    empty = paint(base, pieces)
    push(empty, HOLD)
    stops.append({"ratio": 0.0, "ms": 0})

    def spawn_slot():
        nonlocal next_slot
        sl = slots[next_slot]
        next_slot += 1
        new_piece(pieces, sl["x"], sl["y"])

    def spawn_spill():
        nonlocal spill_n
        sg = 1 if spill_n % 2 else -1
        fs = pick_floor(floor[sg], sg)
        if not fs:
            return False
        cap_x = CX + sg * (R_TOP + 21 * 0.77)
        cap_y = RIM_Y - 21 * 0.64
        p = new_piece(pieces, cap_x, cap_y)
        p["spill"] = True
        p["sg"] = sg
        p["fs"] = fs
        spill_n += 1
        return True

    acc = 0.0

    def record_motion(slot_target, spill_target):
        nonlocal acc
        guard = 0
        while (next_slot < slot_target or spill_n < spill_target or falling(pieces)) and guard < 4000:
            for _ in range(LOGIC_PER_FRAME):
                acc += 0.55
                while acc >= 1 and (next_slot < slot_target or spill_n < spill_target):
                    acc -= 1
                    if next_slot < slot_target:
                        spawn_slot()
                    elif spill_n < spill_target:
                        if not spawn_spill():
                            break
                step_physics(pieces)
            push(paint(base, pieces))
            guard += 1

    for ratio in stops_ratio[1:]:
        if ratio <= 1:
            slot_target = int(round(ratio * full))
            spill_target = 0
        else:
            slot_target = mound_end
            spill_target = SPILL_MAX
        record_motion(slot_target, spill_target)
        # дождаться покоя, если ещё летят
        guard = 0
        while falling(pieces) and guard < 400:
            for _ in range(LOGIC_PER_FRAME):
                step_physics(pieces)
            push(paint(base, pieces))
            guard += 1
        settled_at = len(frames)
        push(frames[-1] if frames else np.asarray(empty), HOLD)
        stops.append({"ratio": ratio, "ms": int(round(settled_at * 1000 / FPS))})
        print("stop", ratio, "frame", settled_at, "pieces", len(pieces), "spills", spill_n)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    import imageio.v2 as imageio

    writer = imageio.get_writer(
        str(OUT),
        fps=FPS,
        codec="libx264",
        pixelformat="yuv420p",
        macro_block_size=1,
        ffmpeg_params=["-crf", "20", "-preset", "veryfast"],
    )
    for frame in frames:
        writer.append_data(frame)
    writer.close()
    META.write_text(json.dumps({"fps": FPS, "stops": stops}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT, "frames", len(frames), "sec", round(len(frames) / FPS, 1))


if __name__ == "__main__":
    main()
