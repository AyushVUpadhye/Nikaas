# Nikaas — plan

## Pitch
For a college fire-safety officer, who today has a printed exit map and an untimed yearly drill,
Nikaas turns a photo of that map into a live evacuation twin: it finds the bottleneck, assigns each
room the exit that empties the building fastest, and re-plans when a stair is blocked.

**Checkable claim:** on the CSE Labs floor, Nikaas' plan evacuates faster than "nearest exit", and we
report how far it is from a proven lower bound. **Wow number:** evacuation time, nearest exit → Nikaas,
measured by `scripts/run_wow.py` into `runs/wow.csv`.

**30-second demo:** a judge taps a staircase to block it; people re-route live, the clock shows the new
time, the panel names the new bottleneck.

**Out of scope:** fire/smoke physics, multi-floor, live sensors, certification-grade compliance.

## Persona
College fire-safety officer. Today: a wall map, "go to the nearest exit", a yearly drill nobody times.
Same pain: stadiums, malls, stations, hospitals, event venues.

## Rubric (Round 2, weights not published; assumed equal)
| Criterion | What judges look for | What we show |
|---|---|---|
| Innovation | Not the obvious build for the theme | Photo → twin → optimised plan with a proven bound; tap-to-block |
| Technical implementation | Real logic, tested | Flow-limited simulator (SFPE), LP lower bound, tests incl. a hand-calculated case and a negative control |
| Working prototype | Runs live, end to end | Deployed URL + `?demo=1` fallback, rehearsed 90 s demo path |
| Impact & scalability | Named user, measured outcome, path to scale | Wow number from `runs/`; Crowd mode (stadium gates) as the scale story |
| Presentation | Clear story under time pressure | Problem in 15 s, live demo, the number, close |

## Compliance checklist
| Rule (source) | How we meet it | Evidence |
|---|---|---|
| Build within 30 Oct 09:30 – 31 Oct 09:30 (guide) | All code written in this repo during the window | Git history |
| No Round 1 problem reuse (guide, rules page) | Theme 03 evacuation twin of a real building, not the fictional city | This plan; mentor check |
| GitHub repo with README, via form (guide) | This repo | README |
| Mandatory commit checkpoints (guide) | Commit at least hourly | Git history |
| APIs, open-source libraries and templates allowed (guide) | FastAPI, SciPy, three.js, React | `docs/STACK.md` |
| Finalists give a demo / video (guide) | Live demo + recorded video | `video/` |
| Repo visible to judges | Make public before submitting | Repo settings |

## Architecture
```mermaid
flowchart LR
  photo[Exit-map photo] --> vision[Bedrock vision\nnikaas/vision.py]
  vision --> graph[Building graph JSON\ndocs/CONTRACT.md]
  hand[Hand-made / edited graph] --> graph
  graph --> sim[Simulator\nnikaas/sim.py]
  graph --> opt[Optimiser + lower bound\nnikaas/optimise.py]
  opt --> sim
  sim --> api[FastAPI on Lambda\nnikaas/api.py]
  api --> web[React + three.js\nweb/]
  api --> runs[runs/*.csv]
```

## Risks
| Risk | Mitigation |
|---|---|
| Vision misreads the map | Hand-made graph + editor; vision shown as assisted |
| LP slow or wrong | Greedy plan + simple capacity bound |
| 3D late | 2D player is the demo |
| Deploy fails or Wi-Fi drops | Local FastAPI on the demo laptop; `?demo=1` replays saved frames |
| Scope creep at night | Anything not in the pitch waits until after 07:30 freeze |

## Timeline
See `docs/TASKS.md`. Checkpoints 15:30, 23:00, freeze 07:30, submit 09:00.
