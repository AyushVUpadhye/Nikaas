"""Tests for nikaas/crowd.py — crowd density and crush-risk detection."""
import math
import pytest
from nikaas.crowd import analyse, CRUSH_THRESHOLD, CONCERN_THRESHOLD


# ── minimal building helpers ──────────────────────────────────────────────────

def _simple_building(corridor_width=2.0, corridor_length=5.0):
    """One room → one corridor → one exit.  Corridor: width × length metres."""
    return {
        "nodes": [
            {"id": "room1", "type": "room", "x": 0, "z": -5, "w": 8, "d": 8, "people": 40},
            {"id": "c1",    "type": "corridor", "x": 0, "z": 0},
            {"id": "EXIT",  "type": "exit",     "x": 0, "z": corridor_length},
        ],
        "edges": [
            {"from": "room1", "to": "c1",   "width": corridor_width, "kind": "door"},
            {"from": "c1",    "to": "EXIT",  "width": corridor_width, "kind": "corridor",
             "length": corridor_length},
        ],
    }


def _frame(t, people_list):
    return {"t": t, "people": people_list}


def _sim_result(frames, edge_load=None):
    return {
        "total_time_s": max(f["t"] for f in frames) if frames else 0,
        "frames": frames,
        "edge_load": edge_load or {},
    }


# ── hand-checked density case ─────────────────────────────────────────────────

def test_hand_checked_density():
    """40 people queuing on a 2 m wide × 5 m long corridor.

    effective_width = 2.0 - 2 × 0.20 = 1.60 m
    area = 1.60 × 5 = 8.0 m²
    density = 40 / 8.0 = 5.0 p/m²  → above CRUSH_THRESHOLD (4.0)
    """
    building = _simple_building(corridor_width=2.0, corridor_length=5.0)
    # corridor midpoint is at (0, 2.5)
    people = [[0.0, 2.5, "queuing"]] * 40
    result = analyse(_sim_result([_frame(1.0, people)]), building)

    edge_id = "c1-EXIT"
    assert edge_id in result["edge_density"]
    rec = result["edge_density"][edge_id]
    # area should be close to 8.0 m²
    assert abs(rec["area_m2"] - 8.0) < 0.5, f"area={rec['area_m2']}"
    # density should be above crush threshold
    assert rec["peak_density"] >= CRUSH_THRESHOLD, f"density={rec['peak_density']}"
    # at least one crush_risk entry for this edge
    crush_entries = [e for e in result["crush_risk"] if e["edge_id"] == edge_id]
    assert crush_entries, "expected a crush_risk entry"
    assert crush_entries[0]["level"] == "crush"


# ── negative control: wide empty corridor ─────────────────────────────────────

def test_wide_empty_corridor_not_flagged():
    """A wide, empty corridor must not be flagged as crush or concern."""
    building = _simple_building(corridor_width=6.0, corridor_length=10.0)
    # only 2 people walking, well spread out
    people = [[0.0, 2.0, "walking"], [0.0, 7.0, "walking"]]
    result = analyse(_sim_result([_frame(1.0, people)]), building)

    for entry in result["crush_risk"]:
        assert entry["level"] not in ("concern", "crush"), (
            f"Wide empty corridor was flagged: {entry}"
        )


# ── concern threshold ─────────────────────────────────────────────────────────

def test_concern_threshold():
    """~12 people on 8 m² corridor → ~3 p/m² → concern but not crush."""
    # effective area: (2.0 - 0.4) × 5.0 = 8.0 m²
    # 3 p/m² × 8 m² = 24 people; use 22 to stay between concern and crush
    building = _simple_building(corridor_width=2.0, corridor_length=5.0)
    count = 22   # 22 / 8.0 = 2.75 p/m²  →  CONCERN but not CRUSH
    people = [[0.0, 2.5, "queuing"]] * count
    result = analyse(_sim_result([_frame(1.0, people)]), building)

    concern = [e for e in result["crush_risk"] if e["level"] == "concern"]
    crush   = [e for e in result["crush_risk"] if e["level"] == "crush"]
    assert concern, f"expected concern entries; got crush_risk={result['crush_risk']}"
    assert not crush, f"did not expect crush entries at {count} people"


# ── zero people ───────────────────────────────────────────────────────────────

def test_zero_people_no_risk():
    building = _simple_building()
    result = analyse(_sim_result([_frame(0.0, [])]), building)
    assert result["crush_risk"] == []
    assert result["max_density"] == 0.0


# ── worst_edge and max_density consistency ────────────────────────────────────

def test_worst_edge_is_max():
    building = _simple_building(corridor_width=2.0, corridor_length=5.0)
    people = [[0.0, 2.5, "queuing"]] * 40
    result = analyse(_sim_result([_frame(1.0, people)]), building)
    eid = result["worst_edge"]
    assert eid != ""
    assert result["edge_density"][eid]["peak_density"] == result["max_density"]


# ── thresholds are exported correctly ────────────────────────────────────────

def test_thresholds_in_result():
    building = _simple_building()
    result = analyse(_sim_result([_frame(0.0, [])]), building)
    assert result["thresholds"]["concern"] == CONCERN_THRESHOLD
    assert result["thresholds"]["crush"] == CRUSH_THRESHOLD
