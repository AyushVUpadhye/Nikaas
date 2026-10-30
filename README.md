# Nikaas

**Photograph the exit map. Get everyone out faster.** An evacuation digital twin: a building's
posted exit map becomes a graph, a simulator times the evacuation, and an optimiser assigns each
room the exit that empties the building fastest, re-planning when a stair is blocked.

Built from scratch at **AfterHours 1.0** (DBIT, 30–31 Oct 2026), Theme 03: Simulation & Digital
Twins, by **TheGoodEngineers** (team AH50): Ayush V U, Bhumika G, Abhijeet, Chirag R H.

> Status: in progress during the hackathon. Every number in this README will come from a file in
> `runs/`. If a number has no file behind it, it is not here.

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
