# Nikaas

**Photograph the exit map. Get everyone out faster.** An evacuation digital twin: a building's
posted exit map becomes a graph, a simulator times the evacuation, and an optimiser assigns each
room the exit that empties the building fastest, re-planning when a stair is blocked.

Built from scratch at **AfterHours 1.0** (DBIT, 30–31 Oct 2026), Theme 03: Simulation & Digital
Twins, by **TheGoodEngineers** (team AH50): Ayush V U, Bhumika G, Abhijeet, Chirag R H.

> Status: in progress during the hackathon. Every number in this README will come from a file in
> `runs/`. If a number has no file behind it, it is not here.

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
