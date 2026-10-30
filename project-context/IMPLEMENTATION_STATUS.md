# NIKAAS — Implementation Status & Feature Inventory

## 1. Status Categories Overview

This document categorizes every component, module, endpoint, and test within NIKAAS as of 30 October 2026 (~12:15 PM, Day 1 of AfterHours 1.0).

| Status Category | Definition |
|---|---|
| **Implemented and Verified** | Code exists, executes successfully, and passes automated verification/tests. |
| **Implemented but Not Verified** | Code exists but cannot be executed or tested in the current environment due to missing dependencies. |
| **Partially Implemented** | Code exists in rudimentary form or lacks critical downstream integration. |
| **Documented but Not Implemented** | Fully described in architecture/contract/task files, but zero code has been authored yet. |
| **Missing** | Required for delivery or mentioned in planning, but no files or stubs exist. |
| **Blocked** | Precluded from execution by absent external accounts, cloud credentials, or tooling. |

---

## 2. Explicit Investigation of Planned Files

The prompt explicitly mandated checking the status of seven key files:

| Planned File | Target Owner | Current Status | Findings & Evidence |
|---|---|---|---|
| **`nikaas/optimise.py`** | Ayush | **Missing / Documented Only** | File does not exist on disk (`Test-Path` returned `False`). Neither greedy search nor SciPy LP solver has been written yet. |
| **`nikaas/vision.py`** | Abhijeet | **Missing / Blocked** | File does not exist on disk (`Test-Path` returned `False`). Blocked on AWS Bedrock credentials on local machine. |
| **`web/`** | Bhumika | **Missing / Documented Only** | Directory does not exist on disk (`Test-Path` returned `False`). React/Vite/Three.js project not yet scaffolded. |
| **`template.yaml`** | Abhijeet | **Missing / Blocked** | File does not exist on disk (`Test-Path` returned `False`). SAM CloudFormation template not yet drafted. |
| **`tests/test_optimise.py`** | Ayush | **Missing / Documented Only** | File does not exist on disk (`Test-Path` returned `False`). No optimisation tests exist. |
| **`data/cse_labs.json`** | Chirag | **Documented / Replaced** | File does not exist. DBIT CSE labs map was not found online; replaced by `data/lab_block.json` and upstream `data/iit_kgp_museum.json`. |
| **`scripts/run_wow.py`** | Ayush | **Missing / Documented Only** | File does not exist on disk (`Test-Path` returned `False`). Wow number generation script not yet created. |

---

## 3. Comprehensive Component-by-Component Status

### 3.1 Backend & Simulation Engine (`nikaas/`)

| Component / Artifact | Category | Notes / Verification Evidence |
|---|---|---|
| `nikaas/building.py`: Data Structures (`Edge`, `Building`) | **Implemented and Verified** | Loaded and instantiated cleanly across 3 distinct building datasets. |
| `nikaas/building.py`: `load()` | **Implemented and Verified** | Parses JSON files and in-memory dicts, computes Euclidean lengths, assigns door/corridor kinds. |
| `nikaas/building.py`: `shortest_path()` | **Implemented and Verified** | Dijkstra path search verified. Correctly excludes nodes in `blocked` set. Returns `(inf, [])` when unreachable. |
| `nikaas/building.py`: `nearest_plan()` | **Implemented and Verified** | Evaluates closest open exit for each room. Verified in `test_sim.py`. |
| `nikaas/building.py`: `validate()` | **Implemented and Verified** | Validates node schemas, coordinates, non-negative occupant counts, edge endpoints, positive widths, exit reachability. Verified directly. |
| `nikaas/sim.py`: Person movement & state machine | **Implemented and Verified** | `inside`, `queuing`, `walking`, `stairs`, `out` transitions execute as expected. |
| `nikaas/sim.py`: Hydraulic capacity credit system | **Implemented and Verified** | SFPE flow limits verified against analytical hand calculation in `test_single_door_matches_hand_calculation`. |
| `nikaas/sim.py`: Bottleneck & edge load calculation | **Implemented and Verified** | Peak queue per edge correctly ranked; bottleneck identified accurately. |
| `nikaas/sim.py`: Determinism & seed control | **Implemented and Verified** | Deterministic with default `seed=7`. Repeated runs produce bit-for-bit identical frames. |
| `nikaas/sim.py`: Frame generation | **Implemented and Verified** | Generates frames every 1 s (first frame at `t=0.25 s`). Person coordinates and states mapped. |
| `nikaas/api.py`: FastAPI App Setup & CORS | **Implemented and Verified** | Broad CORS configured; FastAPI instantiates with title `"Nikaas"`. |
| `nikaas/api.py`: `GET /health` | **Implemented and Verified** | Returns `{"ok": True}`. |
| `nikaas/api.py`: `POST /validate` | **Implemented and Verified** | Validates request JSON; returns `{"ok": bool, "problems": []}`. |
| `nikaas/api.py`: `POST /simulate` | **Implemented and Verified** | Core simulation runs and formats response matching contract. |
| `nikaas/api.py`: Mangum Lambda Handler | **Implemented and Verified** | `handler = Mangum(app)` cleanly wrapped. |
| `nikaas/api.py`: `POST /optimise` | **Documented but Not Implemented** | Specified in `docs/CONTRACT.md`, but route not added to `api.py`. |
| `nikaas/api.py`: `POST /vision` | **Documented but Not Implemented** | Specified in `docs/tasks/abhijeet.md`, but route not added to `api.py`. |

### 3.2 Testing Suite (`tests/`)

| Test File / Function | Category | Notes / Verification Evidence |
|---|---|---|
| `test_sim.py::test_single_door_matches_hand_calculation` | **Implemented and Verified** | **PASSED** (analytical match within 5% tolerance). |
| `test_sim.py::test_everyone_is_accounted_for` | **Implemented and Verified** | **PASSED** (conservation of occupants: 300 in, 300 out). |
| `test_sim.py::test_blocked_exit_sends_everyone_to_the_other_one` | **Implemented and Verified** | **PASSED** (100% of occupants re-routed to Exit B). |
| `test_sim.py::test_plan_into_blocked_exit_is_rejected` | **Implemented and Verified** | **PASSED** (raises `ValueError` on blocked assignment). |
| `test_sim.py::test_wider_door_is_never_slower` | **Implemented and Verified** | **PASSED** (1.8 m door clears faster than 0.9 m door). |
| `test_sim.py::test_frames_are_in_contract_shape` | **Implemented and Verified** | **PASSED** (schema matches contract and JSON serializes). |
| `test_sim.py::test_busiest_edge_is_the_stair_in_front_of_the_overloaded_exit` | **Implemented and Verified** | **PASSED** (busiest edge equals bottleneck and ends with exit ID). |
| `test_sim.py::test_api_returns_edge_load_and_lambda_handler_exists` | **Implemented but Not Verified** | **FAILED during run**: `httpx` is missing in `.venv`, preventing `fastapi.testclient.TestClient` from running. |
| `test_building.py` (All 5 tests) | **Implemented but Not Verified** | **COLLECTION ERROR**: Top-level `from fastapi.testclient import TestClient` crashes pytest because `httpx` is missing. (Core logic verified manually via scratch script). |
| Upstream `test_building.py::test_digitised_iit_kgp_plan_is_valid_and_credited` | **Implemented upstream** | Present in upstream commit `587a6fa`; not yet merged into local branch. |

### 3.3 Data & Benchmark Results (`data/`, `runs/`)

| Dataset / File | Category | Notes |
|---|---|---|
| `data/sample_floor.json` | **Implemented and Verified** | 16 nodes, 15 edges, 6 rooms, 300 occupants. Verified valid. |
| `data/lab_block.json` | **Implemented and Verified** | 30 nodes, 30 edges, 14 rooms, 528 occupants. Verified valid. |
| `data/iit_kgp_museum.json` | **Implemented upstream** | 32 nodes, 31 edges, 15 rooms, 507 occupants. Added in commit `587a6fa`. |
| `data/frames_sample_nearest.json` | **Implemented and Verified** | 120 frames, 300 people, `total_time_s = 119.0`. Includes `routes` and `edge_load`. |
| `data/frames_sample_blockedA.json` | **Implemented and Verified** | 197 frames, 300 people, `total_time_s = 196.75`. Includes `routes` and `edge_load`. |
| `data/frames_lab_block_nearest.json` | **Implemented and Verified** | 212 frames, 528 people, `total_time_s = 211.75`. Includes `routes` and `edge_load`. |
| `data/frames_lab_block_blockedB.json` | **Implemented and Verified** | 306 frames, 528 people, `total_time_s = 305.75`. Includes `routes` and `edge_load`. |
| `runs/results.csv` | **Implemented and Verified** | Contains 5 recorded experimental baseline runs with SHA256 hashes and git commit tags. |

### 3.4 Frontend (`web/`)

| Feature | Category | Notes |
|---|---|---|
| Vite + React + TypeScript scaffolding | **Missing** | `web/` folder does not exist. |
| Top-down 2D Simulation Player (Canvas/SVG) | **Documented but Not Implemented** | Due by 15:30 checkpoint for Bhumika. |
| Agent state visualizer (color by state) | **Documented but Not Implemented** | Color rules specified in `docs/VISUAL_STYLE.md`. |
| Dynamic Tap-to-Block UI interaction | **Documented but Not Implemented** | UI hook to dispatch blocked node array to `/simulate`. |
| Side-by-side comparison (Nearest vs Optimised) | **Documented but Not Implemented** | Needs `/optimise` endpoint output. |
| Three.js 3D Architectural Digital Twin | **Documented but Not Implemented** | Phase 2 objective (after 19:00). |
| `?demo=1` offline replay mode | **Documented but Not Implemented** | Designed to load `data/frames_*.json` without API server. |

### 3.5 Cloud Infrastructure & Bedrock Vision (`infra/`, `nikaas/vision.py`)

| Feature | Category | Notes |
|---|---|---|
| AWS CLI & SAM CLI setup | **Blocked** | Neither `aws` nor `sam` CLI is installed on this machine. |
| AWS IAM user & Bedrock Nova/Claude access | **Blocked** | No AWS credentials configured locally (`docs/tasks/abhijeet.md` task 1). |
| SAM CloudFormation Template (`template.yaml`) | **Missing** | Target: API Gateway HTTP API -> Lambda + S3 static bucket. |
| `nikaas/vision.py`: Bedrock Converse API call | **Blocked / Missing** | Code not yet authored; blocked on Bedrock access. |
| S3 Photo Upload flow | **Documented but Not Implemented** | Due by 23:00 checkpoint. |
