"""Run Monte Carlo evacuation uncertainty evaluation.

Executes N=200 stochastic simulations with random pre-movement delays (5-30s)
and occupancy perturbations (+/- 20%) comparing Nearest vs Nikaas plans.
Outputs verified statistics to runs/monte_carlo.csv.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nikaas.building import load
from nikaas.monte_carlo import run_monte_carlo


def main() -> None:
    data_files = [
        ROOT / "data/iit_kgp_museum.json",
        ROOT / "data/lab_block.json",
    ]

    out_csv = ROOT / "runs/monte_carlo.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    commit = (
        subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        or "uncommitted"
    )

    all_rows = []

    print(f"=== Running N=200 Monte Carlo Analysis (commit {commit}) ===")

    for path in data_files:
        b = load(path)
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        print(f"\nProcessing {path.name} (sha: {sha256})...")

        res = run_monte_carlo(b, n_runs=200, premove=(5.0, 30.0), occ_range=(0.8, 1.2), seed=42)
        summ = res["summary"]

        print(
            f"  Nearest: P50={summ['nearest_p50']}s, P95={summ['nearest_p95']}s, Mean={summ['nearest_mean']}s (+/- {summ['nearest_std']}s)"
        )
        print(
            f"  Nikaas:  P50={summ['opt_p50']}s, P95={summ['opt_p95']}s, Mean={summ['opt_mean']}s (+/- {summ['opt_std']}s)"
        )
        print(
            f"  Nikaas wins in {summ['wins']}/{summ['n_runs']} runs ({summ['win_pct']}%) | P50 saved: {summ['p50_saved_s']}s ({summ['pct_saved_p50']}%)"
        )

        row = {
            "when": datetime.datetime.now().isoformat(timespec="seconds"),
            "building": path.name,
            "sha256": sha256,
            "n_runs": summ["n_runs"],
            "premove_range_s": "5.0-30.0",
            "occ_perturb_pct": "+/-20%",
            "nearest_p50_s": summ["nearest_p50"],
            "nearest_p95_s": summ["nearest_p95"],
            "nearest_mean_s": summ["nearest_mean"],
            "nearest_std_s": summ["nearest_std"],
            "opt_p50_s": summ["opt_p50"],
            "opt_p95_s": summ["opt_p95"],
            "opt_mean_s": summ["opt_mean"],
            "opt_std_s": summ["opt_std"],
            "wins": summ["wins"],
            "win_pct": summ["win_pct"],
            "p50_saved_s": summ["p50_saved_s"],
            "pct_saved_p50": summ["pct_saved_p50"],
            "commit": commit,
        }
        all_rows.append(row)

    if all_rows:
        fieldnames = list(all_rows[0].keys())
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nWritten {len(all_rows)} summary records to {out_csv}")


if __name__ == "__main__":
    main()
