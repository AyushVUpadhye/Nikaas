"""API response size must stay under the AWS Lambda synchronous response limit (6 MB)."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from nikaas.api import app

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_LIMIT = 6 * 1024 * 1024


def test_largest_scenario_is_gzipped_well_under_lambda_limit():
    b = json.loads((ROOT / "data/lab_block.json").read_text())
    r = TestClient(app).post("/simulate", json={"building": b, "blocked": ["B"]}, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and r.headers.get("content-encoding") == "gzip"
    wire = int(r.headers["content-length"])  # compressed bytes actually sent
    assert wire * 4 / 3 < LAMBDA_LIMIT / 4  # even after base64 (x4/3), under a quarter of the limit


def test_frame_every_thins_frames():
    b = json.loads((ROOT / "data/iit_kgp_museum.json").read_text(encoding="utf-8"))
    c = TestClient(app)
    full = c.post("/simulate", json={"building": b}).json()
    thin = c.post("/simulate", json={"building": b, "frame_every": 2}).json()
    assert len(thin["frames"]) < 0.6 * len(full["frames"]) and thin["total_time_s"] == full["total_time_s"]


def test_health_lists_routes_so_stale_deploys_are_visible():
    r = TestClient(app).get("/health").json()
    assert r["ok"] and {"simulate", "optimise", "validate"} <= set(r["routes"])


def test_beat_nikaas_judge_cannot_beat_the_optimiser_with_nearest_exit():
    b = json.loads((ROOT / "data/iit_kgp_museum.json").read_text(encoding="utf-8"))
    from nikaas.building import load, nearest_plan
    plan = nearest_plan(load(b))
    c = TestClient(app)
    r = c.post("/beat", json={"building": b, "plan": plan}).json()
    assert r["judge_time_s"] >= r["nikaas_time_s"] >= r["lower_bound_s"] and r["beat_nikaas"] is False
    bad = c.post("/beat", json={"building": b, "plan": {"avhall": "MAIN"}})
    assert bad.status_code == 422 and "no exit for rooms" in bad.text


def test_crowd_analysis_is_opt_in():
    b = json.loads((ROOT / "data/iit_kgp_museum.json").read_text(encoding="utf-8"))
    c = TestClient(app)
    assert "crowd" not in c.post("/simulate", json={"building": b, "frame_every": 10}).json()
    assert "crowd" in c.post("/simulate", json={"building": b, "frame_every": 10, "crowd": True}).json()
