"""Tests for multi-floor graph quality assurance (QA)."""
import copy
import json
from pathlib import Path

import pytest
from nikaas.graph_qa import analyze_graph

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def clean_multifloor():
    return json.loads((ROOT / "data/multi_floor_office.json").read_text(encoding="utf-8"))


def test_valid_multifloor_graph_passes_with_high_score(clean_multifloor):
    report = analyze_graph(clean_multifloor)
    assert report["score"] == 100.0
    assert report["checks"]["multi_floor"]["status"] == "pass"
    assert report["checks"]["multi_floor"]["floors_count"] == 3
    # No critical warnings
    crit = [w for w in report["warnings"] if w["severity"] == "critical"]
    assert len(crit) == 0


def test_occupied_floor_disconnected_is_flagged(clean_multifloor):
    d = copy.deepcopy(clean_multifloor)
    # Sever all stairs connecting F2
    d["edges"] = [e for e in d["edges"] if not (e.get("kind") == "stair" and ("F2" in e["from"] or "F2" in e["to"]))]
    report = analyze_graph(d)
    w_codes = [w["code"] for w in report["warnings"]]
    assert "OCCUPIED_FLOOR_DISCONNECTED" in w_codes
    disc_w = next(w for w in report["warnings"] if w["code"] == "OCCUPIED_FLOOR_DISCONNECTED")
    assert "F2" in disc_w["message"]
    assert disc_w["severity"] == "critical"


def test_unknown_floor_reference_flagged(clean_multifloor):
    d = copy.deepcopy(clean_multifloor)
    d["nodes"][0]["floor_id"] = "F_GHOST"
    report = analyze_graph(d)
    w_codes = [w["code"] for w in report["warnings"]]
    assert "UNKNOWN_FLOOR_REFERENCE" in w_codes
    ghost_w = next(w for w in report["warnings"] if w["code"] == "UNKNOWN_FLOOR_REFERENCE")
    assert ghost_w["severity"] == "critical"
    assert "F_GHOST" in ghost_w["message"]


def test_cross_floor_non_stair_flagged(clean_multifloor):
    d = copy.deepcopy(clean_multifloor)
    for e in d["edges"]:
        if e.get("kind") == "stair":
            e["kind"] = "corridor"
            break
    report = analyze_graph(d)
    w_codes = [w["code"] for w in report["warnings"]]
    assert "CROSS_FLOOR_NON_STAIR" in w_codes
    w = next(w for w in report["warnings"] if w["code"] == "CROSS_FLOOR_NON_STAIR")
    assert w["severity"] == "critical"


def test_stair_missing_length_flagged(clean_multifloor):
    d = copy.deepcopy(clean_multifloor)
    for e in d["edges"]:
        if e.get("kind") == "stair":
            del e["length"]
            break
    report = analyze_graph(d)
    w_codes = [w["code"] for w in report["warnings"]]
    assert "STAIR_MISSING_LENGTH" in w_codes
    w = next(w for w in report["warnings"] if w["code"] == "STAIR_MISSING_LENGTH")
    assert w["severity"] == "warning"


def test_stair_invalid_length_flagged(clean_multifloor):
    d = copy.deepcopy(clean_multifloor)
    for e in d["edges"]:
        if e.get("kind") == "stair":
            e["length"] = -2.5
            break
    report = analyze_graph(d)
    w_codes = [w["code"] for w in report["warnings"]]
    assert "STAIR_INVALID_PHYSICAL_LENGTH" in w_codes


def test_malformed_floor_metadata_flagged(clean_multifloor):
    d = copy.deepcopy(clean_multifloor)
    d["floors"][0]["elevation_m"] = "not_a_number"
    report = analyze_graph(d)
    w_codes = [w["code"] for w in report["warnings"]]
    assert "MALFORMED_FLOOR_METADATA" in w_codes


def test_inconsistent_capacity_group_flagged(clean_multifloor):
    d = copy.deepcopy(clean_multifloor)
    # Add corridor edge with a capacity group
    d["edges"].append({
        "from": "stair_north_GF",
        "to": "corr_GF_mid",
        "width": 2.0,
        "length": 10.0,
        "kind": "corridor",
        "capacity_group": "stairwell_north"
    })
    report = analyze_graph(d)
    w_codes = [w["code"] for w in report["warnings"]]
    assert "INCONSISTENT_CAPACITY_GROUP" in w_codes


def test_legacy_single_floor_qa_remains_stable():
    legacy_d = json.loads((ROOT / "data/sample_floor.json").read_text(encoding="utf-8"))
    report = analyze_graph(legacy_d)
    assert report["score"] == 100.0
    assert report["checks"]["multi_floor"]["status"] == "pass"
    assert report["checks"]["multi_floor"]["floors_count"] == 1
