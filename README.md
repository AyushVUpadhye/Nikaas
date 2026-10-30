# Nikaas

## For judges, start here
**Nikaas is an open-source evacuation digital twin** — photograph a posted exit map, and Nikaas times the evacuation and finds the room-to-exit assignment that moves everyone out fastest.

- **44.6% faster** evacuation movement time on the demo lab block: nearest-exit rule 301 s → Nikaas plan 167 s, saving 134 s for 528 people (`runs/wow.csv`).
- **Within 3.71 s of a proven lower bound** — no plan can move everyone out faster than 163.04 s with the same exits and widths, and Nikaas reaches 166.75 s (`runs/wow.csv`).
- **Validated against SFPE Handbook Example 1**: 245.25 s vs the published 245.2 s (0.05 s error, `tests/test_sim.py`).
- **Crowd mode (in progress, not built yet)**: will flag corridors above the crowd-density thresholds researched in `docs/CROWD_RESEARCH.md`.

Live site: **http://nikaas-webbucket-hbkfctr0cw8s.s3-website.ap-south-1.amazonaws.com** (Home, Twin, Beat Nikaas, Evidence) · API: https://4kzez16ucj.execute-api.ap-south-1.amazonaws.com/health · Demo video: *(fill before submission)*

---

**Photograph the exit map. Get everyone out faster.** An evacuation digital twin: a building's
posted exit map becomes a graph, a simulator times the evacuation, and an optimiser assigns each
room the exit that empties the building fastest, re-planning when a stair is blocked.

Built from scratch at **AfterHours 1.0** (DBIT, 30–31 Oct 2026), Theme 03: Simulation & Digital
Twins, by **TheGoodEngineers** (team AH50): Ayush V U, Bhumika G, Abhijeet, Chirag R H.

**Working today:** simulator (SFPE-validated) · API live on AWS (`/simulate`, `/optimise`, `/beat`, `/vision`) · website with 2D + 3D twin, nearest-vs-Nikaas comparison, tap-to-block, Beat Nikaas · photo-to-building with Amazon Nova
**In progress:** Crowd mode density analysis (densities being corrected) · stadium building
**Not built yet:** multi-floor buildings · NBC travel-distance check

> Every number above comes from `runs/` or `docs/RESULTS.md`. If a number has no file behind it, it is not here.

## Validated
The simulator reproduces the SFPE Engineering Guide's Example 1 (300 people, two doors, two stairs):
**245.25 s vs the published 245.2 s** (`tests/test_sim.py::test_reproduces_sfpe_engineering_guide_example_1`).
All results: [`docs/RESULTS.md`](docs/RESULTS.md), generated from `runs/`.

## Demo building
A real posted floor-plan panel: **Nehru Museum of Science & Technology, Block B, IIT Kharagpur**,
digitised into `data/iit_kgp_museum.json` (`scripts/make_iit_kgp.py`; overlay check in
`data/maps/iit_kgp_overlay.jpg`). Scale, occupancy and exit widths are our assumptions (`docs/QUESTIONS.md`).

Photo: "Floor Plan Panel - NMST - IIT Kharagpur" by Biswarup Ganguly, CC BY 3.0, via Wikimedia Commons
(https://commons.wikimedia.org/wiki/File:Floor_Plan_Panel_-_NMST_-_IIT_Kharagpur_-_West_Midnapore_2015-09-28_4616.JPG).

## Run locally
```
pip install -r requirements.txt
python -m pytest -q
python scripts/run_nearest.py data/sample_floor.json
uvicorn nikaas.api:app --reload
```

## Layout
- `nikaas/building.py` graph loading, shortest paths, nearest-exit plan
- `nikaas/sim.py` flow-limited evacuation simulator (SFPE hydraulic model)
- `nikaas/api.py` FastAPI app
- `data/` building graphs · `runs/` measured outputs · `docs/CONTRACT.md` shared format
