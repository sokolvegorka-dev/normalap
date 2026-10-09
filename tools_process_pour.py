# -*- coding: utf-8 -*-
"""Обрезать свободный ролик сыпи: миска, белый фон, без банки, без квадратов."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
SRC_VID = ROOT / "assets" / "bowl" / "srcvid" / "pour1.mp4"
WORK = ROOT / "assets" / "bowl" / "srcvid" / "work"
OUT = ROOT / "assets" / "bowl" / "built"
FFMPEG = r"C:\Users\Egor\AppData\Local\Programs\Python\Python312\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

# экран приложения
SCENE_W, SCENE_H = 308, 270
# ролик и стоп-кадры в 2×, чтобы не было квадратов сжатия
ASSET_W, ASSET_H = 616, 540

# геометрия на кадре 1920×1012 (масштаб подставится сам)
REF_W, REF_H = 1920, 1012
BOWL_CX, BOWL_CY = 1109.0, 763.0
BOWL_RX, BOWL_RY = 600.0, 300.0
OPEN_CX, OPEN_CY = 1072.0, 690.0
OPEN_RX, OPEN_RY = 430.0, 210.0
RIM_Y = 510.0
STREAM_CX, STREAM_CY = 1180.0, 600.0
STREAM_RX, STREAM_RY = 130.0, 95.0
CROP = (490, 455, 1830, 1012)


def ellipse_mask(h, w, cx, cy, rx, ry):
    yy, xx = np.ogrid[:h, :w]
    return ((xx - cx) / max(rx, 1.0)) ** 2 + ((yy - cy) / max(ry, 1.0)) ** 2 <= 1.0


def is_kibble(rgb):
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    return (
        (r > 55) & (r < 230)
        & (g > 22) & (g < 190)
        & (b < 125)
        & (r > g)
        & (g >= b - 10)
        & ((r - b) > 28)
        & ((r - g) < 105)
    )


def is_intruder(rgb, yy, xx, rim_y, w):
    """Банка, рука, этикетка — без прямоугольных вырезов."""
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    purple = (b > g + 10) & (b > 52) & (r < 175)
    green_lbl = (g > r + 6) & (g > 38) & (yy < rim_y + 90) & (xx > w * 0.48)
    skin = (
        (r > 72) & (g > 42) & (b > 32)
        & (r > g) & ((r - b) < 95)
        & (yy < rim_y + 40) & (xx > w * 0.50)
        & ~is_kibble(rgb)
    )
    dark_jar = (r < 70) & (g < 60) & (b < 85) & (yy < rim_y + 70) & (xx > w * 0.52)
    return purple | green_lbl | skin | dark_jar


def _morph_dilate(mask, k=3):
    if k % 2 == 0:
        k += 1
    im = Image.fromarray(mask.astype(np.uint8) * 255)
    return np.array(im.filter(ImageFilter.MaxFilter(k))) > 127


def scaled(v, axis, w, h):
    return v * (w / REF_W if axis == "x" else h / REF_H)


_EMPTY = None
_BOWL = None
_OPEN = None
_STREAM = None
_YY = None
_XX = None
_RIM = 0
_W = 0
_H = 0


def setup_masks(empty):
    global _EMPTY, _BOWL, _OPEN, _STREAM, _YY, _XX, _RIM, _W, _H
    _EMPTY = empty
    _H, _W = empty.shape[:2]
    _YY, _XX = np.ogrid[:_H, :_W]
    _RIM = scaled(RIM_Y, "y", _W, _H)
    _BOWL = ellipse_mask(
        _H, _W,
        scaled(BOWL_CX, "x", _W, _H),
        scaled(BOWL_CY, "y", _W, _H),
        scaled(BOWL_RX, "x", _W, _H),
        scaled(BOWL_RY, "y", _W, _H),
    )
    _OPEN = ellipse_mask(
        _H, _W,
        scaled(OPEN_CX, "x", _W, _H),
        scaled(OPEN_CY, "y", _W, _H),
        scaled(OPEN_RX, "x", _W, _H),
        scaled(OPEN_RY, "y", _W, _H),
    )
    _STREAM = ellipse_mask(
        _H, _W,
        scaled(STREAM_CX, "x", _W, _H),
        scaled(STREAM_CY, "y", _W, _H),
        scaled(STREAM_RX, "x", _W, _H),
        scaled(STREAM_RY, "y", _W, _H),
    )


def process_frame(rgb):
    kib = is_kibble(rgb)
    bad = is_intruder(rgb, _YY, _XX, _RIM, _W)
    diff = np.abs(rgb.astype(np.int16) - _EMPTY.astype(np.int16)).sum(axis=2)
    changed = diff > 42
    has_jar = int(bad.sum()) > 400
    jar_zone = has_jar & (_XX > _W * 0.58) & (_YY < _RIM + 70)
    in_bowl = _OPEN & kib & changed & ~bad & ~jar_zone
    falling = _STREAM & kib & ~bad & (_YY > _RIM - 40) & (_YY < _RIM + 85)
    keep = in_bowl | falling
    dilated = _morph_dilate(in_bowl, 3)
    keep = keep | (dilated & kib & _OPEN & ~bad & ~jar_zone)
    out = np.full_like(rgb, 255)
    out[_BOWL] = _EMPTY[_BOWL]
    out[keep] = rgb[keep]
    return out


def crop_pad(rgb):
    h, w = rgb.shape[:2]
    x0 = int(round(scaled(CROP[0], "x", w, h)))
    y0 = int(round(scaled(CROP[1], "y", w, h)))
    x1 = int(round(scaled(CROP[2], "x", w, h)))
    y1 = int(round(scaled(CROP[3], "y", w, h)))
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    crop = rgb[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    target_h = int(round(cw * ASSET_H / ASSET_W))
    canvas = np.full((target_h, cw, 3), 255, dtype=np.uint8)
    canvas[target_h - ch :, :] = crop
    img = Image.fromarray(canvas).resize((ASSET_W, ASSET_H), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=70, threshold=4))
    return np.array(img)


def run_ff(args):
    subprocess.check_call([FFMPEG, "-y", *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def extract_raw(frames_dir: Path):
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    run_ff([
        "-i", str(SRC_VID),
        "-vf", "scale=1920:-2:flags=lanczos,fps=25",
        "-q:v", "2",
        str(frames_dir / "f%04d.jpg"),
    ])


def main(preview_only=False):
    WORK.mkdir(parents=True, exist_ok=True)
    frames_dir = WORK / "raw"
    inspect = ROOT / "assets" / "bowl" / "srcvid" / "inspect"
    if preview_only:
        raw = sorted(inspect.glob("f*.png"))
    else:
        need = not any(frames_dir.glob("f*.jpg"))
        if need:
            extract_raw(frames_dir)
        raw = sorted(frames_dir.glob("f*.jpg"))
        if not raw:
            raw = sorted(frames_dir.glob("f*.png"))
    print("raw frames", len(raw))
    setup_masks(np.array(Image.open(raw[0]).convert("RGB")))
    Image.fromarray((_BOWL.astype(np.uint8) * 255)).save(WORK / "mask.png")
    print("bowl mask px", int(_BOWL.sum()), "size", _W, _H)

    proc_dir = WORK / "proc"
    if proc_dir.exists() and not preview_only:
        shutil.rmtree(proc_dir)
    proc_dir.mkdir(parents=True, exist_ok=True)

    stills = {}
    for i, path in enumerate(raw):
        rgb = np.array(Image.open(path).convert("RGB"))
        done = crop_pad(process_frame(rgb))
        out_name = proc_dir / (f"p{i:04d}.png" if not preview_only else f"prev_{path.stem}.png")
        Image.fromarray(done).save(out_name)
        fill = float(is_kibble(done).mean())
        stills[i] = fill
        if preview_only or i in (0, 80, 140, 180, 220, 260, 300) or i == len(raw) - 1:
            Image.fromarray(done).save(WORK / f"prev_{i:04d}.jpg", quality=90)
            print("frame", i, path.name, "fill", round(fill, 4))

    if preview_only:
        print("preview only")
        return

    fills = np.array([stills[i] for i in range(len(raw))])
    start = int(np.argmax(fills > fills[0] + 0.018))
    # короче активная сыпь, чтобы можно было насыпать несколько раз подряд
    peak = int(np.argmax(fills))
    end = min(len(raw) - 1, max(start + 70, min(peak, start + 110)))
    if start < 20:
        start = 90
        end = min(len(raw) - 1, 200)
    print("pour span", start, end, "n", end - start + 1, "sec", round((end - start + 1) / 25.0, 2))

    pour_dir = WORK / "pour"
    if pour_dir.exists():
        shutil.rmtree(pour_dir)
    pour_dir.mkdir(parents=True, exist_ok=True)
    for j, i in enumerate(range(start, end + 1)):
        (pour_dir / f"q{j:04d}.png").write_bytes((proc_dir / f"p{i:04d}.png").read_bytes())

    OUT.mkdir(parents=True, exist_ok=True)
    mp4 = OUT / "pour.mp4"
    run_ff([
        "-framerate", "25",
        "-i", str(pour_dir / "q%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "slow", "-crf", "16",
        "-movflags", "+faststart",
        str(mp4),
    ])
    print("mp4", mp4, mp4.stat().st_size)

    empty_i = 0
    full_i = min(len(raw) - 1, max(peak, len(raw) - 20))
    # полный кадр без банки — ближе к концу ролика
    full_i = min(len(raw) - 1, 300) if len(raw) > 300 else len(raw) - 1
    mid_i = min(len(raw) - 1, start + (end - start) // 2)
    Image.open(proc_dir / f"p{empty_i:04d}.png").save(OUT / "bowl.png")
    Image.open(proc_dir / f"p{full_i:04d}.png").save(OUT / "bowl_full.png")
    Image.open(proc_dir / f"p{mid_i:04d}.png").save(OUT / "bowl_mid.png")
    meta = {
        "scene": [SCENE_W, SCENE_H],
        "asset": [ASSET_W, ASSET_H],
        "well": {
            "cx": SCENE_W / 2,
            "cy": SCENE_H * 0.62,
            "rx": SCENE_W * 0.38,
            "ry": SCENE_H * 0.22,
        },
        "n_pieces": 0,
        "spills": [],
        "pour_start": start,
        "pour_end": end,
        "empty": empty_i,
        "mid": mid_i,
        "full": full_i,
        "pour_seconds": round((end - start + 1) / 25.0, 1),
    }
    (OUT / "well.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("stills", empty_i, mid_i, full_i, "ok")


if __name__ == "__main__":
    import sys
    main(preview_only="--preview" in sys.argv)
