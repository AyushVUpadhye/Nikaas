"""Vision tests. No AWS calls: Bedrock is replaced by a fake client that returns a fixed reply."""
import json
from pathlib import Path

from nikaas.building import validate
from nikaas.vision import _extract_json, connect, image_size, read_map, to_building

ROOT = Path(__file__).resolve().parents[1]
PHOTO = ROOT / "data/maps/iit_kgp_nmst_block_b.jpg"

# two rooms, a walkway, one exit; room B and the exit are not linked (models often leave gaps like this)
REPLY = {
    "rooms": [
        {"id": "a", "label": "Gallery A", "use": "gallery", "box": [100, 100, 300, 300]},
        {"id": "b", "label": "Hall B", "use": "seated_hall", "box": [300, 100, 500, 300]},
    ],
    "points": [{"id": "p1", "at": [200, 350]}, {"id": "p2", "at": [400, 350]}],
    "exits": [{"id": "OUT", "label": "Main door", "at": [500, 350]}],
    "links": [{"from": "a", "to": "p1", "width": 1.2, "kind": "door"},
              {"from": "p1", "to": "p2", "width": 2.5, "kind": "corridor"},
              {"from": "a", "to": "ghost", "width": 1.0}],
}


class FakeBedrock:
    def __init__(self, reply):
        self.reply, self.calls = reply, 0

    def converse(self, **kw):
        self.calls += 1
        assert kw["messages"][0]["content"][0]["image"]["source"]["bytes"]
        return {"output": {"message": {"content": [{"text": self.reply}]}},
                "usage": {"inputTokens": 10, "outputTokens": 20}}


def test_image_size_reads_jpeg_header():
    assert image_size(PHOTO.read_bytes()) == (1920, 1277)


def test_extract_json_handles_fences_and_chatter():
    assert _extract_json('Here you go:\n```json\n{"a": 1}\n```\nDone.') == {"a": 1}
    assert _extract_json('sure {"a": {"b": 2}} hope that helps') == {"a": {"b": 2}}


def test_to_building_scales_drawing_to_width_and_keeps_aspect():
    b = to_building(REPLY, width_m=40, size=(1000, 500))
    xs = [n["x"] for n in b["nodes"]]
    a = next(n for n in b["nodes"] if n["id"] == "a")
    # drawing spans x 100..500 on the grid -> 40 m; room a is 200 grid units wide = 20 m
    assert a["w"] == 20.0 and min(xs) >= 0 and max(xs) <= 40
    assert a["d"] == 10.0  # photo is half as tall as wide, so 200 grid units down = 10 m
    hall = next(n for n in b["nodes"] if n["id"] == "b")
    assert hall["people"] == round(20 * 10 * 1.5)  # area x seated-hall density


def test_connect_links_everything_and_reports_what_it_added():
    b = to_building(REPLY, width_m=40)
    assert validate(b)  # as the model sent it: unknown node + rooms that cannot leave
    added = connect(b)
    assert validate(b) == [] and added
    assert all(e["to"] != "ghost" for e in b["edges"])


def test_read_map_end_to_end_with_fake_bedrock():
    fake = FakeBedrock("```json\n" + json.dumps(REPLY) + "\n```")
    b, probs = read_map(PHOTO.read_bytes(), "jpeg", width_m=81, client=fake)
    assert probs == [] and fake.calls == 1
    assert b["vision"]["auto_links"] and b["vision"]["photo_px"] == [1920, 1277]
    assert {n["type"] for n in b["nodes"]} == {"room", "corridor", "exit"}


def test_read_map_reports_garbage_instead_of_crashing():
    b, probs = read_map(b"\xff\xd8not really a jpeg", "jpeg", client=FakeBedrock("I cannot read this image."))
    assert probs and b["nodes"] == []
