# Build log

## 30 Oct
- **09:30** Clock starts. Idea pitched to mentor (Nikaas, Theme 03).
- **11:28** Repo started. Building-graph contract, simulator, API. 6 tests pass. Baseline on the
  provisional sample floor (`runs/results.csv`): nearest exit 119 s, 174 people to Stair A vs 126 to B,
  peak queue 92 at Stair A. With Stair A blocked: 196.75 s, all 300 via Stair B.
- **11:35** Task briefs per person (`docs/TASKS.md`), sample frames for the frontend in `data/`.
- **11:44** Per-edge peak queue (`edge_load`) in the simulate output for jam colouring; Lambda entry point `nikaas.api.handler` (Mangum) ready for Abhijeet. 8 tests pass.
- **11:58** Building validation (`/validate`, readable problems, 422 on bad input) and per-room `routes` in the simulate output. 13 tests pass.
- **12:00** No public DBIT floor plan found online. Added `data/lab_block.json` (representative L-shaped lab block, 528 people, 3 stairs; generator `scripts/make_lab_block.py`). Nearest exit: 211.75 s, 264/194/70 across stairs A/B/C, bottleneck the narrow west stair A (queue 153). Blocking A costs only +15 s; blocking main stair B: 305.75 s.
