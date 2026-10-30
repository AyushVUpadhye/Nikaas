"""Run vision on a floor-plan photo and compare it with the hand-digitised graph of the same photo.
Writes runs/vision_<name>_<model>.json (the graph Bedrock produced) and runs/vision_check.md (the comparison).

    python scripts/vision_check.py                                   # IIT KGP museum panel, default model
    python scripts/vision_check.py --models us.amazon.nova-pro-v1:0 us.amazon.nova-lite-v1:0
"""
import argparse
import difflib
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nikaas.building import load, nearest_plan  # noqa: E402
from nikaas.sim import simulate  # noqa: E402
from nikaas.vision import MODEL_ID, read_map  # noqa: E402

RUNS = ROOT / "runs"


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split()


def match_rooms(truth, got):
    """Greedy best-first match of rooms by printed label (falls back to id). Returns [(truth_node, got_node, score)]."""
    t_rooms = [n for n in truth["nodes"] if n["type"] == "room"]
    g_rooms = [n for n in got["nodes"] if n.get("type") == "room"]
    pairs = []
    for t in t_rooms:
        for g in g_rooms:
            a = " ".join(norm(t.get("label") or t["id"]))
            b = " ".join(norm(g.get("label") or g.get("id")))
            score = difflib.SequenceMatcher(None, a, b).ratio()
            if set(a.split()) & set(b.split()) - {"and", "of", "in", "the", "room", "gallery", "hall"}:
                score = max(score, 0.6)
            pairs.append((score, t["id"], g["id"]))
    used_t, used_g, out = set(), set(), []
    byid_t = {n["id"]: n for n in t_rooms}
    byid_g = {n["id"]: n for n in g_rooms}
    for score, ti, gi in sorted(pairs, reverse=True):
        if score < 0.5 or ti in used_t or gi in used_g:
            continue
        used_t.add(ti)
        used_g.add(gi)
        out.append((byid_t[ti], byid_g[gi], score))
    missed = [n for n in t_rooms if n["id"] not in used_t]
    extra = [n for n in g_rooms if n["id"] not in used_g]
    return out, missed, extra


def run_sim(d):
    try:
        b = load(d)
        out = simulate(b, nearest_plan(b))
        return out, None
    except Exception as e:  # report, don't crash the whole check
        return None, f"{type(e).__name__}: {e}"


def count(d, kind):
    return sum(1 for n in d["nodes"] if n.get("type") == kind)


EXIT_RADIUS_M = 8.0


def exits_found(truth, got):
    """Hand exits with a vision exit within EXIT_RADIUS_M; vision exits with no hand exit that close."""
    th = [n for n in truth["nodes"] if n["type"] == "exit"]
    gv = [n for n in got["nodes"] if n.get("type") == "exit"]
    near = lambda a, b: math.hypot(a["x"] - b["x"], a["z"] - b["z"]) <= EXIT_RADIUS_M
    return [t for t in th if any(near(t, g) for g in gv)], [g for g in gv if not any(near(t, g) for t in th)]


def section(truth, got, probs, model, secs):
    pairs, missed, extra = match_rooms(truth, got)
    ex_ok, ex_far = exits_found(truth, got)
    errs = [math.hypot(t["x"] - g["x"], t["z"] - g["z"]) for t, g, _ in pairs]
    sim_t, err_t = run_sim(truth)
    sim_g, err_g = run_sim(got) if not probs else (None, "graph invalid, not simulated")
    people_t = sum(n.get("people", 0) for n in truth["nodes"] if n["type"] == "room")
    people_g = sum(n.get("people", 0) for n in got["nodes"] if n.get("type") == "room")
    v = got.get("vision", {})
    u = v.get("usage", {})
    L = [f"## {model}", "",
         f"Took {secs:.0f} s, {v.get('calls')} model call(s), exits added by the exits pass: {v.get('exits_added') or 'none'}, {len(v.get('auto_links', []))} link(s) added by `connect`, {u.get('inputTokens')} input + {u.get('outputTokens')} output tokens.", "",
         "| | Hand-digitised | Vision |", "|---|---|---|",
         f"| Rooms | {count(truth, 'room')} | {count(got, 'room')} |",
         f"| Exits | {count(truth, 'exit')} | {count(got, 'exit')} ({len(ex_ok)} within {EXIT_RADIUS_M:g} m of a hand exit) |",
         f"| Corridor points | {count(truth, 'corridor')} | {count(got, 'corridor')} |",
         f"| Edges | {len(truth['edges'])} | {len(got['edges'])} |",
         f"| People | {people_t} | {people_g} |",
         f"| Valid (`building.validate`) | yes | {'yes' if not probs else 'no'} |",
         f"| Evacuation time, nearest exit (s) | {sim_t['total_time_s'] if sim_t else err_t} | {sim_g['total_time_s'] if sim_g else err_g} |",
         f"| People per exit | {sim_t['per_exit'] if sim_t else '-'} | {sim_g['per_exit'] if sim_g else '-'} |",
         "",
         f"**Rooms found:** {len(pairs)} of {count(truth, 'room')} "
         f"({100 * len(pairs) / max(1, count(truth, 'room')):.0f}%). "
         + (f"Median position error {sorted(errs)[len(errs) // 2]:.1f} m, worst {max(errs):.1f} m." if errs else ""),
         ""]
    if probs:
        L += ["**Validation problems:**", ""] + [f"- {p}" for p in probs] + [""]
    L += ["| Hand room | Vision room | Position error (m) | People hand / vision |", "|---|---|---|---|"]
    for (t, g, _), e in sorted(zip(pairs, errs), key=lambda p: -p[1]):
        L.append(f"| {t.get('label', t['id'])} | {g.get('label', g['id'])} | {e:.1f} | {t.get('people', 0)} / {g.get('people', 0)} |")
    L.append("")
    if missed:
        L.append("**Missed by vision:** " + ", ".join(n.get("label", n["id"]) for n in missed))
    if extra:
        L.append("**Extra in vision (not in hand graph):** " + ", ".join(n.get("label", n["id"]) for n in extra))
    L += ["", "**Exits** hand: " + ", ".join(n.get("label", n["id"]) for n in truth["nodes"] if n["type"] == "exit")
          + "  |  vision: " + ", ".join(n.get("label", n["id"]) for n in got["nodes"] if n.get("type") == "exit"),
          "", f"**Hand exits found (vision exit within {EXIT_RADIUS_M:g} m):** "
          + (", ".join(n["label"] for n in ex_ok) or "none")
          + f". Vision exits not near any hand exit: {len(ex_far)}.", ""]
    summary = (model, f"{len(pairs)}/{count(truth, 'room')}", f"{len(ex_ok)}/{count(truth, 'exit')} ({count(got, 'exit')} placed)", "yes" if not probs else "no",
               f"{sorted(errs)[len(errs) // 2]:.1f}" if errs else "-",
               sim_g["total_time_s"] if sim_g else "-", sim_t["total_time_s"] if sim_t else "-")
    return L, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", default="data/maps/iit_kgp_nmst_block_b.jpg")
    ap.add_argument("--truth", default="data/iit_kgp_museum.json")
    ap.add_argument("--width", type=float, default=81.0, help="building east-west length in metres")
    ap.add_argument("--models", nargs="+", default=[MODEL_ID])
    a = ap.parse_args()

    photo, truth_path = ROOT / a.photo, ROOT / a.truth
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    img = photo.read_bytes()
    fmt = {"jpg": "jpeg"}.get(photo.suffix[1:].lower(), photo.suffix[1:].lower())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()

    body, rows = [], []
    for model in a.models:
        t0 = time.time()
        got, probs = read_map(img, fmt, width_m=a.width, name=f"{truth_path.stem} (vision, {model})", model_id=model)
        secs = time.time() - t0
        short = re.sub(r"[^a-z0-9]+", "-", model.split(".", 1)[-1].lower()).strip("-")
        out = RUNS / f"vision_{truth_path.stem}_{short}.json"
        out.write_text(json.dumps(got, indent=1), encoding="utf-8")
        L, s = section(truth, got, probs, model, secs)
        body += L + [f"Graph saved to `{out.relative_to(ROOT).as_posix()}`.", ""]
        rows.append(s)
        print(f"{model}: rooms {s[1]}, exits found {s[2]}, valid {s[3]}, median error {s[4]} m, time {s[5]} s (hand {s[6]} s)")

    md = ["# Vision check (generated by `scripts/vision_check.py`; do not edit by hand)", "",
          f"Photo `{a.photo}` read by Amazon Bedrock, compared with the hand-digitised `{a.truth}` of the same photo.",
          f"Building width assumed {a.width:g} m (the panel has no scale bar). Commit {commit}.", "",
          "| Model | Rooms found | Exits found (within 8 m) | Valid | Median position error (m) | Evac time vision (s) | Evac time hand (s) |",
          "|---|---|---|---|---|---|---|"]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md += ["", "How to read this:",
           "- Rooms are matched to the hand graph by printed name. Position error = distance between room centres.",
           "- People come from room area x use (`DENSITY` in `nikaas/vision.py`), not from the model.",
           "- Links the model left out are added by `connect` (nearest walkway point) and listed in the graph's",
           "  `vision.auto_links`, so a person can check them in the editor.",
           "- Exits in the hand graph are also estimates from the panel. Fewer exits means everyone queues at one",
           "  door, which is most of the evacuation-time gap. Confirm exits in the editor before trusting a time.",
           "- Model output varies a little between runs; rerun the script to see the spread.", ""] + body
    (RUNS / "vision_check.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote runs/vision_check.md")


if __name__ == "__main__":
    main()
