"""Acceptance tests written before trusting any number (hand-computed expectations)."""
import json
from pathlib import Path

import pytest

from nikaas.building import load, nearest_plan
from nikaas.sim import SPECIFIC_FLOW, WALK_SPEED, simulate

ROOT = Path(__file__).resolve().parents[1]


def one_room(n, door_w=1.0, length=10.0):
    return load({"nodes": [{"id": "r", "type": "room", "x": 0, "z": 0, "people": n, "w": 0.1, "d": 0.1},
                           {"id": "X", "type": "exit", "x": length, "z": 0}],
                 "edges": [{"from": "r", "to": "X", "width": door_w, "length": length, "kind": "door"}]})


def test_single_door_matches_hand_calculation():
    # Hand calc: last person enters the door after n / (w * Fs) s, then walks L / v.
    n, w, L = 120, 1.0, 10.0
    b = one_room(n, w, L)
    out = simulate(b, {"r": "X"})
    expected = n / (w * SPECIFIC_FLOW["door"]) + L / WALK_SPEED
    assert out["completed"]
    assert out["total_time_s"] == pytest.approx(expected, rel=0.05)


def test_everyone_is_accounted_for():
    b = load(ROOT / "data/sample_floor.json")
    out = simulate(b, nearest_plan(b))
    assert out["completed"]
    assert sum(out["per_exit"].values()) == out["people"] == sum(b.people().values())


def test_blocked_exit_sends_everyone_to_the_other_one():
    b = load(ROOT / "data/sample_floor.json")
    plan = nearest_plan(b, blocked={"A"})
    assert set(plan.values()) == {"B"}
    out = simulate(b, plan, blocked={"A"})
    assert out["per_exit"]["A"] == 0 and out["per_exit"]["B"] == out["people"]


def test_plan_into_blocked_exit_is_rejected():
    b = load(ROOT / "data/sample_floor.json")
    with pytest.raises(ValueError):
        simulate(b, {r: "A" for r in b.rooms}, blocked={"A"})


def test_wider_door_is_never_slower():
    narrow = simulate(one_room(80, 0.9), {"r": "X"})["total_time_s"]
    wide = simulate(one_room(80, 1.8), {"r": "X"})["total_time_s"]
    assert wide < narrow


def test_frames_are_in_contract_shape():
    b = load(ROOT / "data/sample_floor.json")
    out = simulate(b, nearest_plan(b))
    f = out["frames"][0]
    assert set(f) == {"t", "people"}
    x, z, state = f["people"][0]
    assert state in {"inside", "walking", "queuing", "stairs", "out"}
    json.dumps(out)  # must serialise for the API
