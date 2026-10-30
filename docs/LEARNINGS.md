# Learnings (dated)

- **30 Oct 11:25** — The hand-calculated single-door test caught a capacity bug on the first run: leftover
  door capacity was being discarded each time step, making doors ~22% slower than the formula
  (128 s vs 100.7 s for 120 people through a 1 m door). Fixed in the simulator, not by loosening the test.
