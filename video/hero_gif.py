"""Record the Home hero (already evacuating, then a fire at the main entrance) as the README GIF.

Usage, from the repo root with the website running (cd web; npm run dev):
  python video/hero_gif.py --url http://localhost:5175
Writes docs/img/hero.gif. Needs Playwright (playwright install chromium) and ffmpeg.
"""
import argparse
import pathlib
import shutil
import subprocess
import tempfile
import time

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://localhost:5173")
ap.add_argument("--seconds", type=float, default=11)
a = ap.parse_args()

out = pathlib.Path("docs/img/hero.gif")
out.parent.mkdir(parents=True, exist_ok=True)
tmp = pathlib.Path(tempfile.mkdtemp())
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"])  # GPU WebGL (Windows)
    ctx = b.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=str(tmp),
                        record_video_size={"width": 1280, "height": 720})
    t0 = time.monotonic()
    page = ctx.new_page()
    page.goto(f"{a.url}/?fire=MAIN")
    # start the GIF when people are on screen (software WebGL loads slowly)
    page.wait_for_function("document.querySelector('.lh-live')?.textContent.includes('of 5')", timeout=120000)
    start = time.monotonic() - t0
    page.wait_for_timeout(int(a.seconds * 1000))
    raw = page.video.path()
    ctx.close()
    b.close()
# from the moment people appear; 10 fps, 720 px wide, one shared palette keeps the GIF small
vf = f"trim=start={start:.2f},setpts=PTS-STARTPTS,fps=10,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", vf, str(out)], check=True)
shutil.rmtree(tmp, ignore_errors=True)
print(out, round(out.stat().st_size / 1e6, 2), "MB")
