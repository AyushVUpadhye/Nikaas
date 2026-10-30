# Nikaas

## For judges, start here

**Photograph the exit map. Get everyone out faster — and know before the fire where the crowd will crush.**

Nikaas is an open-source evacuation simulator: a building's posted exit map becomes a graph, the simulator
times the full evacuation in < 1 second, and **Crowd mode** shows which corridor will exceed the
4 p/m² crush threshold — the level at which crowd forces become fatal (G. Keith Still, *Introduction to
Crowd Science*, CRC Press 2014).

- **145 s** — IIT KGP Nehru Museum, 507 people, 3 exits, nearest-exit plan (`runs/`)
- **245.25 s vs 245.2 s** — reproduces the SFPE Handbook worked example to 0.05 s
- **301 s → 284 s** — blocking the lab-block west stair makes evacuation *faster* (hydraulic model)
- **Live API:** `https://4kzez16ucj.execute-api.ap-south-1.amazonaws.com/health`

**Demo:** `?demo=1` on the live URL plays a full evacuation with no backend.
**Video:** *(link added after recording, 07:30–08:30)*

Built from scratch at **AfterHours 1.0** (DBIT, 30–31 Oct 2026), Theme 03: Simulation & Digital
Twins, by **TheGoodEngineers** (team AH50): Ayush V U, Bhumika G, Abhijeet, Chirag R H.

**Working today:** simulator · API · web UI (2D + 3D) · Crowd mode density analysis · stadium building · SFPE validation
**Not built yet:** multi-floor animation · NBC distance check · optimiser UI in web

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
