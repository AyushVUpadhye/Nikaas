"""Tests for nikaas/crowd.py — crowd density and crush-risk detection."""
import math
import pytest
from nikaas.crowd import analyse, narrative, CRUSH_THRESHOLD, CONCERN_THRESHOLD


# ── minimal building helpers ──────────────────────────────────────────────────

def _simple_building(corridor_width=2.0, corridor_length=5.0):
    """One room → one corridor → one exit.  Corridor: width × length metres."""
    return {
        "nodes": [
            {"id": "room1", "type": "room",     "x": 0, "z": -5, "w": 8, "d": 8, "people": 40},
            {"id": "c1",    "type": "corridor",  "x": 0, "z": 0},
            {"id": "EXIT",  "type": "exit",      "x": 0, "z": corridor_length},
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
    # people at corridor midpoint (0, 2.5) — on the c1-EXIT segment
    people = [[0.0, 2.5, "queuing"]] * 40
    result = analyse(_sim_result([_frame(1.0, people)]), building)

    edge_id = "c1-EXIT"
    assert edge_id in result["edge_density"]
    rec = result["edge_density"][edge_id]
    assert abs(rec["area_m2"] - 8.0) < 0.5, f"area={rec['area_m2']}"
    assert rec["peak_density"] >= CRUSH_THRESHOLD, f"density={rec['peak_density']}"
    crush_entries = [e for e in result["crush_risk"] if e["edge_id"] == edge_id]
    assert crush_entries, "expected a crush_risk entry"
    assert crush_entries[0]["level"] == "crush"


# ── negative control: wide empty corridor ─────────────────────────────────────

def test_wide_empty_corridor_not_flagged():
    """A wide, empty corridor must not be flagged as crush or concern."""
    building = _simple_building(corridor_width=6.0, corridor_length=10.0)
    people = [[0.0, 2.0, "walking"], [0.0, 7.0, "walking"]]
    result = analyse(_sim_result([_frame(1.0, people)]), building)

    for entry in result["crush_risk"]:
        assert entry["level"] not in ("concern", "crush"), (
            f"Wide empty corridor was flagged: {entry}"
        )


# ── concern threshold ─────────────────────────────────────────────────────────

def test_concern_threshold():
    """22 people on 8 m² corridor → 2.75 p/m² → concern but not crush."""
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


# ── thresholds are exported correctly ─────────────────────────────────────────

def test_thresholds_in_result():
    building = _simple_building()
    result = analyse(_sim_result([_frame(0.0, [])]), building)
    assert result["thresholds"]["concern"] == CONCERN_THRESHOLD
    assert result["thresholds"]["crush"] == CRUSH_THRESHOLD


# ── multi-frame: density rises then falls ─────────────────────────────────────

def test_multiframe_peak_captured():
    """Peak density over multiple frames must equal the maximum frame density."""
    building = _simple_building(corridor_width=2.0, corridor_length=5.0)
    mid = [0.0, 2.5, "queuing"]
    # frame 1: 10 people (safe); frame 2: 40 people (crush); frame 3: 5 people (safe)
    frames = [
        _frame(1.0, [mid] * 10),
        _frame(2.0, [mid] * 40),
        _frame(3.0, [mid] * 5),
    ]
    result = analyse(_sim_result(frames), building)
    rec = result["edge_density"]["c1-EXIT"]
    assert rec["peak_density"] >= CRUSH_THRESHOLD, "peak not captured from frame 2"
    assert rec["peak_t"] == 2.0, f"peak_t should be 2.0, got {rec['peak_t']}"


# ── first_crush_t is the earliest frame that breaches the threshold ────────────

def test_first_crush_t():
    """first_crush_t must be the earliest timestamp that breaches CRUSH_THRESHOLD."""
    building = _simple_building(corridor_width=2.0, corridor_length=5.0)
    mid = [0.0, 2.5, "queuing"]
    frames = [
        _frame(1.0, [mid] * 5),    # safe
        _frame(5.0, [mid] * 40),   # first crush frame
        _frame(8.0, [mid] * 40),   # also crush
    ]
    result = analyse(_sim_result(frames), building)
    assert result["first_crush_t"] == 5.0, f"expected 5.0, got {result['first_crush_t']}"


# ── narrative: safe building ───────────────────────────────────────────────────

def test_narrative_safe():
    building = _simple_building(corridor_width=6.0, corridor_length=10.0)
    people = [[0.0, 5.0, "walking"]]
    result = analyse(_sim_result([_frame(1.0, people)]), building)
    text = narrative(result, "test building")
    assert "below" in text, f"expected 'below' in safe narrative: {text}"
    assert "crush" not in text.lower(), f"unexpected 'crush' in safe narrative: {text}"


# ── narrative: crush scenario mentions threshold and time ─────────────────────

def test_narrative_crush():
    building = _simple_building(corridor_width=2.0, corridor_length=5.0)
    people = [[0.0, 2.5, "queuing"]] * 40
    result = analyse(_sim_result([_frame(3.0, people)]), building)
    text = narrative(result, "stadium")
    assert "stadium" in text
    assert "crush" in text.lower()
    assert "3" in text  # first_crush_t = 3.0 s should appear
