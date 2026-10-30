"""Building graph: load the shared JSON contract, shortest paths, nearest-exit plan."""
import heapq
import json
import math
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Edge:
    a: str
    b: str
    width: float  # metres of clear width
    length: float  # metres
    kind: str = "corridor"  # corridor | door | stair

    @property
    def key(self):
        return f"{self.a}-{self.b}"


@dataclass
class Building:
    name: str
    nodes: dict  # id -> node dict (type, x, z, ...)
    edges: list
    adj: dict = field(default_factory=dict)  # id -> [(neighbour, Edge)]

    @property
    def rooms(self):
        return [n for n, v in self.nodes.items() if v["type"] == "room"]

    @property
    def exits(self):
        return [n for n, v in self.nodes.items() if v["type"] == "exit"]

    def people(self):
        return {r: int(self.nodes[r].get("people", 0)) for r in self.rooms}


def validate(d):
    """Check a building dict against docs/CONTRACT.md. Returns a list of human-readable problems (empty = OK).
    Used on anything that did not come from our own files: vision output, editor saves, API calls."""
    probs = []
    if not isinstance(d, dict) or "nodes" not in d or "edges" not in d:
        return ["building must be an object with 'nodes' and 'edges'"]
    ids = [n.get("id") for n in d["nodes"]]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        probs.append(f"duplicate node ids: {sorted(dup)}")
    nodes = {n.get("id"): n for n in d["nodes"]}
    for n in d["nodes"]:
        if n.get("type") not in ("room", "corridor", "exit"):
            probs.append(f"node {n.get('id')}: type must be room, corridor or exit")
        if not all(isinstance(n.get(k), (int, float)) for k in ("x", "z")):
            probs.append(f"node {n.get('id')}: x and z must be numbers (metres)")
        if n.get("type") == "room" and not (isinstance(n.get("people", 0), int) and n.get("people", 0) >= 0):
            probs.append(f"room {n.get('id')}: people must be a whole number >= 0")
    for i, e in enumerate(d["edges"]):
        for end in ("from", "to"):
            if e.get(end) not in nodes:
                probs.append(f"edge {i}: unknown node '{e.get(end)}'")
        if not (isinstance(e.get("width"), (int, float)) and e["width"] > 0):
            probs.append(f"edge {e.get('from')}-{e.get('to')}: width must be > 0 m")
        if e.get("kind") not in (None, "door", "corridor", "stair"):
            probs.append(f"edge {e.get('from')}-{e.get('to')}: kind must be door, corridor or stair")
    if not any(n.get("type") == "exit" for n in d["nodes"]):
        probs.append("building has no exit")
    if probs:
        return probs
    b = load(d)
    for r in b.rooms:
        if not any(shortest_path(b, r, x)[1] for x in b.exits):
            probs.append(f"room {r} cannot reach any exit")
    return probs


def load(src):
    """src: path or already-parsed dict in the contract format (see docs/CONTRACT.md)."""
    d = json.loads(Path(src).read_text(encoding="utf-8")) if not isinstance(src, dict) else src
    nodes = {n["id"]: n for n in d["nodes"]}
    edges, adj = [], {n: [] for n in nodes}
    for e in d["edges"]:
        a, b = nodes[e["from"]], nodes[e["to"]]
        length = e.get("length") or math.hypot(a["x"] - b["x"], a["z"] - b["z"])
        kind = e.get("kind") or ("door" if "room" in (a["type"], b["type"]) else "corridor")
        ed = Edge(e["from"], e["to"], float(e["width"]), float(length), kind)
        edges.append(ed)
        adj[ed.a].append((ed.b, ed))
        adj[ed.b].append((ed.a, ed))
    return Building(d.get("name", "building"), nodes, edges, adj)


def shortest_path(b, src, dst, blocked=()):
    """Dijkstra on edge length. Returns (distance, [node ids]) or (inf, []) if unreachable."""
    dist, prev, pq = {src: 0.0}, {}, [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == dst:
            break
        if d > dist.get(u, math.inf):
            continue
        for v, e in b.adj[u]:
            if v in blocked:
                continue
            nd = d + e.length
            if nd < dist.get(v, math.inf):
                dist[v], prev[v] = nd, u
                heapq.heappush(pq, (nd, v))
    if dst not in dist:
        return math.inf, []
    path, n = [dst], dst
    while n != src:
        n = prev[n]
        path.append(n)
    return dist[dst], path[::-1]


def nearest_plan(b, blocked=()):
    """Today's rule: every room goes to its closest open exit."""
    plan = {}
    for r in b.rooms:
        best = min(((shortest_path(b, r, x, blocked)[0], x) for x in b.exits if x not in blocked), default=(math.inf, None))
        if best[1] is None:
            raise ValueError(f"room {r} has no reachable open exit")
        plan[r] = best[1]
    return plan
