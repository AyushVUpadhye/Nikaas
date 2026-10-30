"""Evacuation simulator: people walk shortest paths to their assigned exit; every edge
admits at most width x specific-flow people per second (a queue forms in front of it).

Model: flow-limited network ("hydraulic" egress model), the standard engineering method in
SFPE Handbook of Fire Protection Engineering, Ch. "Emergency Movement" (Gwynne & Rosenbaum).
Constants below are the handbook's commonly quoted maxima; they are inputs, not tuned results.
"""
import math
import random
from dataclasses import dataclass

from .building import Building, shortest_path

WALK_SPEED = 1.19  # m/s, unimpeded horizontal walking (SFPE)
STAIR_SPEED = 0.85  # m/s along the stair slope (SFPE, typical riser/tread)
SPECIFIC_FLOW = {"corridor": 1.3, "door": 1.3, "stair": 1.1}  # persons / s / m of clear width (SFPE max)
DT = 0.25  # s


@dataclass
class Person:
    pid: int
    room: str
    exit: str
    path: list  # node ids, room ... exit
    leg: int = 0  # index of the edge being walked (path[leg] -> path[leg+1])
    s: float = 0.0  # metres walked on current edge
    state: str = "inside"  # inside | walking | queuing | stairs | out
    start: float = 0.0  # pre-movement delay, s
    ox: float = 0.0  # spawn offset inside the room
    oz: float = 0.0
    t_out: float = math.nan


def simulate(b: Building, plan: dict, blocked=(), seed=7, max_t=1800.0, frame_every=1.0, premove=(0.0, 0.0)):
    """Run one evacuation. plan: room -> exit. Returns a dict in the API contract shape."""
    rng = random.Random(seed)
    blocked = set(blocked)
    edge_of = {}
    for e in b.edges:
        edge_of[(e.a, e.b)] = e
        edge_of[(e.b, e.a)] = e
    people, pid = [], 0
    for room, n in b.people().items():
        ex = plan[room]
        if ex in blocked:
            raise ValueError(f"plan sends {room} to blocked exit {ex}")
        _, path = shortest_path(b, room, ex, blocked)
        if not path:
            raise ValueError(f"no route from {room} to {ex}")
        node = b.nodes[room]
        for _ in range(n):
            people.append(Person(pid, room, ex, path, start=rng.uniform(*premove),
                                 ox=(rng.random() - .5) * node.get("w", 4) * .8,
                                 oz=(rng.random() - .5) * node.get("d", 4) * .8))
            pid += 1

    cap = {e.key: e.width * SPECIFIC_FLOW[e.kind] for e in b.edges}  # persons / s
    credit = {k: 0.0 for k in cap}
    queues = {k: [] for k in cap}  # FIFO of person ids waiting to enter the edge
    peak_q = {k: 0 for k in cap}
    exit_count = {x: 0 for x in b.exits}
    frames, t, next_frame = [], 0.0, 0.0

    def pos(p):
        if p.state == "inside":
            n = b.nodes[p.room]
            return n["x"] + p.ox, n["z"] + p.oz
        a, c = b.nodes[p.path[p.leg]], b.nodes[p.path[min(p.leg + 1, len(p.path) - 1)]]
        e = edge_of[(p.path[p.leg], p.path[min(p.leg + 1, len(p.path) - 1)])] if p.leg + 1 < len(p.path) else None
        f = 0.0 if not e else min(1.0, p.s / e.length)
        return a["x"] + (c["x"] - a["x"]) * f, a["z"] + (c["z"] - a["z"]) * f

    def want_edge(p):
        k = edge_of[(p.path[p.leg], p.path[p.leg + 1])].key
        if p.pid not in queues[k]:
            queues[k].append(p.pid)
        p.state = "queuing"

    while t <= max_t:
        # 1) people whose pre-movement ended join the queue of their first edge
        for p in people:
            if p.state == "inside" and t >= p.start:
                want_edge(p)
        # 2) each edge admits people at its flow capacity
        for k, q in queues.items():
            credit[k] += cap[k] * DT  # leftover capacity carries over; clamped below only when idle
            while q and credit[k] >= 1.0:
                credit[k] -= 1.0
                p = people[q.pop(0)]
                e = edge_of[(p.path[p.leg], p.path[p.leg + 1])]
                p.state, p.s = ("stairs" if e.kind == "stair" else "walking"), 0.0
            if not q:
                credit[k] = min(credit[k], 1.0)
            peak_q[k] = max(peak_q[k], len(q))
        # 3) walkers advance; at the end of an edge they reach a node
        for p in people:
            if p.state not in ("walking", "stairs"):
                continue
            e = edge_of[(p.path[p.leg], p.path[p.leg + 1])]
            p.s += (STAIR_SPEED if e.kind == "stair" else WALK_SPEED) * DT
            if p.s >= e.length:
                p.leg += 1
                if p.leg == len(p.path) - 1:  # reached the exit node
                    p.state, p.t_out = "out", t + DT
                    exit_count[p.exit] += 1
                else:
                    want_edge(p)
        t += DT
        if t >= next_frame:
            frames.append({"t": round(t, 2), "people": [[round(x, 2), round(z, 2), p.state] for p in people for x, z in [pos(p)]]})
            next_frame += frame_every
        if all(p.state == "out" for p in people):
            break

    done = all(p.state == "out" for p in people)
    bottleneck = max(peak_q, key=peak_q.get) if peak_q else None
    return {
        "total_time_s": round(max(p.t_out for p in people), 2) if done and people else None,
        "completed": done,
        "people": len(people),
        "per_exit": exit_count,
        "bottleneck": bottleneck,
        "peak_queue": peak_q.get(bottleneck, 0) if bottleneck else 0,
        "edge_load": {k: v for k, v in sorted(peak_q.items(), key=lambda kv: -kv[1])},  # peak queue per edge, busiest first
        "frames": frames,
    }
