# Learnings (dated)

- **30 Oct 11:25** — The hand-calculated single-door test caught a capacity bug on the first run: leftover
  door capacity was being discarded each time step, making doors ~22% slower than the formula
  (128 s vs 100.7 s for 120 people through a 1 m door). Fixed in the simulator, not by loosening the test.
- **30 Oct 12:07** — Our first IIT Kharagpur result blamed the Audiovisual Hall's west door (queue 120). That was a model artefact: every room sent all occupants down one shortest path, so a hall's second door was never used. Rooms now split occupants across all usable doors by width (test `test_room_with_two_doors_uses_both`). Total time unchanged (112.75 s); the true bottleneck is the 1.2 m verandah door (peak queue 99). Lesson: check a surprising finding against the model's assumptions before telling anyone.
- **30 Oct 12:10** — Constants checked against published sources. SFPE Example 1 (Thunderhead Pathfinder verification docs) gives 245.2 s; our simulator now gives 245.25 s (0.02% off) after three fixes: effective width (clear width minus 6 in per door jamb), stair specific flow 1.012 p/s/m (18.5 p/min/ft, was 1.1), stair speed 0.915 m/s (0.85 x 212 ft/min, was 0.85). All baselines re-measured; times rose ~30% because effective widths are narrower.
