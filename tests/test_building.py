"""Validation of building graphs that come from outside (vision, editor, API)."""
import copy
import json
from pathlib import Path

from fastapi.testclient import TestClient

from nikaas import api
from nikaas.building import load, nearest_plan, validate
from nikaas.sim import simulate

ROOT = Path(__file__).resolve().parents[1]
GOOD = json.loads((ROOT / "data/sample_floor.json").read_text())


def test_sample_floor_is_valid():
    assert validate(GOOD) == []


def test_bad_graphs_are_explained_not_crashed():
    bad = copy.deepcopy(GOOD)
    bad["edges"].append({"from": "lab1", "to": "nowhere", "width": 1})
    bad["edges"][0]["width"] = 0
    bad["nodes"][0]["people"] = -3
    probs = validate(bad)
    assert any("unknown node 'nowhere'" in p for p in probs)
    assert any("width must be > 0" in p for p in probs)
    assert any("people must be" in p for p in probs)


def test_room_cut_off_from_exits_is_reported():
    cut = copy.deepcopy(GOOD)
    cut["edges"] = [e for e in cut["edges"] if e["from"] != "staff"]
    assert "room staff cannot reach any exit" in validate(cut)


def test_routes_follow_the_plan():
    b = load(GOOD)
    plan = nearest_plan(b)
    out = simulate(b, plan)
    for room, path in out["routes"].items():
        assert path[0] == room and path[-1] == plan[room]


def test_api_rejects_invalid_building_with_reasons():
    c = TestClient(api.app)
    bad = {"nodes": [{"id": "r", "type": "room", "x": 0, "z": 0, "people": 5}], "edges": []}
    r = c.post("/simulate", json={"building": bad})
    assert r.status_code == 422 and "building has no exit" in r.json()["detail"]["problems"]
    assert c.post("/validate", json={"building": GOOD}).json() == {"ok": True, "problems": []}


def test_digitised_iit_kgp_plan_is_valid_and_credited():
    d = json.loads((ROOT / "data/iit_kgp_museum.json").read_text(encoding="utf-8"))
    assert validate(d) == []
    assert d["source"]["license"] == "CC BY 3.0" and d["source"]["author"]
    assert (ROOT / d["source"]["photo"]).exists()
