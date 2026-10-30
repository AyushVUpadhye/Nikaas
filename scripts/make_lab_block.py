"""Generate data/lab_block.json: a REPRESENTATIVE engineering-college lab floor (L-shaped block,
two wings, three stairs). Not measured from any real building; occupancies and widths are
assumptions listed in docs/QUESTIONS.md. Replace with the real map when it is digitised."""
import json
from pathlib import Path

nodes, edges = [], []


def room(rid, x, z, w, d, people, door_to, door_w=1.0):
    nodes.append({"id": rid, "type": "room", "x": x, "z": z, "w": w, "d": d, "people": people})
    edges.append({"from": rid, "to": door_to, "width": door_w})


def cor(cid, x, z):
    nodes.append({"id": cid, "type": "corridor", "x": x, "z": z})


def link(a, b, w, kind=None):
    e = {"from": a, "to": b, "width": w}
    if kind:
        e["kind"] = kind
    edges.append(e)


# main wing: corridor along x at z = 0, 2.4 m wide, from x = -36 to x = 30
main = [-34, -26, -18, -10, -2, 6, 14, 22, 30]
for x in main:
    cor(f"m{x}", x, 0)
for a, b in zip(main, main[1:]):
    link(f"m{a}", f"m{b}", 2.4)
# side wing: corridor along z at x = 30, from z = 0 to z = 34
side = [8, 16, 24, 32]
for z in side:
    cor(f"s{z}", 30, z)
link("m30", "s8", 2.4)
for a, b in zip(side, side[1:]):
    link(f"s{a}", f"s{b}", 2.0)

# north of main wing (z < 0): five labs
for i, x in enumerate([-30, -18, -6, 6, 18], 1):
    room(f"lab{i}", x, -6.5, 11, 9, 42, f"m{min(main, key=lambda m: abs(m - x))}")
# south of main wing (z > 0)
room("hod", -32, 5, 6, 6, 4, "m-34")
room("faculty", -24, 5.5, 10, 7, 14, "m-26")
room("seminar", -6, 8, 18, 12, 120, "m-10", door_w=1.6)
link("seminar", "m-2", 1.6)  # seminar hall has two doors
room("lab6", 10, 6, 10, 8, 40, "m6")
room("wc", 21, 4.5, 6, 5, 6, "m22")
# side wing rooms
room("lab7", 37, 10, 10, 8, 40, "s8")
room("lab8", 37, 22, 10, 9, 40, "s24")
room("project", 23, 17, 8, 10, 24, "s16")
room("library", 23, 30, 8, 8, 30, "s32")

# exits: three stairs
nodes += [{"id": "A", "type": "exit", "x": -40, "z": 0, "label": "Stair A (west)"},
          {"id": "B", "type": "exit", "x": 30, "z": -5, "label": "Stair B (main, junction)"},
          {"id": "C", "type": "exit", "x": 30, "z": 38, "label": "Stair C (side wing end)"}]
link("m-34", "A", 1.2, "stair")
link("m30", "B", 2.0, "stair")
link("s32", "C", 1.2, "stair")

out = {"name": "Representative lab block (L-shaped, 2 wings, 3 stairs) - NOT a measured building",
       "units": "m", "nodes": nodes, "edges": edges}
Path("data/lab_block.json").write_text(json.dumps(out, indent=1))
print(len(nodes), "nodes", len(edges), "edges", sum(n.get("people", 0) for n in nodes), "people")
