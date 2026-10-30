# Learnings (dated)

- **30 Oct 11:25** — The hand-calculated single-door test caught a capacity bug on the first run: leftover
  door capacity was being discarded each time step, making doors ~22% slower than the formula
  (128 s vs 100.7 s for 120 people through a 1 m door). Fixed in the simulator, not by loosening the test.
- **30 Oct 12:07** — Our first IIT Kharagpur result blamed the Audiovisual Hall's west door (queue 120). That was a model artefact: every room sent all occupants down one shortest path, so a hall's second door was never used. Rooms now split occupants across all usable doors by width (test `test_room_with_two_doors_uses_both`). Total time unchanged (112.75 s); the true bottleneck is the 1.2 m verandah door (peak queue 99). Lesson: check a surprising finding against the model's assumptions before telling anyone.
