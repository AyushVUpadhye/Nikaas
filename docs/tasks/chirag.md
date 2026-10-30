# Chirag — build lead, simulator, API, website

Part of Nikaas (AfterHours 1.0). Read first: `docs/CONTRACT.md` (shared data format) and `docs/TASKS.md` (team rules, checkpoints).

Already done: `nikaas/building.py`, `nikaas/sim.py`, `nikaas/api.py`, 6 tests, `runs/results.csv`.

1. **CSE Labs graph** — `data/cse_labs.json` from the photo of the posted evacuation map (rooms, corridors,
   exits, widths in metres, people per room). Done when `python scripts/run_nearest.py data/cse_labs.json` prints a result.
2. **Per-edge stats** — add `edge_load` (peak queue per edge) to the simulate output so the UI can colour jams.
   Done when a test checks the busiest edge is the stair in front of the nearest exit.
3. **Wire `/optimise`** into `nikaas/api.py` once Ayush's `optimise()` exists. Done when a TestClient test calls it.
4. **Hand the API to Abhijeet** for Lambda (`nikaas.api:app`, add `mangum` handler `handler = Mangum(app)`).
5. **Website `web/`** (taken over from Bhumika at 12:25): restyle per `docs/DESIGN_RESEARCH.md` + `docs/VISUAL_STYLE.md`, landing page, tap-to-block against the live API, 3D view, `?demo=1` mode for Bhumika's video. 2D player already works.
6. Review every PR / merge; decide scope cuts at 19:00 and 23:00.
