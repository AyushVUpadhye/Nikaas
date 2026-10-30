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
- **12:05** Demo building switched to a real Indian floor plan: IIT Kharagpur NMST Block-B panel (CC BY 3.0 photo), digitised by hand into 15 rooms / 507 people / 3 exits, overlay-checked against the photo. Nearest exit 112.75 s; bottleneck Audiovisual Hall west door (queue 120). MAIN blocked: 242.75 s; WEST blocked: 208.25 s.
- **12:07** Fix: occupants split across all doors of a room. Re-measured IIT KGP (commit 68a65a8): nearest 112.75 s, bottleneck verandah door `g820-VER` (peak queue 99), not the AV hall. All frames files regenerated; new `door_routes` field. 15 tests pass.
- **12:10** Validated against SFPE Engineering Guide Example 1: 245.25 s vs published 245.2 s (`test_reproduces_sfpe_engineering_guide_example_1`). Re-measured (commit 36c9916): IIT KGP nearest 145.25 s (bottleneck verandah door, queue 104); lab block nearest 301.25 s, and **closing Stair A makes it faster (284.75 s)** - the nearest-exit rule is worse than losing a stair.
- **12:16** `web/` started: 2D player of the IIT KGP building playing real simulator frames (nearest vs main entrance blocked), handed to Bhumika. Design research method added: `docs/DESIGN_RESEARCH.md`.
