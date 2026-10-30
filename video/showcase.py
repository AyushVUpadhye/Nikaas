"""
Nikaas showcase film — ~25 s, 2880×1576 (1440×788 @ 2× device scale).

Sequence (≤26 s, no voice, no speed-up):
  0s  Home hero — hold on the exit-sign headline
  4s  Smooth scroll down through "how it works" and measured numbers
 10s  Open Twin page — building animates in
 13s  Tap "West steps" exit — fire rings appear, re-plan runs
 17s  Switch to "Nikaas plan" — faster time shows
 20s  Navigate to Evidence page
 23s  Navigate back to Home
 26s  Cut

Output:
  video/tmp_raw.webm   — raw Playwright capture
  video/nikaas_showcase.mp4 — final film with gradient frame (requires ffmpeg)

Usage:
  pip install playwright
  playwright install chromium
  python video/showcase.py
  # or with ffmpeg framing:
  python video/showcase.py --frame

Run from the repo root. The dev server must be live at http://localhost:5173.
"""
from __future__ import annotations
import argparse
import pathlib
import subprocess
import time

BASE_URL = "http://localhost:5173"
VIDEO_DIR = pathlib.Path(__file__).parent
RAW = VIDEO_DIR / "tmp_raw.webm"
OUT = VIDEO_DIR / "nikaas_showcase.mp4"
GRADIENT_PNG = VIDEO_DIR / "gradient_bg.png"

# Viewport and device scale
W, H = 1440, 788
DPR = 2


def _make_gradient(path: pathlib.Path) -> None:
    """Create a pink-orange-to-blue gradient desktop wallpaper via ffmpeg."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"gradients=size={W*DPR + 120}x{H*DPR + 120}:c0=0xf97316:c1=0x3b82f6:x0=0:x1=1:y0=0:y1=1",
        "-frames:v", "1", str(path),
    ], check=True)


def _overlay_on_gradient(raw: pathlib.Path, out: pathlib.Path) -> None:
    """Composite the browser recording centred on a gradient with rounded corners.

    Uses ffmpeg geq + rounded-rect mask approach.
    """
    bg = str(GRADIENT_PNG)
    rw, rh = W * DPR, H * DPR
    cx = 60  # horizontal margin
    cy = 60  # vertical margin
    total_w = rw + 2 * cx
    total_h = rh + 2 * cy
    r = 24  # corner radius in output pixels

    # scale raw to exact pixel dimensions then round-mask and overlay on gradient
    subprocess.run([
        "ffmpeg", "-y",
        "-i", bg,
        "-i", str(raw),
        "-filter_complex",
        (
            f"[1:v]scale={rw}:{rh},"
            # rounded-corner alpha mask via geq
            f"format=yuva420p,"
            f"geq='lum(X,Y)':a='if(gt(min(min(X,{rw}-X),min(Y,{rh}-Y)),{r}),255,"
            f"if(lt(hypot(X-{r},{r}-Y),{r})*lt(X,{r})*gt(Y,0),255*lt(hypot(X-{r},{r}-Y),{r}),"
            f"if(lt(hypot({rw}-{r}-X,{r}-Y),{r})*gt(X,{rw}-{r})*gt(Y,0),255*lt(hypot({rw}-{r}-X,{r}-Y),{r}),"
            f"if(lt(hypot(X-{r},{rh}-{r}-Y),{r})*lt(X,{r})*gt(Y,{rh}-{r}),255*lt(hypot(X-{r},{rh}-{r}-Y),{r}),"
            f"if(lt(hypot({rw}-{r}-X,{rh}-{r}-Y),{r})*gt(X,{rw}-{r})*gt(Y,{rh}-{r}),255*lt(hypot({rw}-{r}-X,{rh}-{r}-Y),{r}),0)))))'[browser];"
            f"[0:v]scale={total_w}:{total_h}[bg];"
            f"[bg][browser]overlay={cx}:{cy}:shortest=1"
        ),
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-r", "30",
        str(out),
    ], check=True)


def record() -> None:
    from playwright.sync_api import sync_playwright

    RAW.parent.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=DPR,
            record_video_dir=str(RAW.parent),
            record_video_size={"width": W, "height": H},
        )
        page = ctx.new_page()

        # ── Home hero ─────────────────────────────────────────────────────────
        page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        time.sleep(2.0)   # hold on hero

        # ── Scroll through "how it works" and stats ───────────────────────────
        for _ in range(30):
            page.mouse.wheel(0, 120)
            time.sleep(0.18)

        time.sleep(1.0)

        # ── Open Twin page ────────────────────────────────────────────────────
        page.goto(f"{BASE_URL}/#twin", wait_until="networkidle", timeout=20_000)
        time.sleep(2.5)   # let 3D settle

        # Tap "West steps" exit
        west = page.locator("text=West steps").first
        if west.count():
            west.click()
            time.sleep(2.0)   # fire rings + re-plan animation
        else:
            # fallback: look for any exit button
            exits = page.locator("[data-exit]")
            if exits.count():
                exits.first.click()
                time.sleep(2.0)

        # Switch to Nikaas plan
        nikaas_btn = page.locator("text=Nikaas plan").first
        if nikaas_btn.count():
            nikaas_btn.click()
            time.sleep(1.5)

        # ── Evidence page ─────────────────────────────────────────────────────
        page.goto(f"{BASE_URL}/#evidence", wait_until="networkidle", timeout=20_000)
        time.sleep(2.0)

        # ── Back to Home ──────────────────────────────────────────────────────
        page.goto(BASE_URL, wait_until="networkidle", timeout=20_000)
        time.sleep(1.5)

        ctx.close()
        browser.close()

    # Playwright names the video file automatically; rename it
    videos = sorted(RAW.parent.glob("*.webm"))
    if videos:
        videos[-1].rename(RAW)
        print(f"Raw video saved: {RAW}")
    else:
        print("Warning: no .webm found in output dir")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", action="store_true", help="add gradient frame via ffmpeg")
    ap.add_argument("--frame-only", action="store_true", help="skip recording, only add frame to existing tmp_raw.webm")
    args = ap.parse_args()

    if not args.frame_only:
        record()

    if args.frame or args.frame_only:
        if not GRADIENT_PNG.exists():
            _make_gradient(GRADIENT_PNG)
        _overlay_on_gradient(RAW, OUT)
        print(f"Film saved: {OUT}")
    else:
        # simple re-encode without frame for quick check
        subprocess.run([
            "ffmpeg", "-y", "-i", str(RAW),
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            str(OUT),
        ], check=True)
        print(f"Film saved (no frame): {OUT}")


if __name__ == "__main__":
    main()
