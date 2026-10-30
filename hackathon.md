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
- **12:17** Queued people now get distinct positions in frames (render fix only; evacuation times unchanged). 17 tests pass.
- **12:25** API responses gzipped (largest run 4.54 MB raw, 0.08 MB on the wire; Lambda limit 6 MB). Roles changed: Chirag takes the website; Bhumika takes pitch, README, demo video and Crowd mode stadium data; Abhijeet keeps AWS + vision.
- **12:23** Live API verified (Abhijeet's SAM deploy, ap-south-1): `/simulate` on IIT KGP returns 145.25 s, same as local; asked for a redeploy to pick up gzip. Bhumika's task: Crowd mode crush-risk feature (`nikaas/crowd.py`, research-backed density thresholds) plus pitch, README, video, and an hourly improve/research loop.
- **12:25** Website: tap any exit to block it; the page calls the live AWS `/simulate` and animates the new run (verified in the browser: verandah door blocked = 208.25 s, same as `docs/RESULTS.md`). Green escape routes per door, time change vs all-exits-open, loading and error states, `?demo=1` uses saved runs with no backend.
- **12:32** Landing page: hero with the real map photo (credited), the three incidents, four stats loaded from runs/ (`web/public/data/results.json`, `validation.json` written by `scripts/report.py` and the new `scripts/run_validation.py`), features, FAQ. SFPE validation now also saved to `runs/validation.csv` (245.25 s vs 245.2 s, 0.02%).
- **12:33** Reviewed Abhijeet: Bedrock Nova Pro reads the IIT KGP photo into a valid graph, 14/15 rooms, median 3.3 m error, but 1/3 exits (388.5 s vs 145.25 s hand). Exits are the next fix. 25 tests pass.
- **12:44** Website 3D view (default, 2D toggle kept): white architectural walls with door gaps on a dark floor, human figures coloured by state, green escape ribbons per door, exit signs that turn red when blocked, orbit camera; tap an exit in 3D to block it (live AWS re-run). npm registry blocked at the venue, so three.js 0.160.0 is vendored from unpkg.
- **12:46** `?demo=1` story mode (landing, nearest-exit run, main entrance blocked, captions; offline) verified in the browser.
- **12:51** Website: building switch Hand-digitised vs Read from the photo (Amazon Nova Pro), with an honest banner (14 rooms, 1 of 3 exits). Live run of the photo graph on AWS = 388.5 s, matches runs/vision_check.md. Fixed a crash when switching buildings (old routes drawn on the new graph).
