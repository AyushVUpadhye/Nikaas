"""Tests for Graph Quality Analysis (QA) and Auto-Repair Engine."""
import copy
import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nikaas.api import app
from nikaas.graph_qa import analyze_graph, exit_flow_capacity, repair_graph

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def clean_building():
    return json.loads((ROOT / "data/sample_floor.json").read_text(encoding="utf-8"))


def test_clean_graph_passes_with_high_score(clean_building):
    report = analyze_graph(clean_building)
    assert report["status"] == "pass"
    assert report["score"] >= 90.0
    assert report["metrics"]["rooms_count"] > 0
    assert report["metrics"]["exits_count"] > 0
    assert report["checks"]["connectivity"]["status"] == "pass"
    assert report["checks"]["exit_accessibility"]["status"] == "pass"


def test_isolated_room_detection():
    bad = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "r2", "type": "room", "x": 30, "z": 30, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 5},
            {"id": "ex1", "type": "exit", "x": 10, "z": 5},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 2.0, "kind": "corridor"},
            # r2 has no edges and cannot reach ex1
        ]
    }
    report = analyze_graph(bad)
    assert report["status"] == "critical"
    assert any(w["code"] == "ISOLATED_ROOM" and "r2" in w["elements"] for w in report["warnings"])
    assert report["checks"]["connectivity"]["status"] == "critical"
    assert "r2" in report["checks"]["connectivity"]["isolated_rooms"]


def test_no_exits_detection():
    no_ex = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 5},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
        ]
    }
    report = analyze_graph(no_ex)
    assert report["status"] == "critical"
    assert any(w["code"] == "NO_EXITS" for w in report["warnings"])


def test_disconnected_exit_detection():
    stranded_exit = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 5},
            {"id": "ex1", "type": "exit", "x": 10, "z": 5},
            {"id": "ex_stranded", "type": "exit", "x": 40, "z": 40},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 2.0, "kind": "corridor"},
        ]
    }
    report = analyze_graph(stranded_exit)
    assert any(w["code"] == "DISCONNECTED_EXIT" and "ex_stranded" in w["elements"] for w in report["warnings"])
    assert "ex_stranded" in report["checks"]["exit_accessibility"]["unreachable_exits"]


def test_self_loops_and_duplicate_edges():
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "r1", "to": "p1", "width": 1.5, "kind": "door"},  # duplicate
            {"from": "p1", "to": "p1", "width": 2.0, "kind": "corridor"},  # self-loop
            {"from": "p1", "to": "ex1", "width": 2.0, "kind": "corridor"},
        ]
    }
    report = analyze_graph(graph)
    assert any(w["code"] == "SELF_LOOP_EDGE" for w in report["warnings"])
    assert any(w["code"] == "DUPLICATE_EDGE" for w in report["warnings"])
    assert report["checks"]["self_loops"]["count"] == 1
    assert report["checks"]["duplicate_edges"]["count"] == 1


def test_zero_length_edge_detection():
    graph = {
        "nodes": [
            {"id": "p1", "type": "corridor", "x": 5.0, "z": 5.0},
            {"id": "p2", "type": "corridor", "x": 5.0, "z": 5.0},  # identical location
            {"id": "ex1", "type": "exit", "x": 10.0, "z": 5.0},
        ],
        "edges": [
            {"from": "p1", "to": "p2", "width": 2.0, "kind": "corridor"},
            {"from": "p2", "to": "ex1", "width": 2.0, "kind": "corridor"},
        ]
    }
    report = analyze_graph(graph)
    assert any(w["code"] == "ZERO_LENGTH_EDGE" for w in report["warnings"])
    assert report["checks"]["zero_length_edges"]["count"] >= 1


def test_suspicious_auto_links():
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 0, "z": 20},  # 20 metres away
            {"id": "ex1", "type": "exit", "x": 0, "z": 25},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door", "inferred": True, "source": "auto_connect"},
            {"from": "p1", "to": "ex1", "width": 2.0, "kind": "corridor", "inferred": False, "source": "model"},
        ]
    }
    report = analyze_graph(graph)
    assert any(w["code"] == "SUSPICIOUS_AUTO_LINK" for w in report["warnings"])
    assert len(report["inferred_edges"]) == 1
    assert report["inferred_edges"][0]["source"] == "auto_connect"


def test_implausible_widths_and_room_dimensions():
    graph = {
        "nodes": [
            {"id": "r_narrow", "type": "room", "x": 0, "z": 0, "w": 20, "d": 1, "people": 100},
            {"id": "p1", "type": "corridor", "x": 5, "z": 5},
            {"id": "ex1", "type": "exit", "x": 10, "z": 5},
        ],
        "edges": [
            {"from": "r_narrow", "to": "p1", "width": 0.4, "kind": "door"},  # narrow
            {"from": "p1", "to": "ex1", "width": 8.0, "kind": "corridor"},  # excessive width
        ]
    }
    report = analyze_graph(graph)
    codes = [w["code"] for w in report["warnings"]]
    assert "EXTREME_ASPECT_RATIO" in codes
    assert "EXTREME_DENSITY" in codes
    assert "NARROW_PASSAGE" in codes
    assert "EXCESSIVE_WIDTH" in codes


def test_repair_graph_fixes_common_issues():
    flawed = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 0.3, "kind": "door"},
            {"from": "r1", "to": "p1", "width": 1.4, "kind": "door"},
            {"from": "p1", "to": "p1", "width": 2.0, "kind": "corridor"},
            {"from": "p1", "to": "ex1", "width": 9.0, "kind": "corridor"},
        ]
    }
    before = analyze_graph(flawed)
    assert before["status"] != "pass"

    repaired, actions = repair_graph(flawed)
    assert len(actions) >= 2  # removed self-loop, deduplicated r1-p1
    assert len(repaired["edges"]) == 2

    after = analyze_graph(repaired)
    assert after["score"] > before["score"]
    assert after["checks"]["self_loops"]["count"] == 0
    assert after["checks"]["duplicate_edges"]["count"] == 0


def test_qa_api_endpoint(clean_building):
    client = TestClient(app)
    res = client.post("/qa", json={"building": clean_building})
    assert res.status_code == 200
    data = res.json()
    assert "score" in data
    assert "status" in data
    assert "checks" in data
    assert "warnings" in data
    assert "metrics" in data


def test_real_datasets_qa():
    # 1. IIT KGP Museum (Hand digitised)
    b_museum = json.loads((ROOT / "data/iit_kgp_museum.json").read_text(encoding="utf-8"))
    qa_museum = analyze_graph(b_museum)
    assert qa_museum["status"] == "pass"
    assert qa_museum["score"] == 100.0

    # 2. Lab Block
    b_lab = json.loads((ROOT / "data/lab_block.json").read_text(encoding="utf-8"))
    qa_lab = analyze_graph(b_lab)
    assert qa_lab["status"] == "pass"
    assert qa_lab["score"] == 100.0

    # 3. Bedrock vision output for IIT KGP Museum
    b_vis = json.loads((ROOT / "runs/vision_iit_kgp_museum_amazon-nova-pro-v1-0.json").read_text(encoding="utf-8"))
    qa_vis = analyze_graph(b_vis)
    assert "metrics" in qa_vis
    assert qa_vis["metrics"]["rooms_count"] == 12
    assert qa_vis["metrics"]["exits_count"] == 2


# =========================================================================
# Targeted Regression Tests for Audit Review Fixes
# =========================================================================

def test_repair_graph_preserves_narrow_physical_widths():
    """Repair must never silently widen narrow passages."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 0.45, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 1.2, "kind": "corridor"},
        ]
    }
    repaired, _ = repair_graph(graph)
    door_edge = next(e for e in repaired["edges"] if e["from"] == "r1" or e["to"] == "r1")
    assert door_edge["width"] == 0.45


def test_repair_graph_preserves_excessive_physical_widths():
    """Repair must never silently shrink wide physical passages."""
    graph = {
        "nodes": [
            {"id": "p1", "type": "corridor", "x": 0, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "p1", "to": "ex1", "width": 8.5, "kind": "corridor"},
        ]
    }
    repaired, _ = repair_graph(graph)
    assert repaired["edges"][0]["width"] == 8.5


def test_repair_graph_input_immutability():
    """repair_graph must not mutate the input dictionary."""
    graph = {
        "nodes": [
            {"id": "p1", "type": "corridor", "x": 0, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "p1", "to": "p1", "width": 1.5, "kind": "corridor"},
            {"from": "p1", "to": "ex1", "width": 1.5, "kind": "corridor"},
        ]
    }
    snapshot = copy.deepcopy(graph)
    repaired, _ = repair_graph(graph)
    assert graph == snapshot
    assert len(repaired["edges"]) == 1


def test_deduplication_preserves_model_provenance_over_inferred():
    """Model-detected edges must take precedence over auto_connect links during deduplication."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door", "source": "model", "inferred": False},
            {"from": "r1", "to": "p1", "width": 2.0, "kind": "corridor", "source": "auto_connect", "inferred": True},
            {"from": "p1", "to": "ex1", "width": 2.0, "kind": "corridor", "source": "model", "inferred": False},
        ]
    }
    repaired, _ = repair_graph(graph)
    dedup = next(e for e in repaired["edges"] if set([e["from"], e["to"]]) == {"r1", "p1"})
    assert dedup["source"] == "model"
    assert dedup["kind"] == "door"
    assert dedup["width"] == 1.2


def test_deduplication_preserves_kind_hierarchy():
    """Hierarchy stair > door > corridor must be preserved when deduplicating."""
    graph = {
        "nodes": [
            {"id": "p1", "type": "corridor", "x": 0, "z": 0},
            {"id": "ex1", "type": "exit", "x": 5, "z": 0},
        ],
        "edges": [
            {"from": "p1", "to": "ex1", "width": 1.5, "kind": "door", "source": "model"},
            {"from": "p1", "to": "ex1", "width": 1.5, "kind": "stair", "source": "model"},
        ]
    }
    repaired, _ = repair_graph(graph)
    assert len(repaired["edges"]) == 1
    assert repaired["edges"][0]["kind"] == "stair"


def test_deduplication_handles_reversed_endpoints():
    """Edges (u, v) and (v, u) must be recognized as duplicate parallel links."""
    graph = {
        "nodes": [
            {"id": "p1", "type": "corridor", "x": 0, "z": 0},
            {"id": "p2", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "p1", "to": "p2", "width": 1.5, "kind": "corridor"},
            {"from": "p2", "to": "p1", "width": 1.8, "kind": "corridor"},
            {"from": "p2", "to": "ex1", "width": 1.5, "kind": "corridor"},
        ]
    }
    repaired, actions = repair_graph(graph)
    assert len(repaired["edges"]) == 2
    dedup = next(e for e in repaired["edges"] if set([e["from"], e["to"]]) == {"p1", "p2"})
    assert dedup["width"] == 1.8
    assert any("Deduplicated parallel edge between" in a for a in actions)


def test_conflicting_duplicate_metadata_preserved_and_noted():
    """Custom attributes must not be discarded when merging duplicate edges."""
    graph = {
        "nodes": [
            {"id": "p1", "type": "corridor", "x": 0, "z": 0},
            {"id": "ex1", "type": "exit", "x": 5, "z": 0},
        ],
        "edges": [
            {"from": "p1", "to": "ex1", "width": 1.2, "kind": "door", "source": "model", "fire_rating": "30min"},
            {"from": "p1", "to": "ex1", "width": 2.2, "kind": "door", "source": "auto_connect", "wheelchair": True},
        ]
    }
    repaired, actions = repair_graph(graph)
    edge = repaired["edges"][0]
    assert edge["fire_rating"] == "30min"
    assert edge["wheelchair"] is True
    assert any("noted width discrepancy" in a for a in actions)


def test_exit_to_corridor_door_diagnostics_and_10m_threshold():
    """Exit-to-corridor door links must use 10m threshold and clear wording without 'from room boundary'."""
    # Sub-10m: normal exit to corridor (e.g. 7.5 m)
    graph_normal = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 12.5, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "ex1", "to": "p1", "width": 1.5, "kind": "door"},
        ]
    }
    report_normal = analyze_graph(graph_normal)
    assert not any(w["code"] == "SUSPICIOUS_DOOR_LENGTH" for w in report_normal["warnings"])

    # Over 10m: anomalous exit to corridor (e.g. 18.0 m)
    graph_long = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 23.0, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "ex1", "to": "p1", "width": 1.5, "kind": "door"},
        ]
    }
    report_long = analyze_graph(graph_long)
    door_warn = next(w for w in report_long["warnings"] if w["code"] == "SUSPICIOUS_DOOR_LENGTH")
    assert "Door link between exit 'ex1' and corridor point 'p1' spans 18.0 m" in door_warn["message"]
    assert "from room boundary" not in door_warn["message"]


def test_room_to_corridor_door_diagnostics_retain_5m_threshold_and_boundary_wording():
    """Room doors must measure from room perimeter with 5m threshold and specify 'from room boundary'."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 12, "z": 0},
            {"id": "ex1", "type": "exit", "x": 15, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 2.0, "kind": "corridor"},
        ]
    }
    report = analyze_graph(graph)
    door_warn = next(w for w in report["warnings"] if w["code"] == "SUSPICIOUS_DOOR_LENGTH")
    assert "Door link between 'r1' and 'p1' spans 7.0 m from room boundary" in door_warn["message"]


def test_historical_exits_added_fallback_and_precedence():
    """Historical vision graphs with exits_added must infer merge_exits, while explicit provenance takes precedence."""
    historical_graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "EXIT_MAIN", "type": "exit", "x": 10, "z": 0, "label": "Main exit"},
            {"id": "EXIT_1", "type": "exit", "x": 0, "z": 10, "label": "West steps"},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "EXIT_MAIN", "to": "p1", "width": 1.5, "kind": "door"},
            {"from": "EXIT_1", "to": "p1", "width": 1.5, "kind": "door"},
        ],
        "vision": {
            "exits_added": ["West steps"]
        }
    }
    report = analyze_graph(historical_graph)
    assert report["metrics"]["inferred_edges_count"] == 1
    assert report["metrics"]["provenance"]["merge_exits"] == 1
    inferred_edge = report["inferred_edges"][0]
    assert inferred_edge["source"] == "merge_exits"
    assert set([inferred_edge["from"], inferred_edge["to"]]) == {"EXIT_1", "p1"}

    # Explicit provenance takes precedence over historical fallback
    with_explicit = copy.deepcopy(historical_graph)
    with_explicit["edges"][2]["source"] = "model"
    with_explicit["edges"][2]["inferred"] = False
    report_explicit = analyze_graph(with_explicit)
    assert report_explicit["metrics"]["inferred_edges_count"] == 0
    assert report_explicit["metrics"]["provenance"]["model"] == 1
    assert report_explicit["metrics"]["provenance"]["merge_exits"] == 0


def test_existing_auto_links_fallback_preserved():
    """Historical auto_links fallback must continue to work."""
    historical_auto = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "p2", "type": "corridor", "x": 10, "z": 0},
            {"id": "ex1", "type": "exit", "x": 15, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "p1", "to": "p2", "width": 2.0, "kind": "corridor"},
            {"from": "p2", "to": "ex1", "width": 1.5, "kind": "door"},
        ],
        "vision": {
            "auto_links": ["p1-p2"]
        }
    }
    report = analyze_graph(historical_auto)
    assert report["metrics"]["inferred_edges_count"] == 1
    assert report["metrics"]["provenance"]["auto_connect"] == 1
    assert report["inferred_edges"][0]["source"] == "auto_connect"


# =========================================================================
# Exit Capacity & Minimum Exit Count Unit & Integration Tests
# =========================================================================

def test_exit_capacity_adequately_wide_small_occupancy():
    """One adequately wide exit (2.0 m door) for small occupant load (50 people) flows quickly."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 50},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 2.0, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 2.0, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    assert report["checks"]["exit_capacity"]["status"] == "pass"
    est_time = report["metrics"]["estimated_capacity_time_s"]
    assert est_time is not None and est_time <= 150.0
    assert not any(w["code"] == "INSUFFICIENT_EXIT_CAPACITY" for w in report["warnings"])


def test_exit_capacity_large_occupancy_exceeding_heuristic():
    """One narrow exit (1.2 m door) for 500 occupants requires > 150 s and triggers warning."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 500},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.2, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 1.2, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    assert report["checks"]["exit_capacity"]["status"] == "warning"
    assert any(w["code"] == "INSUFFICIENT_EXIT_CAPACITY" for w in report["warnings"])
    assert report["metrics"]["estimated_capacity_time_s"] > 150.0


def test_multiple_exits_sufficient_combined_capacity():
    """Multiple exits whose combined capacity is sufficient pass the 150 s heuristic."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 300},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": -5},
            {"id": "ex2", "type": "exit", "x": 10, "z": 5},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 2.5, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 1.5, "kind": "door"},
            {"from": "p1", "to": "ex2", "width": 1.5, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    assert report["checks"]["exit_capacity"]["status"] == "pass"
    assert report["metrics"]["estimated_capacity_time_s"] <= 150.0
    assert not any(w["code"] == "INSUFFICIENT_EXIT_CAPACITY" for w in report["warnings"])


def test_multiple_exits_insufficient_combined_capacity():
    """Multiple exits whose combined capacity is insufficient for 1000 people trigger warning."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 20, "d": 20, "people": 1000},
            {"id": "p1", "type": "corridor", "x": 10, "z": 0},
            {"id": "ex1", "type": "exit", "x": 15, "z": -5},
            {"id": "ex2", "type": "exit", "x": 15, "z": 5},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 2.5, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 1.2, "kind": "door"},
            {"from": "p1", "to": "ex2", "width": 1.2, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    assert report["checks"]["exit_capacity"]["status"] == "warning"
    assert any(w["code"] == "INSUFFICIENT_EXIT_CAPACITY" for w in report["warnings"])
    assert report["metrics"]["estimated_capacity_time_s"] > 150.0


def test_door_vs_stair_flow_capacity():
    """Stair exit capacity is strictly lower than door exit capacity of the same width (SFPE model)."""
    cap_door = exit_flow_capacity(1.5, "door")
    cap_stair = exit_flow_capacity(1.5, "stair")
    # Stair specific flow is 1.012 pps/m vs door 1.312 pps/m
    assert cap_door > cap_stair
    assert abs(cap_door - 1.5685) < 0.01
    assert abs(cap_stair - 1.2139) < 0.01


def test_boundary_layer_deductions_and_minimum_clamp():
    """Effective width subtracts boundary layer (0.3048 m for door) and clamps to 0.30 m minimum."""
    # 0.40 m width door: 0.40 - 0.3048 = 0.0952 m < 0.30 m -> clamps to 0.30 m
    cap_narrow = exit_flow_capacity(0.40, "door")
    assert abs(cap_narrow - 0.30 * (24 / 60 / 0.3048)) < 1e-4

    # 1.0 m width door: 1.0 - 0.3048 = 0.6952 m
    cap_std = exit_flow_capacity(1.0, "door")
    assert abs(cap_std - 0.6952 * (24 / 60 / 0.3048)) < 1e-4


def test_exit_with_no_connecting_edge():
    """Disconnected exit has capacity 0.0 and does not inflate aggregate capacity."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 50},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
            {"id": "ex_orphan", "type": "exit", "x": 50, "z": 50},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.5, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 1.5, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    assert report["metrics"]["per_exit_capacity_pps"]["ex_orphan"] == 0.0
    assert "ex_orphan" in report["checks"]["exit_accessibility"]["unreachable_exits"]


def test_exit_with_zero_or_invalid_width():
    """Non-positive or non-numeric exit edge width yields 0.0 capacity safely."""
    assert exit_flow_capacity(0.0, "door") == 0.0
    assert exit_flow_capacity(-1.5, "door") == 0.0
    assert exit_flow_capacity("invalid", "door") == 0.0
    assert exit_flow_capacity(None, "door") == 0.0


def test_graph_with_no_exits():
    """Graph with 0 exits returns 0 aggregate capacity and None estimated capacity time."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 50},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.5, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    assert report["status"] == "critical"
    assert report["metrics"]["aggregate_exit_capacity_pps"] == 0.0
    assert report["metrics"]["estimated_capacity_time_s"] is None


def test_missing_edge_kind_defaults_to_door():
    """Missing or unrecognized edge kind defaults to door flow parameters."""
    cap_missing = exit_flow_capacity(1.5, None)
    cap_door = exit_flow_capacity(1.5, "door")
    assert cap_missing == cap_door


def test_multiple_links_connected_to_single_exit():
    """An exit connected to two corridor branches sums capacity from both feeder links."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 100},
            {"id": "p_north", "type": "corridor", "x": 5, "z": -2},
            {"id": "p_south", "type": "corridor", "x": 5, "z": 2},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p_north", "width": 1.5, "kind": "corridor"},
            {"from": "r1", "to": "p_south", "width": 1.5, "kind": "corridor"},
            {"from": "p_north", "to": "ex1", "width": 1.5, "kind": "door"},
            {"from": "p_south", "to": "ex1", "width": 1.5, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    # ex1 has two 1.5m door links = 1.5685 * 2 = 3.137 pps
    assert abs(report["metrics"]["per_exit_capacity_pps"]["ex1"] - 3.14) < 0.02
    assert abs(report["metrics"]["aggregate_exit_capacity_pps"] - 3.14) < 0.02


def test_no_double_counting_between_exits():
    """An edge between two exits is not double-counted into exterior egress capacity."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 50},
            {"id": "p1", "type": "corridor", "x": 5, "z": 0},
            {"id": "ex1", "type": "exit", "x": 10, "z": 0},
            {"id": "ex2", "type": "exit", "x": 10, "z": 5},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 1.5, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 1.5, "kind": "door"},
            {"from": "ex1", "to": "ex2", "width": 2.0, "kind": "door"},  # inter-exit edge
        ]
    }
    report = analyze_graph(graph)
    # Only p1 -> ex1 should count in aggregate exterior capacity (1.5685 pps)
    assert abs(report["metrics"]["aggregate_exit_capacity_pps"] - 1.57) < 0.02


def test_sufficient_capacity_but_insufficient_exit_count():
    """Single wide exit (10.0 m) for 200 occupants has plenty of capacity but fails NBC minimum exit count."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 20, "d": 20, "people": 200},
            {"id": "p1", "type": "corridor", "x": 15, "z": 0},
            {"id": "ex1", "type": "exit", "x": 20, "z": 0},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 10.0, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 10.0, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    # Capacity is sufficient (estimated time ~15 s <= 150 s)
    assert report["checks"]["exit_capacity"]["status"] == "pass"
    assert not any(w["code"] == "INSUFFICIENT_EXIT_CAPACITY" for w in report["warnings"])

    # But exit count is 1 for 200 occupants -> triggers INSUFFICIENT_EXIT_COUNT (NBC 2016 Part 4)
    assert report["checks"]["exit_count"]["status"] == "warning"
    assert any(w["code"] == "INSUFFICIENT_EXIT_COUNT" for w in report["warnings"])


def test_sufficient_exit_count_but_insufficient_capacity():
    """3 narrow exits (0.6 m each) for 400 occupants satisfy exit count but fail capacity heuristic."""
    graph = {
        "nodes": [
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 20, "d": 20, "people": 400},
            {"id": "p1", "type": "corridor", "x": 10, "z": 0},
            {"id": "ex1", "type": "exit", "x": 15, "z": -5},
            {"id": "ex2", "type": "exit", "x": 15, "z": 0},
            {"id": "ex3", "type": "exit", "x": 15, "z": 5},
        ],
        "edges": [
            {"from": "r1", "to": "p1", "width": 2.0, "kind": "door"},
            {"from": "p1", "to": "ex1", "width": 0.6, "kind": "door"},
            {"from": "p1", "to": "ex2", "width": 0.6, "kind": "door"},
            {"from": "p1", "to": "ex3", "width": 0.6, "kind": "door"},
        ]
    }
    report = analyze_graph(graph)
    # Exit count is 3 -> passes exit count check
    assert report["checks"]["exit_count"]["status"] == "pass"
    assert not any(w["code"] == "INSUFFICIENT_EXIT_COUNT" for w in report["warnings"])

    # Aggregate capacity is 3 * 0.39 pps = 1.18 pps -> est time = 400 / 1.18 = 339 s > 150 s -> warning
    assert report["checks"]["exit_capacity"]["status"] == "warning"
    assert any(w["code"] == "INSUFFICIENT_EXIT_CAPACITY" for w in report["warnings"])


def test_canonical_graphs_satisfy_exit_adequacy():
    """All canonical hand-grounded benchmark buildings satisfy the 150 s flow heuristic and NBC exit count."""
    for filename in ["data/sample_floor.json", "data/lab_block.json", "data/iit_kgp_museum.json"]:
        b = json.loads((ROOT / filename).read_text(encoding="utf-8"))
        report = analyze_graph(b)
        assert report["status"] == "pass"
        assert report["score"] == 100.0
        assert report["checks"]["exit_capacity"]["status"] == "pass"
        assert report["checks"]["exit_count"]["status"] == "pass"
        assert report["metrics"]["estimated_capacity_time_s"] <= 150.0
        assert report["checks"]["exit_count"]["accessible_exits"] >= 2


def test_historical_nova_pro_detects_exit_inadequacy():
    """Nova-Pro graph in web/public/data/vision_nova_pro.json triggers both insufficient exit count and capacity."""
    path = ROOT / "web/public/data/vision_nova_pro.json"
    if path.exists():
        b = json.loads(path.read_text(encoding="utf-8"))
        report = analyze_graph(b)
        # Only 1 exit for 671 people
        assert any(w["code"] == "INSUFFICIENT_EXIT_COUNT" for w in report["warnings"])
        assert any(w["code"] == "INSUFFICIENT_EXIT_CAPACITY" for w in report["warnings"])
        assert report["checks"]["exit_count"]["status"] == "warning"
        assert report["checks"]["exit_capacity"]["status"] == "warning"
        assert report["metrics"]["estimated_capacity_time_s"] > 150.0
