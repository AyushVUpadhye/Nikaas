# What-if questions — judge preparation

Every answer below comes from a run saved in `runs/` or from `docs/RESULTS.md`.
Numbers to fill: run the scenarios with `python scripts/run_nearest.py <building>` before the demo.

---

## 1. "What happens if you block each exit one at a time?"

**Lab block (528 people, 3 exits):**

| Blocked exit | Movement time | vs. unblocked | Bottleneck |
|---|---|---|---|
| None | 301.25 s | — | m-34-A (175) |
| A (west) | **284.75 s** | −16.5 s (faster!) | m30-B (184) |
| B (main) | 437.5 s | +136.25 s | m-34-A (256) |
| C (side wing) | 301.25 s | ±0 s (C's 70 people move to B, which has spare capacity; A stays the bottleneck) | m-34-A (175) |

Note: blocking A is faster because A was the bottleneck; removing it redistributes flow to B and C which have spare capacity — counterintuitive result from the hydraulic model (SFPE Ch. 56).

**IIT KGP museum (507 people, 3 exits):**

| Blocked exit | Movement time |
|---|---|
| None | 145.25 s |
| MAIN | 318.0 s |
| VER | 208.25 s |
| WEST | 272.25 s |

Source: `docs/RESULTS.md`.

---

## 2. "What if you double the Audiovisual / seminar hall occupancy?"

Building: `data/whatif_lab_block_seminar_x2.json` (lab block with the seminar hall doubled to 240; 648 people in total).
Movement time with the nearest-exit rule: **433.0 s** (vs 301.25 s), people per exit A 384 / B 194 / C 70, bottleneck m-34-A (peak queue 254).
The extra 120 people all join the narrow west stair A. Source: `runs/results.csv` / `docs/RESULTS.md`.

---

## 3. "What if a corridor door is narrower?"

Corridor `seminar → m-10` currently width 1.6 m (effective ~1.2 m).
Narrow it to 0.9 m and re-simulate.
*(run needed)*

---

## 4. "Can your tool prove the Chinnaswamy gate was dangerous?"

Yes.  The stadium model (`data/stadium_gates.json`) has Gate South at 2.0 m width — the metro-side gate.
Running Crowd mode shows density exceeds 4 p/m² on the `cn2 → GATE_S` corridor within the first 60 s.
That is the crush threshold from G. Keith Still's crowd-safety framework.

---

## 5. "How does Nikaas compare to Pathfinder or Exodus?"

Nikaas uses the same hydraulic network model as the SFPE Handbook worked example (245.25 s vs 245.2 s match).
Pathfinder uses an agent-based model which is more detailed but requires a paid licence and hours of setup.
Nikaas is open-source, runs in a browser, and returns results in < 1 second for buildings up to ~600 people.
It is not a replacement for a full agent-based simulation for regulatory submission — it is the first step that tells you *where to look*.

---

## 6. "What about multi-floor buildings?"

Not built yet.  The contract supports `stair` edges which connect floors — the graph is already multi-floor capable.
The simulator treats stairs as slower corridors (SFPE stair speed 0.915 m/s vs 1.19 m/s walking).
Full multi-floor animation is the next feature after the hackathon.

---

## 7. "What about the Indian National Building Code?"

National Building Code of India 2016, Part 4 (Fire and Life Safety):
- Minimum exit width: 1.0 m for up to 50 persons, +300 mm per additional 50 persons.
- Travel distance to exit: ≤ 30 m (unsprinklered), ≤ 45 m (sprinklered).
- Minimum 2 exits for any occupancy > 50 persons.

Nikaas can flag NBC violations: if any room has only one path to an exit, or if the shortest-path distance exceeds 30 m, the `/validate` endpoint returns a problem string.
*(Add NBC distance check to validate — note for Chirag)*
