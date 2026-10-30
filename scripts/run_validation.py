"""Run the SFPE Engineering Guide Example 1 reproduction and save it to runs/ (and the website).
Published hand calculation: 245.2 s (Thunderhead Pathfinder verification docs, SFPE Example 1)."""
import csv, datetime, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nikaas.building import load
from nikaas.sim import WALK_SPEED, simulate

FT, IN, PUBLISHED = 0.3048, 0.0254, 245.2
b = load({"nodes": [{"id": "room", "type": "room", "x": 0, "z": 0, "people": 150, "w": .01, "d": .01},
                    {"id": "top", "type": "corridor", "x": 0, "z": 0}, {"id": "bot", "type": "corridor", "x": 0, "z": 0},
                    {"id": "X", "type": "exit", "x": 0, "z": 0}],
          "edges": [{"from": "room", "to": "top", "width": 32 * IN, "length": WALK_SPEED, "kind": "door"},
                    {"from": "top", "to": "bot", "width": 44 * IN, "length": 50 * FT, "kind": "stair"},
                    {"from": "bot", "to": "X", "width": 30 * FT, "length": 10 * FT, "kind": "corridor"}]})
ours = simulate(b, {"room": "X"})["total_time_s"]
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
row = {"when": datetime.datetime.now().isoformat(timespec="seconds"), "case": "SFPE Engineering Guide Example 1",
       "published_s": PUBLISHED, "ours_s": ours, "error_pct": round(100 * (ours - PUBLISHED) / PUBLISHED, 3), "commit": commit}
f = Path("runs/validation.csv"); new = not f.exists()
with f.open("a", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(row)); new and w.writeheader(); w.writerow(row)
if Path("web/public/data").exists():
    json.dump(row, open("web/public/data/validation.json", "w"), indent=1)
print(row)
