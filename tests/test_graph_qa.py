"""Tests for Graph Quality Analysis (QA) and Auto-Repair Engine."""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nikaas.api import app
from nikaas.graph_qa import analyze_graph, repair_graph

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
    assert qa_museum["status"] in ("pass", "warning")
    assert qa_museum["score"] >= 80.0

    # 2. Lab Block
    b_lab = json.loads((ROOT / "data/lab_block.json").read_text(encoding="utf-8"))
    qa_lab = analyze_graph(b_lab)
    assert qa_lab["status"] == "pass"
    assert qa_lab["score"] >= 90.0

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
    assert dedup["width"] == 1.2  # inferred width 2.0 does not overwrite model's 1.2


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
            {"id": "ex1", "type": "exit", "x": 12.5, "z": 0},  # 7.5 m from p1
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
            {"id": "ex1", "type": "exit", "x": 23.0, "z": 0},  # 18.0 m from p1
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
            {"id": "r1", "type": "room", "x": 0, "z": 0, "w": 10, "d": 10, "people": 10},  # boundary at x=5
            {"id": "p1", "type": "corridor", "x": 12, "z": 0},  # 7 m from room perimeter
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
            {"from": "EXIT_1", "to": "p1", "width": 1.5, "kind": "door"},  # historical exit link
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
