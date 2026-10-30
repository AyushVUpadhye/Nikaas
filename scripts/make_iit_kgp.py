"""Digitise the IIT Kharagpur NMST Block-B floor-plan panel (data/maps/iit_kgp_nmst_block_b.jpg)
into data/iit_kgp_museum.json. Layout read by hand from the photo; pixel positions converted to
metres at 0.06 m/px (panel has no scale bar, so overall size ~80 m is an assumption).
Occupancy, widths and which openings are exits are assumptions (see docs/QUESTIONS.md).
Photo: Biswarup Ganguly, CC BY 3.0, via Wikimedia Commons."""
import json
from pathlib import Path

S = 0.06
P = lambda px, py: (round((px - 260) * S, 1), round((py - 150) * S, 1))
nodes, edges = [], []


def room(rid, px, py, w, d, people, label):
    x, z = P(px, py)
    nodes.append({"id": rid, "type": "room", "x": x, "z": z, "w": w, "d": d, "people": people, "label": label})


def cor(cid, px, py):
    x, z = P(px, py)
    nodes.append({"id": cid, "type": "corridor", "x": x, "z": z})


def exit_(eid, px, py, label):
    x, z = P(px, py)
    nodes.append({"id": eid, "type": "exit", "x": x, "z": z, "label": label})


def e(a, b, w, kind=None):
    d = {"from": a, "to": b, "width": w}
    if kind:
        d["kind"] = kind
    edges.append(d)


# rooms (label as printed on the panel)
room("machine", 1330, 230, 26, 5, 40, "Machine, Motion, Light and Sound")
room("mechanics", 1140, 400, 9, 13, 35, "Principles of Mechanics")
room("electricity", 1300, 400, 9, 12, 35, "Electricity and Magnetics")
room("maths", 1500, 420, 7, 13, 30, "Mathematics Gallery")
room("reception", 1500, 640, 8, 7, 15, "Reception")
room("office", 1355, 600, 6, 10, 8, "Office")
room("rail", 1210, 600, 9, 9, 40, "Rail Transport in India")
room("water", 1085, 600, 4, 9, 25, "Water Transport Gallery")
room("aviation", 975, 600, 6, 9, 35, "Aviation and Space")
room("computing", 870, 600, 6, 9, 35, "Computing Machines")
room("taramandal", 700, 580, 11, 9, 60, "Taramandal")
room("study", 550, 720, 4, 7, 15, "Study")
room("avhall", 420, 700, 10, 7, 120, "Audiovisual Hall")
room("washroom", 360, 820, 7, 3, 10, "Washroom / Drinking water")
room("guest", 560, 830, 4, 4, 4, "Guest Room")

# circulation (gallery route shown by arrows on the panel)
for cid, px, py in [("g1540", 1540, 680), ("r440", 1540, 440), ("r250", 1540, 250), ("u500", 1270, 500),
                    ("g1420", 1420, 680), ("g1270", 1270, 680), ("g1130", 1130, 680), ("g1030", 1030, 680),
                    ("g920", 920, 680), ("g820", 820, 680), ("g640", 640, 680), ("w770", 550, 770), ("w860", 420, 860)]:
    cor(cid, px, py)
exit_("MAIN", 1590, 715, "Main entrance (by Reception)")
exit_("WEST", 420, 895, "West steps")
exit_("VER", 820, 740, "Verandah door")

# gallery spine, right corridor, upper block
for a, b in [("g1540", "g1420"), ("g1420", "g1270"), ("g1270", "g1130"), ("g1130", "g1030"), ("g1030", "g920"),
             ("g920", "g820"), ("g820", "g640"), ("g640", "w770"), ("w770", "w860")]:
    e(a, b, 2.5)
e("g1540", "r440", 2.0); e("r440", "r250", 2.0); e("g1270", "u500", 2.0)
# room doors
for r, c, w in [("machine", "r250", 1.5), ("maths", "r440", 1.5), ("mechanics", "u500", 1.5), ("electricity", "u500", 1.5),
                ("reception", "g1540", 2.0), ("office", "g1420", 1.0), ("rail", "g1270", 1.5), ("water", "g1130", 1.2),
                ("aviation", "g1030", 1.2), ("computing", "g920", 1.2), ("taramandal", "g640", 1.5), ("study", "w770", 1.0),
                ("avhall", "w770", 1.5), ("avhall", "w860", 1.2), ("washroom", "w860", 1.0), ("guest", "w770", 0.9)]:
    e(r, c, w)
# exits
e("g1540", "MAIN", 2.0, "door"); e("w860", "WEST", 1.5, "stair"); e("g820", "VER", 1.2, "door")

out = {"name": "Nehru Museum of Science & Technology, Block B, IIT Kharagpur (digitised from the posted floor-plan panel)",
       "source": {"photo": "data/maps/iit_kgp_nmst_block_b.jpg", "author": "Biswarup Ganguly", "license": "CC BY 3.0",
                  "url": "https://commons.wikimedia.org/wiki/File:Floor_Plan_Panel_-_NMST_-_IIT_Kharagpur_-_West_Midnapore_2015-09-28_4616.JPG"},
       "assumptions": "scale 0.06 m/px; occupancy for a busy school-visit day; widths and exits estimated from the panel",
       "units": "m", "nodes": nodes, "edges": edges}
Path("data/iit_kgp_museum.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(nodes), "nodes", len(edges), "edges", sum(n.get("people", 0) for n in nodes), "people")
