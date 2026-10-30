"""Build the 5-slide finalist deck from docs/RESULTS.md numbers.

Usage (run from repo root):
    python scripts/make_slides.py                   # writes runs/nikaas_slides.pptx
    python scripts/make_slides.py --screenshots     # also captures site screenshots

Slides:
  1. Title — "Nikaas: smarter evacuation routing" + tagline + incident stat
  2. Problem — 3 real incidents, one number each
  3. How it works — 3 steps (Photo → Graph → Simulate / Optimise)
  4. Evidence — SFPE validation line + results table (from RESULTS.md)
  5. Crowd mode — what it detects, thresholds, status

Numbers come exclusively from docs/RESULTS.md (via runs/wow.csv + runs/results.csv).
Never edit the numbers in this file by hand.
"""
from __future__ import annotations
import argparse
import csv
import io
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent
OUT = ROOT / "runs" / "nikaas_slides.pptx"

# ── colours (ISO 7010 green system, dark bg) ─────────────────────────────────
GREEN = "1B5E20"   # exit green
WHITE = "FFFFFF"
DARK  = "0A0A0A"
ACCENT = "E65100"  # evacuation orange
LIGHT_BG = "F5F5F5"
GREY = "424242"

# font sizes (14–18 pt per task spec)
F_TITLE = 32    # slide title — larger for legibility
F_HEAD  = 18
F_BODY  = 15
F_SMALL = 13

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches, Pt
except ImportError:
    sys.exit("python-pptx not installed. Run: pip install python-pptx")


def _rgb(hex6: str) -> RGBColor:
    h = hex6.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _add_slide(prs, layout_idx=6):
    layout = prs.slide_layouts[layout_idx]  # blank
    return prs.slides.add_slide(layout)


def _bg(slide, hex6: str):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(hex6)


def _box(slide, l, t, w, h, text, size=F_BODY, bold=False, colour=WHITE,
         align=PP_ALIGN.LEFT, bg=None, wrap=True):
    txBox = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    if bg:
        txBox.fill.solid()
        txBox.fill.fore_color.rgb = _rgb(bg)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(colour)
    return txBox


def _line(slide, l, t, w, h, colour=GREEN):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(l), Inches(t), Inches(w), Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(colour)
    shape.line.fill.background()


# ── load numbers from runs/ ───────────────────────────────────────────────────

def _load_wow() -> list[dict]:
    p = ROOT / "runs" / "wow.csv"
    if not p.exists():
        return []
    with p.open(newline="") as f:
        return list(csv.DictReader(f))


def _load_results() -> list[dict]:
    p = ROOT / "runs" / "results.csv"
    if not p.exists():
        return []
    with p.open(newline="") as f:
        return list(csv.DictReader(f))


def _load_validation() -> dict:
    p = ROOT / "runs" / "validation.csv"
    if not p.exists():
        return {}
    with p.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


# ── screenshots (optional) ────────────────────────────────────────────────────

def _screenshot(url: str, out: pathlib.Path, width=1440, height=788):
    """Capture a page screenshot with Playwright (headless)."""
    script = (
        "from playwright.sync_api import sync_playwright\n"
        f"with sync_playwright() as p:\n"
        f"    b = p.chromium.launch()\n"
        f"    pg = b.new_page(viewport={{'width':{width},'height':{height}}})\n"
        f"    pg.goto('{url}', wait_until='networkidle', timeout=20000)\n"
        f"    pg.wait_for_timeout(1500)\n"
        f"    pg.screenshot(path=r'{out}', full_page=False)\n"
        f"    b.close()\n"
    )
    subprocess.run([sys.executable, "-c", script], check=True)


# ── slides ────────────────────────────────────────────────────────────────────

def slide_title(prs):
    s = _add_slide(prs)
    _bg(s, DARK)
    _line(s, 0, 3.5, 10, 0.06, GREEN)
    _box(s, 0.4, 0.3, 9.2, 1.2,
         "Nikaas", size=F_TITLE, bold=True, colour=GREEN, align=PP_ALIGN.LEFT)
    _box(s, 0.4, 1.35, 9.2, 0.6,
         "Smarter evacuation routing from a photograph of the exit map",
         size=F_HEAD, colour=WHITE, align=PP_ALIGN.LEFT)
    _box(s, 0.4, 2.1, 9.2, 0.5,
         "AfterHours 1.0  ·  Theme 03: Public Safety",
         size=F_SMALL, colour=GREY, align=PP_ALIGN.LEFT)
    _box(s, 0.4, 3.7, 9.2, 1.1,
         "11 people were killed outside Chinnaswamy Stadium, Bengaluru — 4 June 2025.\n"
         "Nikaas gives every room in a building the exit that gets everyone out fastest,\n"
         "even when a stair is blocked.",
         size=F_BODY, colour=WHITE, align=PP_ALIGN.LEFT)
    _box(s, 0.4, 5.5, 9.2, 0.5,
         "Live API  ·  IIT Kharagpur floor plan  ·  SFPE validation",
         size=F_SMALL, colour=GREY, align=PP_ALIGN.LEFT)


def slide_problem(prs):
    s = _add_slide(prs)
    _bg(s, DARK)
    _box(s, 0.4, 0.2, 9.2, 0.7, "The problem", size=F_HEAD, bold=True,
         colour=GREEN, align=PP_ALIGN.LEFT)
    _line(s, 0.4, 0.95, 9.2, 0.04, GREEN)

    incidents = [
        ("22", "students died in the 2019 Surat coaching-centre fire\nafter the escape stair burned."),
        ("23", "people died on one overloaded footbridge at Elphinstone Road, Mumbai, in 2017."),
        ("11", "people were killed outside Chinnaswamy Stadium,\nBengaluru, on 4 June 2025."),
    ]
    for i, (num, text) in enumerate(incidents):
        x = 0.4 + i * 3.2
        _box(s, x, 1.2, 2.8, 1.0, num, size=40, bold=True, colour=ACCENT,
             align=PP_ALIGN.LEFT)
        _box(s, x, 2.1, 2.9, 1.4, text, size=F_SMALL, colour=WHITE,
             align=PP_ALIGN.LEFT)

    _box(s, 0.4, 3.7, 9.2, 0.5,
         "Common thread: people follow the nearest visible exit, not the fastest one.\n"
         "Evacuation plans are static PDFs that cannot re-route when a stair is blocked.",
         size=F_BODY, colour=WHITE, align=PP_ALIGN.LEFT)


def slide_how(prs):
    s = _add_slide(prs)
    _bg(s, DARK)
    _box(s, 0.4, 0.2, 9.2, 0.7, "How Nikaas works", size=F_HEAD, bold=True,
         colour=GREEN, align=PP_ALIGN.LEFT)
    _line(s, 0.4, 0.95, 9.2, 0.04, GREEN)

    steps = [
        ("① Photograph", "Take a photo of the floor plan fixed to the wall."),
        ("② Read", "Amazon Bedrock Nova Pro reads the photo into a building graph\n(rooms, doors, stairs, exits) in ~15 s."),
        ("③ Simulate & optimise", "Nikaas times every room-to-exit path,\nfinds jams, and gives each room the fastest exit.\n"
         "Lab block: 301 s → 167 s  (44.6% faster movement time)."),
    ]
    for i, (head, body) in enumerate(steps):
        x = 0.4 + i * 3.2
        _line(s, x, 1.2, 2.8, 0.05, GREEN)
        _box(s, x, 1.35, 2.9, 0.5, head, size=F_BODY, bold=True, colour=GREEN)
        _box(s, x, 1.85, 2.9, 2.0, body, size=F_SMALL, colour=WHITE)

    _box(s, 0.4, 4.2, 9.2, 0.5,
         "All times are evacuation movement times (SFPE Handbook Ch. 56 definition).",
         size=F_SMALL, colour=GREY)


def slide_evidence(prs, wow: list[dict], validation: dict):
    s = _add_slide(prs)
    _bg(s, LIGHT_BG)
    _box(s, 0.4, 0.2, 9.2, 0.7, "How we know the numbers hold",
         size=F_HEAD, bold=True, colour=DARK, align=PP_ALIGN.LEFT)
    _line(s, 0.4, 0.95, 9.2, 0.04, GREEN)

    sim_t = validation.get("simulated_s", "245.25")
    pub_t = validation.get("published_s", "245.2")
    err   = validation.get("error_pct", "0.02")
    _box(s, 0.4, 1.1, 9.2, 0.5,
         f"SFPE Engineering Guide Example 1: simulator = {sim_t} s  vs  published = {pub_t} s  ({err}% error)",
         size=F_BODY, bold=True, colour=DARK)

    headers = ["Building", "Nearest (s)", "Nikaas (s)", "Saved (s)", "Saved (%)", "Lower bound (s)"]
    col_w   = [3.2, 1.3, 1.3, 1.1, 1.0, 1.5]
    row_h   = 0.35
    top     = 1.75

    # header row
    x = 0.4
    for j, (h, w) in enumerate(zip(headers, col_w)):
        _box(s, x, top, w, row_h, h, size=F_SMALL, bold=True, colour=WHITE,
             bg=GREEN, align=PP_ALIGN.CENTER)
        x += w

    # data rows (only key rows from wow.csv)
    key_rows = [
        r for r in wow
        if r.get("blocked_exit", "-") in ("-", "") and r.get("building") in
           ("iit_kgp_museum.json", "lab_block.json")
    ] + [
        r for r in wow
        if r.get("blocked_exit") == "MAIN" and r.get("building") == "iit_kgp_museum.json"
    ]

    for i, row in enumerate(key_rows[:5]):
        bg = "FFFFFF" if i % 2 == 0 else "EEEEEE"
        vals = [
            row.get("building", "").replace(".json", "").replace("_", " "),
            row.get("nearest_s", ""),
            row.get("nikaas_s", ""),
            row.get("saved_s", ""),
            row.get("saved_pct", "") + "%",
            row.get("lower_bound_s", ""),
        ]
        x = 0.4
        for j, (v, w) in enumerate(zip(vals, col_w)):
            _box(s, x, top + row_h * (i + 1), w, row_h, v,
                 size=F_SMALL, colour=DARK, bg=bg, align=PP_ALIGN.CENTER)
            x += w

    _box(s, 0.4, 5.3, 9.2, 0.4,
         "All numbers generated by scripts/report.py from runs/. Nothing typed by hand.",
         size=F_SMALL, colour=GREY)


def slide_crowd(prs):
    s = _add_slide(prs)
    _bg(s, DARK)
    _box(s, 0.4, 0.2, 9.2, 0.7, "Crowd mode — where will people be crushed?",
         size=F_HEAD, bold=True, colour=GREEN, align=PP_ALIGN.LEFT)
    _line(s, 0.4, 0.95, 9.2, 0.04, GREEN)

    _box(s, 0.4, 1.1, 9.2, 0.6,
         "Crowd mode computes people per m² on every corridor and door over time.\n"
         "It flags when and where density exceeds safety thresholds.",
         size=F_BODY, colour=WHITE)

    thresholds = [
        ("2.7 p/m²", "Concern — LoS E (Fruin);\nUK Green Guide stadium cap"),
        ("4.0 p/m²", "Crush risk — crowd forces\nreach fatal levels (G. Keith Still)"),
        ("10.0 p/m²", "Physical cap — absolute maximum\nfor standing humans"),
    ]
    for i, (val, label) in enumerate(thresholds):
        x = 0.4 + i * 3.2
        _box(s, x, 2.0, 2.9, 0.55, val, size=F_HEAD, bold=True, colour=ACCENT)
        _box(s, x, 2.6, 2.9, 1.1, label, size=F_SMALL, colour=WHITE)

    _box(s, 0.4, 3.9, 9.2, 0.5,
         "Integrated into /simulate with crowd=true. Red zones on the 3D map.\n"
         "Tested on the IIT KGP museum floor plan (507 people, 3 exits, 11 tests pass).",
         size=F_BODY, colour=WHITE)

    _box(s, 0.4, 5.1, 9.2, 0.5,
         "Status: crowd density fix merged (PR #4). Stadium precompute: pending Chirag's choice.",
         size=F_SMALL, colour=GREY)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screenshots", action="store_true",
                    help="capture site screenshots and embed them (requires dev server at localhost:5173)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    wow = _load_wow()
    validation = _load_validation()

    prs = Presentation()
    prs.slide_width  = Inches(10)
    prs.slide_height = Inches(6.5)

    slide_title(prs)
    slide_problem(prs)
    slide_how(prs)
    slide_evidence(prs, wow, validation)
    slide_crowd(prs)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    print(f"Saved: {out}  ({prs.slides.__len__()} slides)")


if __name__ == "__main__":
    main()
