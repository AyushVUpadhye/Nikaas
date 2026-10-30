"""Tests for multi-floor evacuation simulation, stair movement, and shared stairwell capacity."""
import copy
import json
from pathlib import Path

import pytest
from nikaas.building import load, nearest_plan
from nikaas.sim import simulate, STAIR_SPEED, WALK_SPEED

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def office_building():
    return load(ROOT / "data/multi_floor_office.json")


def test_ground_floor_occupants_reach_outdoor_exit(office_building):
    b = office_building
    plan = nearest_plan(b)
    res = simulate(b, plan, frame_every=1e9)
    assert res["completed"] is True
    # GF occupants evacuated
    assert res["per_floor"]["GF"]["completed"] is True
    assert res["per_floor"]["GF"]["occupants"] == 60


def test_first_floor_occupants_reach_exit_through_stairwell(office_building):
    b = office_building
    plan = nearest_plan(b)
    res = simulate(b, plan, frame_every=1e9)
    assert res["per_floor"]["F1"]["completed"] is True
    assert res["per_floor"]["F1"]["occupants"] == 160
    # Routes from F1 use stairs
    assert any("stair_north_GF" in r for r in res["routes"].values())


def test_second_floor_occupants_traverse_multiple_stair_segments(office_building):
    b = office_building
    plan = nearest_plan(b)
    res = simulate(b, plan, frame_every=1e9)
    assert res["per_floor"]["F2"]["completed"] is True
    assert res["per_floor"]["F2"]["occupants"] == 180
    f2_route = res["routes"]["r_F2_1"]
    # Path traverses F2 landing, F1 landing, GF landing, and exit
    assert "stair_north_F2" in f2_route
    assert "stair_north_F1" in f2_route
    assert "stair_north_GF" in f2_route
    assert "exit_north" in f2_route


def test_travel_time_includes_vertical_stair_lengths(office_building):
    # Single person on F2 with 0 queue should take:
    # door (6.3m) / walk_speed + 2 flights of stairs (13m) / stair_speed + corridor (5m) / walk_speed
    d = json.loads((ROOT / "data/multi_floor_office.json").read_text(encoding="utf-8"))
    for n in d["nodes"]:
        if n.get("type") == "room":
            n["people"] = 1 if n["id"] == "r_F2_1" else 0
    b = load(d)
    plan = nearest_plan(b)
    res = simulate(b, plan, frame_every=1e9)
    t = res["total_time_s"]
    expected_stair_time = 13.0 / STAIR_SPEED
    expected_walk_time = (6.3 + 5.0) / WALK_SPEED
    # Total time should be approx walk + stair time
    assert t >= expected_stair_time + expected_walk_time - 1.0


def test_people_attributed_to_correct_floor_and_elevation_in_frames(office_building):
    b = office_building
    plan = nearest_plan(b)
    res = simulate(b, plan, frame_every=1.0)
    assert len(res["frames"]) > 0
    f0 = res["frames"][0]
    assert "people" in f0
    assert "people_3d" in f0
    # Check 3D tuple: [x, y, z, state, floor_id]
    x, y, z, state, fl = f0["people_3d"][0]
    assert fl in ("GF", "F1", "F2")
    assert y in (0.0, 3.5, 7.0)


def test_people_not_marked_out_before_reaching_outdoor_exit(office_building):
    b = office_building
    plan = nearest_plan(b)
    res = simulate(b, plan, frame_every=1.0)
    # Check every frame that no person has state="out" while their position is not at an exit
    for f in res["frames"]:
        for x, y, z, state, fl in f["people_3d"]:
            if state == "out":
                # Outdoor exit elevation is 0.0
                assert y == 0.0
                assert fl == "GF"


def test_shared_stairwell_capacity_prevents_throughput_multiplication():
    # Construct a 2-segment stairwell vs uncoupled stairwell
    # If 2 floors each feed 100 people into stairwell with capacity C = 1.0 pps
    # If capacity is shared, total time to admit 200 people into the stairwell is at least 200 / 1.0 = 200 s.
    d = {
        "name": "Stair Capacity Test",
        "floors": [
            {"id": "GF", "name": "GF", "elevation_m": 0.0},
            {"id": "F1", "name": "F1", "elevation_m": 3.5},
            {"id": "F2", "name": "F2", "elevation_m": 7.0}
        ],
        "nodes": [
            {"id": "exit", "type": "exit", "floor_id": "GF", "x": 0.0, "z": 0.0},
            {"id": "land_GF", "type": "corridor", "floor_id": "GF", "x": 0.0, "z": 2.0},
            {"id": "land_F1", "type": "corridor", "floor_id": "F1", "x": 0.0, "z": 2.0},
            {"id": "land_F2", "type": "corridor", "floor_id": "F2", "x": 0.0, "z": 2.0},
            {"id": "r_F1", "type": "room", "floor_id": "F1", "x": 5.0, "z": 2.0, "w": 4.0, "d": 4.0, "people": 100},
            {"id": "r_F2", "type": "room", "floor_id": "F2", "x": 5.0, "z": 2.0, "w": 4.0, "d": 4.0, "people": 100}
        ],
        "edges": [
            {"from": "exit", "to": "land_GF", "width": 3.0, "length": 2.0, "kind": "corridor"},
            {"from": "r_F1", "to": "land_F1", "width": 2.0, "length": 5.0, "kind": "door"},
            {"from": "r_F2", "to": "land_F2", "width": 2.0, "length": 5.0, "kind": "door"},
            # Grouped stairwell edges
            {"from": "land_F2", "to": "land_F1", "width": 1.3, "length": 5.0, "kind": "stair", "capacity_group": "shaft_1"},
            {"from": "land_F1", "to": "land_GF", "width": 1.3, "length": 5.0, "kind": "stair", "capacity_group": "shaft_1"}
        ]
    }
    b = load(d)
    res = simulate(b, {"r_F1": "exit", "r_F2": "exit"}, frame_every=1e9)
    # Effective width = 1.3 - 0.3 = 1.0 m. Specific flow = 1.012 p/s.
    # Group capacity = ~1.012 p/s.
    # Evacuating 200 people must take at least 200 / 1.012 ≈ 197.6 s.
    assert res["total_time_s"] >= 195.0


def test_blocked_stairwell_triggers_valid_alternative_routing(office_building):
    b = office_building
    # Block north exit; all people must route through south stairwell and south exit
    plan = nearest_plan(b, blocked={"exit_north"})
    res = simulate(b, plan, blocked={"exit_north"}, frame_every=1e9)
    assert res["completed"] is True
    assert res["per_exit"]["exit_north"] == 0
    assert res["per_exit"]["exit_south"] == 400


def test_all_stairwells_blocked_yields_clear_failure(office_building):
    b = office_building
    with pytest.raises(ValueError, match="no reachable open exit"):
        nearest_plan(b, blocked={"exit_north", "exit_south"})


def test_deterministic_seed_produces_identical_frames(office_building):
    b = office_building
    plan = nearest_plan(b)
    r1 = simulate(b, plan, seed=42, frame_every=2.0)
    r2 = simulate(b, plan, seed=42, frame_every=2.0)
    assert r1["total_time_s"] == r2["total_time_s"]
    assert len(r1["frames"]) == len(r2["frames"])
    assert r1["frames"][0]["people_3d"] == r2["frames"][0]["people_3d"]


def test_legacy_single_floor_frames_do_not_contain_people_3d():
    b = load(ROOT / "data/sample_floor.json")
    res = simulate(b, nearest_plan(b), frame_every=1.0)
    assert "people" in res["frames"][0]
    assert "people_3d" not in res["frames"][0]
