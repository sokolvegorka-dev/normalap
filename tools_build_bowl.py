# -*- coding: utf-8 -*-
"""Собрать фото-миску и гранулы из настоящих снимков.

Источники (Wikimedia Commons):
- Empty white bowl.png — Alorin
- Pile of Kibble Dog Food (51049786351).jpg
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "assets" / "bowl"
OUT = SRC / "built"
SCENE_W, SCENE_H = 308, 318
BG = (246, 243, 236, 255)


def crop_alpha(im, pad=4):
    a = im.split()[-1]
    box = a.getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def isolate_white_bg(im, thresh=238):
    im = im.convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if r >= thresh and g >= thresh and b >= thresh:
                px[x, y] = (r, g, b, 0)
    return im


def extract_pieces(pile: Image.Image, n=18):
    im = pile.copy()
    im.thumbnail((1408, 940))
    w, h = im.size
    gray = im.convert("L")
    mask = gray.point(lambda v: 255 if v < 205 else 0).filter(ImageFilter.MedianFilter(3))
    region = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(region)
    d.rectangle((0, 0, int(w * 0.22), h), fill=255)
    d.rectangle((int(w * 0.78), 0, w, h), fill=255)
    d.rectangle((0, int(h * 0.72), w, h), fill=255)
    mask = ImageChops.multiply(mask, region)
    vis = Image.new("L", (w, h), 0)
    vis_px, src = vis.load(), mask.load()
    blobs = []
    for y in range(h):
        for x in range(w):
            if src[x, y] < 128 or vis_px[x, y]:
                continue
            stack = [(x, y)]
            vis_px[x, y] = 255
            xs, ys = [x], [y]
            while stack:
                cx, cy = stack.pop()
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and not vis_px[nx, ny] and src[nx, ny] >= 128:
                        vis_px[nx, ny] = 255
                        stack.append((nx, ny))
                        xs.append(nx)
                        ys.append(ny)
            area = len(xs)
            if 400 < area < 9000:
                blobs.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1, area))
    blobs.sort(key=lambda b: b[4])
    rgba = im.convert("RGBA")
    pieces = []
    for i, (x0, y0, x1, y1, _) in enumerate(blobs):
        pad = 14
        crop = rgba.crop((max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)))
        cut = isolate_white_bg(crop, 220)
        # tighten alpha from brightness
        px = cut.load()
        for yy in range(cut.height):
            for xx in range(cut.width):
                r, g, b, a = px[xx, yy]
                if a and r > 218 and g > 210 and b > 200:
                    px[xx, yy] = (r, g, b, 0)
        cut = crop_alpha(cut, 1)
        if min(cut.size) < 12:
            continue
        side = max(cut.size)
        target = 22 + (i % 5) * 2
        scale = target / side
        cut = cut.resize(
            (max(12, int(cut.width * scale)), max(12, int(cut.height * scale))),
            Image.Resampling.LANCZOS,
        )
        pieces.append(cut)
    extra = []
    for i, p in enumerate(pieces):
        extra.append(p.rotate(28 + i * 22, expand=True, resample=Image.Resampling.BICUBIC))
        extra.append(p.rotate(180 - i * 15, expand=True, resample=Image.Resampling.BICUBIC))
    all_pieces = pieces + extra
    random.seed(3)
    random.shuffle(all_pieces)
    return all_pieces[: max(n, len(all_pieces))]


def bowl_on_scene(bowl: Image.Image):
    # white product bowl: trim outer gray, keep the dish
    w, h = bowl.size
    # crop a centered square a bit inside the frame
    s = int(min(w, h) * 0.92)
    x0 = (w - s) // 2
    y0 = (h - s) // 2
    dish = bowl.crop((x0, y0, x0 + s, y0 + s)).convert("RGBA")
    dish = dish.resize((240, 240), Image.Resampling.LANCZOS)
    s = dish.width
    # fade the outer gray toward cream
    px = dish.load()
    cx, cy = s / 2, s / 2
    r_out = s * 0.49
    for y in range(s):
        for x in range(s):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            r, g, b, a = px[x, y]
            if d > r_out:
                t = min(1.0, (d - r_out) / (s * 0.04 + 1))
                px[x, y] = (
                    int(r * (1 - t) + BG[0] * t),
                    int(g * (1 - t) + BG[1] * t),
                    int(b * (1 - t) + BG[2] * t),
                    255,
                )
    scene = Image.new("RGBA", (SCENE_W, SCENE_H), BG)
    bx = (SCENE_W - dish.width) // 2
    by = 18
    # soft shadow
    sh = Image.new("RGBA", (SCENE_W, SCENE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse((bx + 18, by + dish.height - 28, bx + dish.width - 18, by + dish.height + 10), fill=(80, 70, 55, 40))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    scene.alpha_composite(sh)
    scene.alpha_composite(dish, (bx, by))
    # inner well in scene coords (concentric, inside the rim)
    well = {
        "cx": bx + dish.width / 2,
        "cy": by + dish.height / 2 + 2,
        "rx": dish.width * 0.38,
        "ry": dish.height * 0.36,
    }
    return scene, well, (bx, by, dish.width, dish.height)


def make_heap(pile: Image.Image, well, scene_size, pieces):
    w, h = scene_size
    heap = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # dense crop of the pile
    pw, ph = pile.size
    crop = pile.crop((int(pw * 0.18), int(ph * 0.08), int(pw * 0.86), int(ph * 0.78))).convert("RGBA")
    crop = isolate_white_bg(crop, 236)
    # fit into well ellipse, a bit larger so it fills
    tw = int(well["rx"] * 2.15)
    th = int(well["ry"] * 2.25)
    crop = crop.resize((tw, th), Image.Resampling.LANCZOS)
    hx = int(well["cx"] - tw / 2)
    hy = int(well["cy"] - th / 2 + 4)
    heap.alpha_composite(crop, (hx, hy))
    # elliptical mask
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse(
        (well["cx"] - well["rx"], well["cy"] - well["ry"],
         well["cx"] + well["rx"], well["cy"] + well["ry"]),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    return _and_alpha(heap, mask)


def _and_alpha(im, mask):
    a = im.split()[-1]
    from PIL import ImageChops
    im = im.copy()
    im.putalpha(ImageChops.multiply(a, mask))
    return im


def spills_from_pieces(pieces, well):
    """Positions around the bowl for overflow crumbs."""
    spots = []
    cx, cy, rx, ry = well["cx"], well["cy"], well["rx"], well["ry"]
    ring = [
        (-1.42, 0.15), (-1.38, 0.55), (-1.22, 0.95), (-0.7, 1.12),
        (0.05, 1.16), (0.72, 1.10), (1.28, 0.88), (1.40, 0.42),
        (1.36, 0.05), (-0.95, 1.08),
    ]
    for i, (nx, ny) in enumerate(ring):
        spots.append({
            "x": cx + nx * rx - 12,
            "y": cy + ny * ry - 4,
            "piece": i % max(1, len(pieces)),
            "t": 1.04 + i * 0.03,
        })
    return spots


def main():
    from PIL import ImageChops  # noqa: F401
    OUT.mkdir(parents=True, exist_ok=True)
    bowl_path = SRC / "bowl_white.jpg"
    if not bowl_path.exists():
        bowl_path = SRC / "bowl_white.png"
    bowl = Image.open(bowl_path)
    pile = Image.open(SRC / "kibble_pile.jpg")
    print("extract pieces...")
    pieces = extract_pieces(pile, 20)
    print(" pieces", len(pieces))
    for i, p in enumerate(pieces):
        p.save(OUT / f"piece_{i:02d}.png")
    scene, well, box = bowl_on_scene(bowl)
    scene.save(OUT / "bowl.png")
    print("bowl", box, "well", well)
    heap = make_heap(pile, well, scene.size, pieces)
    heap.save(OUT / "heap.png")
    spills = spills_from_pieces(pieces, well)
    (OUT / "well.json").write_text(
        __import__("json").dumps(
            {"well": well, "scene": [SCENE_W, SCENE_H], "n_pieces": len(pieces), "spills": spills},
            indent=2,
        ),
        encoding="utf-8",
    )
    # previews
    def preview(ratio, name):
        img = scene.copy()
        if ratio > 0:
            # scale heap from center
            s = 0.42 + 0.58 * min(1.0, ratio)
            hw, hh = heap.size
            # crop heap to its bbox then scale — simpler: scale whole layer
            layer = heap.copy()
            nw, nh = int(hw * s), int(hh * s)
            # actually scale around well center via affine
            cx, cy = well["cx"], well["cy"]
            scaled = Image.new("RGBA", (hw, hh), (0, 0, 0, 0))
            small = heap.resize((max(1, int(hw * s)), max(1, int(hh * s))), Image.Resampling.LANCZOS)
            scaled.alpha_composite(small, (int(cx - small.width / 2 + (hw / 2 - cx)), int(cy - small.height / 2 + (hh / 2 - cy))))
            # easier: resize heap then paste centered on well
            small = heap.resize((max(1, int(hw * s)), max(1, int(hh * s))), Image.Resampling.LANCZOS)
            img.alpha_composite(small, (int(cx - small.width / 2), int(cy - small.height / 2)))
        if ratio > 1.02:
            for i, sp in enumerate(spills_from_pieces(pieces, well)):
                if ratio >= sp["t"] and pieces:
                    pc = pieces[sp["piece"]]
                    img.alpha_composite(pc, (int(sp["x"]), int(sp["y"])))
        img.convert("RGB").save(OUT / name, quality=90)
        print("preview", name)

    preview(0, "prev_empty.jpg")
    preview(0.35, "prev_low.jpg")
    preview(0.85, "prev_full.jpg")
    preview(1.2, "prev_over.jpg")
    print("ok", OUT)


if __name__ == "__main__":
    main()
