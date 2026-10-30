# Ayush — optimiser, lower bound, wow number

Part of Nikaas (AfterHours 1.0). Read first: `docs/CONTRACT.md` (shared data format) and `docs/TASKS.md` (team rules, checkpoints).

Files: `nikaas/optimise.py`, `tests/test_optimise.py`, `scripts/run_wow.py`, `runs/wow.csv`.

Goal: assign each room an exit so the **last person out** leaves as early as possible, given the
simulator's model (edge capacity = width × specific flow from `nikaas/sim.py`).

1. **Greedy first (by 14:00):** start from `nearest_plan`; repeatedly move one room to another exit if
   `simulate()` total time drops; stop when no move helps. Done when it beats nearest on `data/sample_floor.json`.
2. **Lower bound (by 17:00):** a quickest-flow / time-expanded network flow LP (Ford & Fulkerson, *Flows in
   Networks*, 1962) on the same graph, solved with `scipy.optimize.linprog` (HiGHS backend is fine as a
   library call). Report `lower_bound_s`. Done when a test shows `lower_bound_s <= total_time_s` for every plan tried.
3. **`optimise(building, blocked=()) -> {"plan", "total_time_s", "lower_bound_s"}`**; re-plan with a blocked
   exit in < 2 s on the CSE Labs graph.
4. **Tests:** (a) two exits, one blocked → everyone to the other; (b) **negative control:** a building where
   nearest is already optimal → optimiser reports the same time, no fake gain; (c) bound ≤ plan time.
5. **Wow number (by 06:00):** `scripts/run_wow.py` runs nearest vs optimised vs blocked on `data/cse_labs.json`,
   writes `runs/wow.csv` with building sha256, times, gap to the bound, git commit.
6. **"Beat Nikaas" score:** function that takes a judge's hand-made plan and returns its time and the gap to Nikaas.

Fallback: if the LP is slow or wrong, keep greedy and use a simple bound: total people / total exit capacity + shortest walk.

## Notes from Chirag (build lead)
Newest at the bottom. Check this section after every `git pull`.
- **11:47** — Use `simulate(b, plan, blocked)` from `nikaas/sim.py` to score any plan; `nearest_plan(b, blocked)` is your starting point. Return shape for `/optimise` is in `docs/CONTRACT.md`; Chirag wires the endpoint once `optimise()` is pushed.
