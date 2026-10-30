"""Measure the Wow Number: Nearest Exit vs Nikaas Optimised vs Theoretical Lower Bound.
Outputs verifiable metrics to runs/wow.csv.
"""
import csv
import datetime
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nikaas.building import load, nearest_plan
from nikaas.optimise import lower_bound, optimise
from nikaas.sim import simulate


def run_benchmark(src_path: Path, blocked=()):
    b = load(src_path)
    blocked_tuple = tuple(sorted(blocked))
    blocked_str = "+".join(blocked_tuple) if blocked_tuple else "-"

    # Nearest plan simulation
    near_plan = nearest_plan(b, blocked_tuple)
    near_sim = simulate(b, near_plan, blocked_tuple, frame_every=1e9)
    near_time = near_sim["total_time_s"]
    near_bottleneck = near_sim["bottleneck"]

    # Optimised plan
    opt_res = optimise(b, blocked_tuple)
    opt_time = opt_res["total_time_s"]
    opt_plan = opt_res["plan"]
    lb = opt_res["lower_bound_s"]

    # Re-simulate optimized plan to extract full metrics
    opt_sim = simulate(b, opt_plan, blocked_tuple, frame_every=1e9)
    opt_bottleneck = opt_sim["bottleneck"]

    saved_s = round(near_time - opt_time, 2)
    pct_saved = round((saved_s / near_time) * 100.0, 1)
    gap_bound = round(opt_time - lb, 2)

    sha256 = hashlib.sha256(src_path.read_bytes()).hexdigest()[:12]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "uncommitted"

    row = {
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "building": src_path.name,
        "sha256": sha256,
        "blocked": blocked_str,
        "people": b.people(),
        "total_people": sum(b.people().values()),
        "nearest_s": near_time,
        "optimised_s": opt_time,
        "saved_s": saved_s,
        "pct_saved": pct_saved,
        "lower_bound_s": lb,
        "gap_to_bound_s": gap_bound,
        "bottleneck_nearest": near_bottleneck,
        "bottleneck_opt": opt_bottleneck,
        "commit": commit,
    }
    return row


def main():
    scenarios = [
        (ROOT / "data/lab_block.json", ()),
        (ROOT / "data/lab_block.json", ("B",)),
        (ROOT / "data/iit_kgp_museum.json", ()),
        (ROOT / "data/iit_kgp_museum.json", ("MAIN",)),
        (ROOT / "data/sample_floor.json", ()),
        (ROOT / "data/sample_floor.json", ("A",)),
    ]

    out_file = ROOT / "runs/wow.csv"
    fieldnames = [
        "when",
        "building",
        "sha256",
        "blocked",
        "total_people",
        "nearest_s",
        "optimised_s",
        "saved_s",
        "pct_saved",
        "lower_bound_s",
        "gap_to_bound_s",
        "bottleneck_nearest",
        "bottleneck_opt",
        "commit",
    ]

    rows = []
    print("\nRunning NIKAAS Wow Number Benchmarks...")
    print("-" * 110)
    for path, blocked in scenarios:
        if not path.exists():
            continue
        print(f"Benchmarking {path.name} (blocked: {list(blocked) or 'none'})...", end="", flush=True)
        r = run_benchmark(path, blocked)
        rows.append(r)
        print(f" done. Saved: {r['saved_s']} s ({r['pct_saved']}%) | Gap to Bound: {r['gap_to_bound_s']} s")

    with out_file.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print("-" * 110)
    print(f"Results saved to {out_file}\n")
    print(f"| Building | Blocked | People | Nearest (s) | Optimised (s) | Time Saved | % Saved | Lower Bound (s) | Gap to Bound |")
    print(f"|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['building']} | {r['blocked']} | {r['total_people']} | {r['nearest_s']} | {r['optimised_s']} | **{r['saved_s']} s** | **{r['pct_saved']}%** | {r['lower_bound_s']} | {r['gap_to_bound_s']} s |")


if __name__ == "__main__":
    main()
