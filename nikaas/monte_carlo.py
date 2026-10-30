"""Stochastic Monte Carlo evacuation analysis under behavioral and crowd uncertainty.

Evaluates the distribution of egress times across N runs with:
1. Stochastic pre-movement delays U(t_min, t_max) per occupant (configurable managed-drill benchmark assumption).
2. Uniform occupancy perturbations (+/- 20%) per room to model crowd variance.

Reports empirical percentiles (P50, P95), win rates, and expected time savings.
"""
from __future__ import annotations

import copy
import random
from typing import Any

import numpy as np

from .building import Building, load, nearest_plan
from .optimise import optimise
from .sim import simulate


def run_monte_carlo(
    b: Building | dict,
    blocked: tuple[str, ...] | list[str] | set[str] = (),
    n_runs: int = 200,
    premove: tuple[float, float] = (5.0, 30.0),
    occ_range: tuple[float, float] = (0.8, 1.2),
    seed: int = 42,
) -> dict[str, Any]:
    """Run an N-run Monte Carlo evacuation trial comparing Nearest vs Nikaas plans.

    Args:
        b: Building graph or JSON dict.
        blocked: Sequence of blocked exit node IDs.
        n_runs: Number of stochastic iterations (default 200).
        premove: (min_s, max_s) uniform pre-movement delay window per person.
        occ_range: (min_factor, max_factor) occupancy multiplier per room.
        seed: Master random seed for deterministic reproduction.

    Returns:
        dict containing individual 'records' and aggregate 'summary' statistics.
    """
    if not isinstance(b, Building):
        b = load(b)
    blocked_set = set(blocked)

    # Base allocations on unperturbed building
    plan_near = nearest_plan(b, blocked_set)
    opt_res = optimise(b, blocked_set)
    plan_opt = opt_res["plan"]

    records = []
    base_people = b.people()

    for i in range(n_runs):
        run_seed = seed + i * 1000
        run_rng = random.Random(run_seed)

        # Perturb building occupancy by room
        b_run = copy.deepcopy(b)
        for r in b_run.rooms:
            base_n = base_people.get(r, 0)
            if base_n > 0:
                mult = run_rng.uniform(*occ_range)
                new_n = max(1, int(round(base_n * mult)))
                b_run.nodes[r]["people"] = new_n

        total_people = sum(b_run.people().values())

        # Simulate nearest plan
        sim_near = simulate(
            b_run, plan_near, blocked=blocked_set, seed=run_seed, premove=premove, frame_every=1e9
        )
        t_near = sim_near["total_time_s"]

        # Simulate Nikaas plan
        sim_opt = simulate(
            b_run, plan_opt, blocked=blocked_set, seed=run_seed, premove=premove, frame_every=1e9
        )
        t_opt = sim_opt["total_time_s"]

        saved = round(t_near - t_opt, 2)
        records.append({
            "run": i + 1,
            "seed": run_seed,
            "occupants": total_people,
            "nearest_s": t_near,
            "opt_s": t_opt,
            "saved_s": saved,
            "opt_faster": t_opt < t_near,
            "opt_tied_or_better": t_opt <= t_near,
        })

    near_times = [r["nearest_s"] for r in records]
    opt_times = [r["opt_s"] for r in records]
    saved_times = [r["saved_s"] for r in records]

    wins = sum(1 for r in records if r["opt_faster"])
    ties = sum(1 for r in records if r["nearest_s"] == r["opt_s"])

    near_p50 = round(float(np.percentile(near_times, 50)), 2)
    opt_p50 = round(float(np.percentile(opt_times, 50)), 2)
    p50_saved = round(float(np.percentile(saved_times, 50)), 2)
    pct_saved_p50 = round(((near_p50 - opt_p50) / near_p50) * 100.0, 1) if near_p50 > 0 else 0.0

    summary = {
        "n_runs": n_runs,
        "premove_range_s": premove,
        "occ_perturb_range": occ_range,
        "nearest_p50": near_p50,
        "nearest_p95": round(float(np.percentile(near_times, 95)), 2),
        "nearest_mean": round(float(np.mean(near_times)), 2),
        "nearest_std": round(float(np.std(near_times)), 2),
        "opt_p50": opt_p50,
        "opt_p95": round(float(np.percentile(opt_times, 95)), 2),
        "opt_mean": round(float(np.mean(opt_times)), 2),
        "opt_std": round(float(np.std(opt_times)), 2),
        "wins": wins,
        "ties": ties,
        "win_pct": round(wins / n_runs * 100.0, 1),
        "mean_saved_s": round(float(np.mean(saved_times)), 2),
        "p50_saved_s": p50_saved,
        "pct_saved_p50": pct_saved_p50,
    }

    return {"records": records, "summary": summary}
