"""Crowd density analysis — crush-risk detection.

Computes people per m² on each corridor/door edge over time from a simulate() result.
Thresholds from docs/CROWD_RESEARCH.md (G. Keith Still; UK Green Guide).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import NamedTuple


CRUSH_THRESHOLD = 4.0    # p/m²  — crowd forces can reach fatal levels (G.K. Still)
CONCERN_THRESHOLD = 2.7  # p/m²  — LoS E boundary; UK Green Guide cap for stadia


def _edge_area(edge_id: str, building: dict) -> float:
    """Return the floor area (m²) of an edge: length × effective width.

    effective_width = clear_width − 2 × boundary_layer
    Boundary layers (SFPE): door 0.152 m, corridor 0.20 m, stair 0.15 m.
    Falls back to clear_width when kind is unknown.
    """
    nodes = {n["id"]: n for n in building["nodes"]}
    # edge_id is "from-to"
    parts = edge_id.split("-", 1)
    if len(parts) != 2:
        # try splitting differently for ids that contain "-"
        # find the edge by scanning
        pass

    # locate the edge in the building
    edge = None
    for e in building["edges"]:
        if f"{e['from']}-{e['to']}" == edge_id or f"{e['to']}-{e['from']}" == edge_id:
            edge = e
            break
    if edge is None:
        return 1.0  # unknown edge: 1 m² avoids division-by-zero

    kind = edge.get("kind", "corridor")
    # default kind logic matching sim.py
    from_node = nodes.get(edge["from"], {})
    to_node = nodes.get(edge["to"], {})
    if from_node.get("type") == "room" or to_node.get("type") == "room":
        kind = edge.get("kind", "door")
    else:
        kind = edge.get("kind", "corridor")

    boundary = {"door": 0.152, "corridor": 0.20, "stair": 0.15}.get(kind, 0.15)
    eff_width = max(0.3, edge["width"] - 2 * boundary)

    # length: explicit or straight-line distance
    if "length" in edge:
        length = edge["length"]
    else:
        fn, tn = nodes.get(edge["from"]), nodes.get(edge["to"])
        if fn and tn:
            length = math.hypot(fn["x"] - tn["x"], fn["z"] - tn["z"])
        else:
            length = 1.0

    return max(0.1, eff_width * length)


@dataclass
class EdgeDensityRecord:
    edge_id: str
    peak_density: float           # p/m² peak over all frames
    peak_time: float              # t (s) when peak occurred
    crush_risk: list = field(default_factory=list)   # [{t, density, level}]


class CrushRiskEntry(NamedTuple):
    edge_id: str
    t: float
    density: float
    level: str   # "concern" | "crush"


def analyse(sim_result: dict, building: dict) -> dict:
    """Compute crowd density from a simulate() result.

    Parameters
    ----------
    sim_result : dict   Output of POST /simulate (with "edge_load" and "frames").
    building   : dict   The building JSON passed to /simulate.

    Returns
    -------
    dict with:
      "edge_density"  : {edge_id: {"area_m2", "peak_density", "peak_t"}}
      "crush_risk"    : list of {edge_id, t, density, level}   (sorted by t, then density desc)
      "max_density"   : float   — highest single density seen anywhere
      "worst_edge"    : str     — edge_id with highest peak density
    """
    frames = sim_result.get("frames", [])
    edge_load = sim_result.get("edge_load", {})

    # Build area cache for all edges in the building
    area_cache: dict[str, float] = {}
    for e in building["edges"]:
        eid = f"{e['from']}-{e['to']}"
        area_cache[eid] = _edge_area(eid, building)

    # Track per-edge density over time
    # edge_load gives PEAK queue counts (not per-frame), so for per-frame density
    # we use people counts near each edge from frames.
    # For a simpler but valid approximation: distribute the queuing people to edges
    # proportionally.  For a precise method we need per-frame edge counts.
    #
    # The frames give [x, z, state] for each person.  Map each person position to the
    # nearest edge by matching their (x,z) to corridor nodes in the building.
    # This is an approximation consistent with the simulator's "hydraulic" model.

    nodes = {n["id"]: n for n in building["nodes"]}
    edges = building["edges"]

    # Build lookup: for each edge, compute its midpoint
    def midpoint(e):
        fn, tn = nodes.get(e["from"]), nodes.get(e["to"])
        if fn and tn:
            return ((fn["x"] + tn["x"]) / 2, (fn["z"] + tn["z"]) / 2)
        return (0.0, 0.0)

    edge_mids = {f"{e['from']}-{e['to']}": midpoint(e) for e in edges}

    # Per-frame density per edge
    per_edge: dict[str, list[float]] = {eid: [] for eid in area_cache}
    frame_times: list[float] = []

    for frame in frames:
        t = frame["t"]
        frame_times.append(t)
        # count queuing/walking people near each edge
        counts: dict[str, int] = {eid: 0 for eid in area_cache}
        for (px, pz, st) in frame["people"]:
            if st in ("out", "inside"):
                continue
            # assign this person to nearest edge
            best_eid, best_d = None, float("inf")
            for eid, (mx, mz) in edge_mids.items():
                if eid not in counts:
                    continue
                d = math.hypot(px - mx, pz - mz)
                if d < best_d:
                    best_d = d
                    best_eid = eid
            if best_eid:
                counts[best_eid] += 1
        for eid in counts:
            area = area_cache.get(eid, 1.0)
            density = counts[eid] / area
            per_edge[eid].append(density)

    # Compute peak per edge and crush_risk entries
    crush_risk: list[dict] = []
    edge_density: dict[str, dict] = {}
    max_density = 0.0
    worst_edge = ""

    for eid, densities in per_edge.items():
        if not densities:
            continue
        peak = max(densities)
        peak_t = frame_times[densities.index(peak)] if frame_times else 0.0
        area = area_cache.get(eid, 1.0)
        edge_density[eid] = {
            "area_m2": round(area, 2),
            "peak_density": round(peak, 2),
            "peak_t": peak_t,
        }
        if peak > max_density:
            max_density = peak
            worst_edge = eid
        # collect risk entries per frame
        for i, d in enumerate(densities):
            if d >= CRUSH_THRESHOLD:
                crush_risk.append({"edge_id": eid, "t": frame_times[i], "density": round(d, 2), "level": "crush"})
            elif d >= CONCERN_THRESHOLD:
                crush_risk.append({"edge_id": eid, "t": frame_times[i], "density": round(d, 2), "level": "concern"})

    crush_risk.sort(key=lambda x: (x["t"], -x["density"]))

    return {
        "edge_density": edge_density,
        "crush_risk": crush_risk,
        "max_density": round(max_density, 2),
        "worst_edge": worst_edge,
        "thresholds": {
            "concern": CONCERN_THRESHOLD,
            "crush": CRUSH_THRESHOLD,
        },
    }
