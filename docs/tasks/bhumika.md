# Bhumika — web app, realistic 3D view

Part of Nikaas (AfterHours 1.0). Read first: `docs/CONTRACT.md` (shared data format) and `docs/TASKS.md` (team rules, checkpoints).

Folder: `web/` (Vite + React + TypeScript, no UI kit). Style rules: `docs/VISUAL_STYLE.md` (copy it into the repo from Chirag's laptop).

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
