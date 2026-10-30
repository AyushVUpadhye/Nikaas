# Bhumika — Crowd mode (crush-risk feature), pitch, proof, demo video

Part of Nikaas (AfterHours 1.0). Read first: `docs/CONTRACT.md` (shared data format), `docs/TASKS.md`
(team rules, checkpoints) and `docs/PLAN.md` (pitch, persona, rubric).

You own one product feature (Crowd mode) and how judges experience Nikaas: the story and the evidence.
Every number you use comes from `docs/RESULTS.md` or a script that writes to `runs/`; never type a number from memory.

## Your feature: Crowd mode — crush-risk detection
The Chinnaswamy Stadium crowd crush (Bengaluru, 4 June 2025, 11 killed) is in our problem slide. Crowd mode
answers: *where will the crowd get dangerously dense, and when?*

1. **Research first (by 14:00)** — `docs/CROWD_RESEARCH.md`: crowd density levels and when they become
   dangerous (people per m²), with sources you actually opened (e.g. Fruin's Level of Service, G. Keith Still's
   crowd-safety work, UK Guide to Safety at Sports Grounds). Write each threshold with its source and link.
2. **Density from the simulator (by 17:00)** — `nikaas/crowd.py` + `tests/test_crowd.py`: from a `simulate()`
   result, compute people per m² on each corridor/door area over time (area = edge length × effective width
   from `nikaas/sim.py`), the peak density per edge, and a `crush_risk` list of edges and times above the
   threshold from your research. Tests: a hand-checked case (e.g. 40 people queued on a 2 m × 5 m corridor =
   4 p/m²), and a negative control (a wide, empty corridor is never flagged).
3. **Stadium building (by 19:00)** — `data/stadium_gates.json` in the contract format: a representative cricket
   stadium (stands as rooms, concourse as corridors, 4–6 gates as exits, one gate narrow and near the metro).
   Label it "representative, not measured" in `name`; list assumptions in `docs/QUESTIONS.md`. Done when
   `POST /validate` returns no problems and `python scripts/run_nearest.py data/stadium_gates.json` writes to `runs/`.
4. **API field (with Chirag, by 21:00)** — when `crowd.py` is tested, tell Chirag in the team chat; he adds a
   `crush_risk` field to `/simulate` and shows it in the website (red zones).

## Proof and story
5. **Pitch script (draft by 17:00, final by 06:00)** — `docs/PITCH.md`, 3 minutes as spoken: problem in the
   first 15 s, product name, live demo path (what to click and say), the validation line ("reproduces the SFPE
   handbook example: 245.25 s vs 245.2 s"), the wow number from `docs/RESULTS.md`, Crowd mode, close. Mark who says what.
6. **What-if sheet (by 23:00)** — `docs/WHATIFS.md`: questions judges are likely to ask (block each exit, double the
   Audiovisual Hall, a narrower door…), each answered by a run saved in `runs/`.
7. **README "For judges, start here" (draft by 23:00, final by 06:00)** — top of `README.md`: one-line pitch, live URL
   (from Abhijeet), video link, 4 bullets with real numbers, how to run, honest "working today / not built yet".
8. **Finalist PPT (by 23:00)** — update the idea PPT (offline template, max 5 slides) with real numbers and app screenshots.
9. **Demo video (07:30–08:30)** — record the website's `?demo=1` story (Chirag provides it), ≤ 3 min, captions, no speed-up.

## Keep improving (every hour until 07:30 freeze)
Do not stop when the list is done. Each hour: `git pull`, read `docs/RESULTS.md` and `hackathon.md` for what changed,
then pick one thing and commit it:
- **Research** a claim we make (density thresholds, evacuation speeds, Indian fire-safety rules such as the
  National Building Code 2016 Part 4) and add the source to the doc that uses it;
- **Review** the app and the docs as a judge would: anything unclear, unproven or broken goes in your notes to Chirag;
- **Sharpen** the pitch and what-ifs with the newest numbers; cut anything that is not backed by a run.
Log each hour's change in `hackathon.md` (one line).

Fallback: if `crowd.py` is not tested by 21:00, Crowd mode is shown as a slide with your research only.

## Notes from Chirag (build lead)
Newest at the bottom. Check this section after every `git pull`.
- **12:25** — Change of plan: **Chirag now owns the website (`web/`)**. Your work is above: the Crowd mode
  crush-risk feature (research + `nikaas/crowd.py`) plus pitch, proof, README and the demo video (moved from
  Abhijeet, who keeps AWS + vision). Useful now: the simulator matches the SFPE handbook example (245.25 s vs
  245.2 s); on the lab block, closing a stair makes evacuation *faster* than the nearest-exit rule (`docs/RESULTS.md`).
- **12:28** — The live API is up (Abhijeet): `https://4kzez16ucj.execute-api.ap-south-1.amazonaws.com/health`.
- **12:46** — Video mode is ready: open the site with `?demo=1` (e.g. `npm run dev` then `http://localhost:5173/?demo=1`). It shows the landing page for 4 s, scrolls to the map, plays the nearest-exit run with a caption, then blocks the main entrance and plays the re-routed run. Saved runs only, so it works offline. Set speed with the 1-8x buttons before recording.
- **12:54** — The wow numbers are in `runs/wow.csv` (Ayush): lab block nearest 301.25 s -> Nikaas 166.75 s (134.5 s, 44.6% faster, 3.71 s from the proven lower bound); IIT KGP 145.25 -> 124.0 s. `?demo=1` now plays nearest exit -> Nikaas plan -> main entrance blocked, with captions.
- **12:56** — Your web app (pushed at 12:57, written at 12:10) arrived after the website moved to me, and it replaced the live site. I merged so nothing is lost: your code is kept in `web/legacy-bhumika/` (with a README), and the live site in `web/src` stays on the version with the landing page, vendored three.js (npm is blocked on the venue network, so a build that needs npm packages cannot be installed here), photo switch, Nikaas comparison and `?demo=1` story. I will port your scrubber, side-by-side panels and edge_load colouring into it. **Please do not push to `web/` from now on**; your tasks are in this file (Crowd mode, pitch, README, video). Also: our rule is **no AI mentions in commits or files**, so please remove `Co-Authored-By` lines from your commit messages.
- **13:02** — Ported two of your ideas into the live site: the timeline scrubber and corridors coloured red by `edge_load` (2D view). Credited in the commit. Thanks.
