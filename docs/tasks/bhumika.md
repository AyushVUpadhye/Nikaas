# Bhumika — web app, realistic 3D view

Part of Nikaas (AfterHours 1.0). Read first: `docs/CONTRACT.md` (shared data format) and `docs/TASKS.md` (team rules, checkpoints).

Folder: `web/` (Vite + React + TypeScript, no UI kit). Style rules: `docs/VISUAL_STYLE.md`. Research method and gallery links: **`docs/DESIGN_RESEARCH.md`** (do the vibe discovery first).

1. **2D player (by 15:30):** load `data/frames_sample_nearest.json`; draw rooms/corridors from
   `data/sample_floor.json` top-down; play frames with play/pause and 1×/2×/4× speed; colour people by `state`
   (walking orange, queuing red, stairs blue, out hidden). Clock + dot grid of all people + legend with counts.
2. **Live API (by 19:00):** call `POST /simulate` (local: `uvicorn nikaas.api:app`, URL in `.env`); show
   nearest vs Nikaas side by side when `/optimise` exists.
3. **Tap to block:** click an exit → re-run with `blocked` → animate the new plan. Show `bottleneck`.
4. **3D view (after 19:00):** three.js, white architectural walls, dark floor, human figures, green route ribbons
   from each room to its exit, fire + red cross on a blocked exit, perspective camera. 2D stays as fallback.
5. **`?demo=1`** plays saved frames with no backend; check it at 400 px wide too.

Fallback: if 3D is not ready by 03:00, the 2D player is the demo.

## Notes from Chirag (build lead)
Newest at the bottom. Check this section after every `git pull`.
- **11:47** — `/simulate` now returns `edge_load`: peak queue per edge (`"from-to": count`, busiest first). Use it to colour jammed corridors/stairs red; `bottleneck` is the worst one.
- **11:47** — Until the API is deployed, use `data/frames_sample_nearest.json` and `data/frames_sample_blockedA.json` (real simulator output, same shape as the API).
- **11:58** — `/simulate` now also returns `routes`: for each room the list of node ids to its exit. Draw the green escape ribbons along those nodes (coordinates from the building JSON). The sample frames files in `data/` are regenerated with `routes`.
- **12:00** — New, more realistic building: `data/lab_block.json` (L-shaped block, 2 wings, 3 stairs, 528 people). Frames: `data/frames_lab_block_nearest.json` and `data/frames_lab_block_blockedB.json`. Use this one for the demo view; it is labelled as representative, not measured.
- **12:05** — **Demo building is now the IIT Kharagpur museum floor plan** (real posted panel from India): `data/iit_kgp_museum.json` + frames `data/frames_iit_kgp_nearest.json`, `data/frames_iit_kgp_blockedMAIN.json`. Rooms have a `label` field (name as printed on the panel) to show in the 3D view. Show the original photo `data/maps/iit_kgp_nmst_block_b.jpg` on the landing screen as "the map we started from".
- **12:07** — All `data/frames_*.json` regenerated. New optional field `door_routes` (one path per door of a room); `routes` still gives one path per room if you want to keep it simple.
- **12:10** — All `data/frames_*.json` regenerated with SFPE-validated timings (names unchanged).
- **12:16** — To keep the 15:30 checkpoint safe I started `web/` (Vite + React + TS): a working 2D player of the IIT Kharagpur building with scenario switch, play/pause, 1-8x speed, clock and live counts. Run: `cd web && npm install && npm run dev`. **It is yours now**: restyle it from `docs/DESIGN_RESEARCH.md`, then add the 3D view, landing page and `?demo=1`. All colours are variables in `web/src/theme.css`. I will not edit `web/` again unless you ask, so no merge conflicts.
