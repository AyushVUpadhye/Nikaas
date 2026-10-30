"""Live drill: one shared evacuation state that a presenter controls and every phone in the room follows.

The presenter starts a drill on a building and blocks exits; the optimiser re-plans; each phone polls the state
for its own room and gets a personal instruction (exit, walking distance, walking time) plus an alert when its
exit changes. State lives in memory locally, or in one S3 object when NIKAAS_DRILL_BUCKET is set (Lambda
instances do not share memory).
"""
import json
import os
import time

from .building import Building, load, shortest_path
from .optimise import optimise
from .sim import WALK_SPEED, door_paths

KEY = "drill/state.json"
_memory: dict = {}


def _store():
    bucket = os.environ.get("NIKAAS_DRILL_BUCKET")
    if not bucket:
        return None
    import boto3  # available on Lambda; not needed locally

    return boto3.client("s3"), bucket


def save(state: dict) -> None:
    s = _store()
    if s is None:
        _memory["state"] = state
        return
    client, bucket = s
    client.put_object(Bucket=bucket, Key=KEY, Body=json.dumps(state).encode(), ContentType="application/json",
                      CacheControl="no-cache")


def read() -> dict | None:
    s = _store()
    if s is None:
        return _memory.get("state")
    client, bucket = s
    try:
        return json.loads(client.get_object(Bucket=bucket, Key=KEY)["Body"].read())
    except client.exceptions.NoSuchKey:
        return None


def _instructions(b: Building, plan: dict, blocked: set) -> dict:
    """room -> {exit, exit_label, distance_m, walk_s, path}: shortest route through the room's best door."""
    out = {}
    for room, ex in plan.items():
        routes = door_paths(b, room, ex, blocked)
        if not routes:
            continue
        best = min((sum(e.length for u, v in zip(p, p[1:]) for nb, e in b.adj[u] if nb == v), p) for _, p in routes)
        dist, path = best
        out[room] = {"exit": ex, "exit_label": b.nodes[ex].get("label", ex), "distance_m": round(dist, 1),
                     "walk_s": round(dist / WALK_SPEED), "path": path}
    return out


def start(building: dict, blocked: list[str], previous: dict | None = None) -> dict:
    """Plan the building with the given exits blocked and publish it as the new drill state."""
    b = load(building)
    blocked_set = set(blocked)
    opt = optimise(b, blocked_set)
    rooms = _instructions(b, opt["plan"], blocked_set)
    old = (previous or {}).get("rooms", {})
    changed = sorted(r for r, x in rooms.items() if r in old and old[r]["exit"] != x["exit"])
    state = {
        "version": (previous or {}).get("version", 0) + 1,
        "updated_at": time.time(),
        "building_name": building.get("name", "building"),
        "blocked": sorted(blocked_set),
        "blocked_labels": [b.nodes[x].get("label", x) for x in sorted(blocked_set)],
        "total_time_s": opt["total_time_s"],
        "room_labels": {r: b.nodes[r].get("label", r) for r in b.rooms},
        "exit_labels": {x: b.nodes[x].get("label", x) for x in b.exits},  # for the phones taped by each door
        "rooms": rooms,
        # the sign at a blocked door points to the open exit with the shortest walk from that door
        "instead": {x: min((shortest_path(b, x, y, blocked_set)[0], y) for y in b.exits if y not in blocked_set)[1]
                    for x in sorted(blocked_set) if len(blocked_set) < len(b.exits)},
        "changed": changed,  # rooms whose exit just changed: their phones alert
        # small map for the phones: node positions/sizes and walkways (a few KB)
        "map": {"nodes": [[n["id"], n["type"], n["x"], n["z"], n.get("w", 0), n.get("d", 0)] for n in building["nodes"]],
                "edges": [[e["from"], e["to"]] for e in building["edges"]]},
    }
    save(state)
    return state
