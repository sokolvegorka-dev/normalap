"""Снимает assets/bowl/pour_src.html кадр за кадром и собирает pour.mp4."""
import asyncio
import base64
import json
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import imageio_ffmpeg
import websockets

ROOT = Path(__file__).resolve().parent
BOWL = ROOT / "assets" / "bowl"
FRAMES = BOWL / "_frames"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PORT = 8769
DBG = 9223
FPS = 30

# Пустая миска, затем четыре шага файла: утро, день, вечер, уже лишнее.
STAGE_RATIOS = [0.05, 0.40, 0.80, 1.01]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BOWL), **kwargs)

    def log_message(self, fmt, *args):
        return


async def cdp(ws, msg_id, method, params=None):
    await ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == msg_id:
            if "error" in msg:
                raise RuntimeError(msg["error"])
            return msg.get("result") or {}


async def ev(ws, msg_id, expression):
    result = await cdp(
        ws,
        msg_id,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )
    if result.get("exceptionDetails"):
        raise RuntimeError(result["exceptionDetails"])
    return (result.get("result") or {}).get("value")


def save_jpg(data_url, path: Path):
    raw = data_url.split(",", 1)[1]
    path.write_bytes(base64.b64decode(raw))


async def record():
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)
    n = 0
    stops = []

    def hold(jpg, frames):
        nonlocal n
        raw = base64.b64decode(jpg.split(",", 1)[1])
        for _ in range(frames):
            (FRAMES / f"f{n:05d}.jpg").write_bytes(raw)
            n += 1

    async with websockets.connect(ws_url, max_size=20_000_000) as ws:
        mid = 1
        ready = None
        for _ in range(40):
            mid += 1
            ready = await ev(ws, mid, "typeof window.__step")
            if ready == "function":
                break
            await asyncio.sleep(0.15)
        if ready != "function":
            raise SystemExit("страница миски не загрузилась")

        async def grab():
            nonlocal mid
            mid += 1
            return await ev(ws, mid, "window.__step(true)")

        def remember(state, copies):
            nonlocal n
            raw = base64.b64decode(state["jpg"].split(",", 1)[1])
            for _ in range(copies):
                (FRAMES / f"f{n:05d}.jpg").write_bytes(raw)
                n += 1

        state = await grab()
        remember(state, 8)
        stops.append({"ratio": 0.0, "ms": int(round((n - 1) * 1000 / FPS))})
        mid += 1
        await ev(ws, mid, "phase = 'pour'; window.__run = true;")
        seen = 0
        guard = 0
        while seen < 4 and guard < 2000:
            state = await grab()
            save_jpg(state["jpg"], FRAMES / f"f{n:05d}.jpg")
            n += 1
            guard += 1
            stage_now = int(state.get("stage") or 0)
            if state.get("done"):
                stops.append({
                    "ratio": STAGE_RATIOS[3],
                    "ms": int(round((n - 1) * 1000 / FPS)),
                })
                seen = 4
                break
            if stage_now > seen:
                stops.append({
                    "ratio": STAGE_RATIOS[seen],
                    "ms": int(round((n - 1) * 1000 / FPS)),
                })
                seen = stage_now
        print("stops", stops, "pieces", state.get("n"), "frames", n)

    meta = {"w": 700, "h": 520, "fps": FPS, "stops": stops, "frames": n}
    (BOWL / "pour.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out = BOWL / "pour.mp4"
    subprocess.run(
        [
            ffmpeg, "-y", "-framerate", str(FPS),
            "-i", str(FRAMES / "f%05d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-movflags", "+faststart",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    shutil.rmtree(FRAMES, ignore_errors=True)
    print("video", out, out.stat().st_size, "frames", n)
    print(json.dumps(stops, ensure_ascii=False))


def main():
    global ws_url
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    profile = BOWL / "_chrome"
    if profile.exists():
        shutil.rmtree(profile, ignore_errors=True)
    profile.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            f"--remote-debugging-port={DBG}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--allow-file-access-from-files",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    info = None
    try:
        url = f"http://127.0.0.1:{PORT}/pour_src.html#cap"
        for _ in range(50):
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{DBG}/json/new?{urllib.parse.quote(url, safe='')}",
                    method="PUT",
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    info = json.loads(resp.read().decode("utf-8"))
                break
            except Exception:
                time.sleep(0.2)
        if not info or "webSocketDebuggerUrl" not in info:
            raise SystemExit(f"chrome debug failed: {info}")
        global_ws = info["webSocketDebuggerUrl"]
        globals()["ws_url"] = global_ws
        asyncio.run(record())
    finally:
        proc.kill()
        httpd.shutdown()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
