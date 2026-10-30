# Nikaas — who does what (AfterHours 1.0 finale, deadline 31 Oct 09:30)

Each section below is self-contained: it lists the files you own and how to know you are done.
Read `docs/CONTRACT.md` first. Commit at least every hour (mandatory checkpoints):
small commits, clear messages, `git pull --rebase` before `git push`.

Team rules
- Code against the contract, not each other's code. Use the saved files in `data/` until the API is live.
- Every number shown to judges comes from a script that writes to `runs/`. No made-up numbers.
- Write everything fresh here. Do not copy code from earlier projects or from the concept video.
- Stuck more than 30 minutes: tell Chirag (build lead) and take the fallback listed in your section.
- Ayush stays the registered team lead on Unstop (team ID AH50) and submits the form.

Checkpoints: **15:30** something demoable · **23:00** everything deployed · **07:30** code freeze · **09:00** submit.

---

## Chirag — build lead, simulator, API

Already done: `nikaas/building.py`, `nikaas/sim.py`, `nikaas/api.py`, 6 tests, `runs/results.csv`.

1. **CSE Labs graph** — `data/cse_labs.json` from the photo of the posted evacuation map (rooms, corridors,
   exits, widths in metres, people per room). Done when `python scripts/run_nearest.py data/cse_labs.json` prints a result.
2. **Per-edge stats** — add `edge_load` (peak queue per edge) to the simulate output so the UI can colour jams.
   Done when a test checks the busiest edge is the stair in front of the nearest exit.
3. **Wire `/optimise`** into `nikaas/api.py` once Ayush's `optimise()` exists. Done when a TestClient test calls it.
4. **Hand the API to Abhijeet** for Lambda (`nikaas.api:app`, add `mangum` handler `handler = Mangum(app)`).
5. Review every PR / merge; decide scope cuts at 19:00 and 23:00.

## Ayush — optimiser, lower bound, wow number

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

## Bhumika — web app, realistic 3D view

Folder: `web/` (Vite + React + TypeScript, no UI kit). Style rules: `docs/VISUAL_STYLE.md` (copy it into the repo from Chirag's laptop).

1. **2D player (by 15:30):** load `data/frames_sample_nearest.json`; draw rooms/corridors from
   `data/sample_floor.json` top-down; play frames with play/pause and 1×/2×/4× speed; colour people by `state`
   (walking orange, queuing red, stairs blue, out hidden). Clock + dot grid of all people + legend with counts.
2. **Live API (by 19:00):** call `POST /simulate` (local: `uvicorn nikaas.api:app`, URL in `.env`); show
   nearest vs Nikaas side by side when `/optimise` exists.
3. **Tap to block:** click an exit → re-run with `blocked` → animate the new plan. Show `bottleneck`.
4. **3D view (after 19:00):** three.js, white architectural walls, dark floor, human figures, green route ribbons
   from each room to its exit, fire + red cross on a blocked exit, perspective camera. 2D stays as fallback.
5. **`?demo=1`** plays saved frames with no backend; check it at 400 px wide too.

Fallback: if 3D is not ready by 03:00, the 2D player is the demo.

## Abhijeet — all AWS, photo → graph, README, pitch

1. **AWS on every laptop (now):** IAM user per member, `aws configure` (region `ap-south-1`), billing alarm ₹500,
   Bedrock model access (Amazon Nova, vision-capable). Done when `aws sts get-caller-identity` works on all 4 laptops.
2. **Deploy skeleton (by 15:30):** `template.yaml` (AWS SAM): HTTP API → Lambda (Python 3.11, `nikaas.api` via
   Mangum) + S3 bucket for the web build. `sam build && sam deploy`. Done when `/health` answers on the public URL.
3. **Photo → graph (by 19:00):** `nikaas/vision.py`: send the map photo to Bedrock (`converse` with an image),
   ask for JSON in the `docs/CONTRACT.md` format, validate with `nikaas.building.load`. Compare against Chirag's
   hand-made `data/cse_labs.json`; write the differences to `runs/vision_check.md`.
4. **Upload flow (by 23:00):** `POST /vision` endpoint + S3 for photos; deploy everything; frontend on S3.
5. **README "For judges, start here" (by 06:00):** live URL, video, how to run, results table generated from `runs/`.
6. **Pitch + video (07:30–09:00):** 3-minute pitch, rehearse twice with a timer; record the demo.

Fallback: if Bedrock misreads the map, the hand-made JSON + editor is the demo and vision is shown as "assisted".
