# NIKAAS — Repository Overview & Engineering Inventory

## 1. Project Identity & Hackathon Context
- **Project Name:** Nikaas
- **Tagline:** *"Photograph the exit map. Get everyone out faster."*
- **Theme:** 03 — Simulation, Digital Twins & Synthetic Data
- **Hackathon Event:** AfterHours 1.0 (Don Bosco Institute of Technology — DBIT, 30–31 Oct 2026)
- **Team Name:** TheGoodEngineers (Team ID: `AH50` on Unstop)
- **Team Members & Core Roles:**
  - **Ayush V U (Team Lead):** Optimiser, lower bound (LP), wow number (`nikaas/optimise.py`, `runs/wow.csv`)
  - **Bhumika G:** Web application, 2D simulation player, 3D digital twin rendering (`web/`)
  - **Abhijeet:** Cloud infrastructure, Bedrock vision pipeline, SAM deployment, pitch & submission (`template.yaml`, `nikaas/vision.py`)
  - **Chirag R H (Build Lead):** Core building graph, hydraulic simulator, FastAPI backend, validation, integration (`nikaas/building.py`, `nikaas/sim.py`, `nikaas/api.py`)
- **Key Deadlines & Checkpoints:**
  - 30 Oct 09:30 — Clock started / Idea pitch
  - 30 Oct 15:30 — Working 2D player demo
  - 30 Oct 19:00 — Live API + Vision prototype
  - 30 Oct 23:00 — Full AWS deployment
  - 31 Oct 07:30 — Code freeze
  - 31 Oct 09:00 — Final submission (Unstop form + public GitHub repo)
  - 31 Oct 09:30 — Hackathon clock ends

---

## 2. Git State & Repository Synchronization

### Remotes
- `origin`: `https://github.com/AyushVUpadhye/Nikaas.git` (Working fork)
- `upstream`: `https://github.com/thegoodengineers/Nikaas.git` (Main team repo)

### Branch & Commit Comparison
- **Current Local Branch:** `main`
- **Current Local HEAD:** `f206a10` (*"feat: representative L-shaped lab block (3 stairs, 528 people) with measured baselines"*)
- **Status vs `origin/main`:** **Ahead by 2 commits** (`5ce810f` and `f206a10`). Changes have not yet been pushed to Ayush's fork remote.
- **Status vs `upstream/main`:** **Behind by 1 commit** (`587a6fa` - *"feat: real Indian demo building (IIT Kharagpur NMST floor-plan panel), digitised and credited"*).
- **Working Tree:** Clean (no uncommitted or untracked file modifications).

### Commit Timeline Log (Recent)
```text
587a6fa (upstream/main) feat: real Indian demo building (IIT Kharagpur NMST floor-plan panel), digitised and credited
f206a10 (HEAD -> main) feat: representative L-shaped lab block (3 stairs, 528 people) with measured baselines
5ce810f feat: building validation endpoint, per-room routes in simulate output
2a82545 (origin/main) docs: build-lead notes in each task file
a808d83 feat: per-edge load in simulate output, Lambda handler for deploy
f889ebf docs: one task file per person under docs/tasks/
9c6b132 docs: plan, stack, questions, learnings, build log, submission template
f5c2779 docs: per-person task briefs, visual style, sample frames for the frontend
```

---

## 3. Complete File & Directory Inventory

```
C:\Users\HP\Nikaas\
├── .gitignore                      # Python and pytest ignore patterns
├── README.md                       # High-level elevator pitch, setup instructions, layout
├── hackathon.md                    # Live timestamped build log from 09:30 onward
├── requirements.txt                # Runtime & testing dependencies (fastapi, uvicorn, pydantic, pytest, mangum)
│
├── nikaas/                         # Core Python package
│   ├── __init__.py                 # Empty package marker
│   ├── api.py                      # FastAPI application with CORS, Mangum handler, /health, /validate, /simulate
│   ├── building.py                 # Graph data structures (Edge, Building), loader, Dijkstra, nearest_plan, validator
│   └── sim.py                      # Flow-limited SFPE hydraulic simulation engine, frame generator
│
├── tests/                          # Automated acceptance test suite
│   ├── test_building.py            # Graph structural validation, reachability checks, API error tests
│   └── test_sim.py                 # Simulation mechanics, capacity checks, queue accounting, frame contracts
│
├── data/                           # Building topology graphs and pre-computed frame datasets
│   ├── sample_floor.json           # 16-node provisional test floor (6 rooms, 300 occupants, 2 stair exits)
│   ├── lab_block.json              # 30-node L-shaped engineering lab block (14 rooms, 528 occupants, 3 stairs)
│   ├── frames_sample_nearest.json  # 120 simulation frames for sample_floor baseline (119.0 s)
│   ├── frames_sample_blockedA.json # 197 simulation frames for sample_floor with Stair A blocked (196.75 s)
│   ├── frames_lab_block_nearest.json   # 212 frames for lab_block baseline (211.75 s)
│   └── frames_lab_block_blockedB.json  # 306 frames for lab_block with Stair B blocked (305.75 s)
│
├── runs/                           # Verifiable experimental data and benchmark records
│   └── results.csv                 # Canonical run log recording sha256, plan, blocked exits, completion times, bottlenecks
│
├── scripts/                        # Automation & generation utilities
│   ├── make_lab_block.py           # Procedural generator for data/lab_block.json
│   └── run_nearest.py              # CLI script to simulate nearest-exit plan and append metrics to runs/results.csv
│
└── docs/                           # Team documentation, system contracts, and task specifications
    ├── CONTRACT.md                 # Frozen data contract for building graphs, API payloads, and simulation frames
    ├── PLAN.md                     # Hackathon master plan, value proposition, rubric alignment, risks
    ├── STACK.md                    # Technical stack rationale per layer
    ├── TASKS.md                    # Team workflow rules, checkpoints, and task ownership matrix
    ├── QUESTIONS.md                # Assumptions log (capacities, corridor widths, speed constants)
    ├── LEARNINGS.md                # Discovered bugs and empirical observations
    ├── VISUAL_STYLE.md             # Aesthetic guidelines for 2D/3D visualization (matte white model, orange queues)
    ├── submission.md               # Unstop submission draft template
    └── tasks/                      # Per-engineer actionable specifications
        ├── abhijeet.md             # AWS infrastructure, Bedrock vision, SAM template
        ├── ayush.md                # Optimiser LP, greedy algorithm, lower bound, wow benchmark
        ├── bhumika.md              # React frontend, 2D player, 3D three.js twin, dynamic re-route UI
        └── chirag.md               # Core engine, build lead responsibilities, merge checkpoints
```

---

## 4. Environment & Toolchain State

- **Operating System:** Windows 10/11 x64
- **Python Runtime:** Python 3.11.9 (`C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe`)
- **Virtual Environment:** Present at `C:\Users\HP\Nikaas\.venv`
  - Installed packages: `fastapi` (0.162.0), `uvicorn` (0.54.0), `pydantic` (2.14.2), `pytest` (9.2.0), `mangum` (0.22.0), `starlette` (1.10.0), `anyio` (4.15.1)
  - **Critical Dependency Gap:** `httpx` is missing from `.venv` and `requirements.txt`. Starlette's `TestClient` cannot instantiate without it, causing API-level test failures.
- **Node.js / NPM:** Node v24.20.0, NPM 11.19.0 (ExecutionPolicy blocks `npm.ps1`; `npm.cmd` must be used).
- **AWS CLI:** `aws` CLI is **not installed / not in PATH**. `aws sts get-caller-identity` cannot be run locally.
- **AWS SAM CLI:** `sam` is **not installed / not in PATH**. Local packaging/deployment via SAM is currently unavailable on this machine.
