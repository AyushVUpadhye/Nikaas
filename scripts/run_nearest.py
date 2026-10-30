"""Measure the nearest-exit baseline and save it under runs/ (numbers shown to judges come from here)."""
import csv, datetime, hashlib, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nikaas.building import load, nearest_plan
from nikaas.sim import simulate

src = Path(sys.argv[1] if len(sys.argv) > 1 else "data/sample_floor.json")
b = load(src)
blocked = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()
plan = nearest_plan(b, blocked)
out = simulate(b, plan, blocked)
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "uncommitted"
row = {"when": datetime.datetime.now().isoformat(timespec="seconds"), "building": src.name,
       "sha256": hashlib.sha256(src.read_bytes()).hexdigest()[:12], "plan": "nearest", "blocked": "+".join(sorted(blocked)),
       "people": out["people"], "total_time_s": out["total_time_s"], "per_exit": out["per_exit"],
       "bottleneck": out["bottleneck"], "peak_queue": out["peak_queue"], "commit": commit}
f = Path("runs/results.csv"); new = not f.exists()
with f.open("a", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(row)); new and w.writeheader(); w.writerow(row)
print(row)
