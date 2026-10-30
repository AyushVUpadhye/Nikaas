# NIKAAS — API & Data Contracts

## 1. Contract Overview

This document specifies the exact data schemas, API contracts, units, coordinate systems, and validation rules governing NIKAAS.
It reflects the frozen contract defined in `docs/CONTRACT.md` and the actual implementation in `nikaas/building.py` and `nikaas/api.py`.

---

## 2. Building Graph Data Format (`data/*.json`)

A building is represented as a planar graph stored in a JSON file or sent in API payloads.

### 2.1 Coordinate System & Units
- **Distance Unit:** Metres (`m`).
- **Plane:** Horizontal plane defined by $(X, Z)$.
  - $+X$: East / Right
  - $+Z$: South / Forward
  - $Y$: Height / Vertical (reserved for multi-story / 3D elevation; currently flat 2D projection with stair flags).
- **Time Unit:** Seconds (`s`).
- **Speed Unit:** Metres per second (`m/s`).
- **Capacity Unit:** Persons per second ($p/s$).
- **Occupancy Unit:** Whole integer individuals ($p \ge 0$).

### 2.2 Schema Definition

```json
{
  "name": "string (Human-readable building title)",
  "units": "m",
  "nodes": [
    {
      "id": "string (Unique identifier, e.g., 'lab1', 'c_w', 'A')",
      "type": "room | corridor | exit",
      "x": "number (X coordinate in metres)",
      "z": "number (Z coordinate in metres)",
      "w": "number (Room width in metres; required for 'room', ignored otherwise)",
      "d": "number (Room depth in metres; required for 'room', ignored otherwise)",
      "people": "integer >= 0 (Initial occupants; required for 'room')",
      "label": "string (Optional friendly display name, e.g. 'Stair A (West)')"
    }
  ],
  "edges": [
    {
      "from": "string (Valid node id)",
      "to": "string (Valid node id)",
      "width": "number > 0 (Clear width in metres)",
      "length": "number > 0 (Optional length in metres; defaults to Euclidean distance hypot(dx, dz))",
      "kind": "door | corridor | stair (Optional; defaults to 'door' if room connected, else 'corridor')"
    }
  ]
}
```

### 2.3 Structural Rules & Validation Constraints (`nikaas/building.py: validate`)
1. Must contain top-level `"nodes"` and `"edges"` arrays.
2. Node IDs must be strictly unique within the graph (no duplicate IDs).
3. Every node `type` must be exactly `"room"`, `"corridor"`, or `"exit"`.
4. Every node must have numeric `x` and `z` values.
5. Rooms must have an integer occupant count `people >= 0`.
6. Every edge's `from` and `to` references must resolve to an existing node ID.
7. Edge `width` must be strictly positive (`width > 0`).
8. Edge `kind`, if provided, must be `"door"`, `"corridor"`, or `"stair"`.
9. The building must have at least one node of type `"exit"`.
10. **Global Reachability Constraint:** Every room must be able to reach at least one exit via an unblocked Dijkstra path. If any room is orphaned or isolated, validation fails.

---

## 3. HTTP API Endpoints

Base URL (Local): `http://127.0.0.1:8000`  
Base URL (AWS Production - Target): `https://<api-id>.execute-api.ap-south-1.amazonaws.com`

### 3.1 `GET /health`
Liveness probe.
- **Request:** None
- **Response `200 OK`:**
  ```json
  { "ok": true }
  ```

### 3.2 `POST /validate`
Checks whether a building graph complies with all topological and reachability rules without running a simulation.
- **Request Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "building": { ... }
  }
  ```
- **Response `200 OK` (Valid):**
  ```json
  {
    "ok": true,
    "problems": []
  }
  ```
- **Response `200 OK` (Invalid):**
  ```json
  {
    "ok": false,
    "problems": [
      "duplicate node ids: ['c1']",
      "edge 3: unknown node 'exit_lost'",
      "room staff cannot reach any exit"
    ]
  }
  ```

### 3.3 `POST /simulate`
Executes a deterministic hydraulic evacuation simulation.
- **Request Body:**
  ```json
  {
    "building": { ... },
    "plan": {
      "lab1": "A",
      "lab2": "A",
      "lab3": "B"
    },
    "blocked": ["A"]
  }
  ```
  - `plan` is optional: if omitted (`null`), the simulator computes the default `nearest_plan(building, blocked)`.
  - `blocked` is optional: defaults to `[]`. Lists node IDs (typically staircases or exit doors) that cannot be entered.
- **Response `200 OK`:**
  ```json
  {
    "total_time_s": 119.0,
    "completed": true,
    "people": 300,
    "per_exit": {
      "A": 174,
      "B": 126
    },
    "bottleneck": "c_w-A",
    "peak_queue": 92,
    "edge_load": {
      "c_w-A": 92,
      "c_e-B": 64,
      "c_l1-c_l4": 12,
      "lab1-c_l1": 0
    },
    "routes": {
      "lab1": ["lab1", "c_l1", "c_w", "A"],
      "lab2": ["lab2", "c_l2", "c_sm", "c_l3", "c_st", "c_e", "B"]
    },
    "plan": {
      "lab1": "A",
      "lab2": "B"
    },
    "frames": [
      {
        "t": 0.25,
        "people": [
          [-14.85, -6.92, "queuing"],
          [-15.12, -7.15, "queuing"]
        ]
      },
      {
        "t": 1.0,
        "people": [
          [-15.0, -5.81, "walking"],
          [-15.12, -7.15, "queuing"]
        ]
      }
    ]
  }
  ```
- **Error Response `422 Unprocessable Entity` (Schema / Reachability failure):**
  ```json
  {
    "detail": {
      "problems": [
        "room lab1 cannot reach any exit"
      ]
    }
  }
  ```
- **Error Response `422 Unprocessable Entity` (Invalid plan targeting blocked exit):**
  ```json
  {
    "detail": "plan sends lab1 to blocked exit A"
  }
  ```

### 3.4 `POST /optimise` (Contract Defined in `docs/CONTRACT.md`, Planned for Ayush)
Solves exit allocation to minimize the completion time of the last evacuee.
- **Request Body:**
  ```json
  {
    "building": { ... },
    "plan": null,
    "blocked": ["A"]
  }
  ```
- **Target Response `200 OK`:**
  ```json
  {
    "plan": {
      "lab1": "B",
      "lab2": "B",
      "lab3": "C"
    },
    "total_time_s": 185.5,
    "lower_bound_s": 172.0
  }
  ```

---

## 4. Simulation Frames & Person State Machine

### 4.1 Frame Sampling Cadence
- Physical simulation step: `DT = 0.25 s`.
- Output frame record: Every `1.0 s` of simulated time (`frame_every = 1.0`).
- **Initial Frame Offset:** The first frame is captured at `t = 0.25 s` (immediately following the first simulation tick), followed by `t = 1.0 s, 2.0 s, 3.0 s, ...`.

### 4.2 Person Vector Format
Each element in `frame.people` is a 3-tuple:
`[x: float, z: float, state: string]`
- Coordinates are rounded to 2 decimal places (`round(..., 2)`).
- `state` is strictly one of five enumerated strings:
  1. `"inside"`: Occupant is still inside originating room during pre-movement delay.
  2. `"queuing"`: Occupant is waiting in a FIFO line at the threshold of an edge that is at flow capacity.
  3. `"walking"`: Occupant is actively moving along a horizontal corridor or through a clear door.
  4. `"stairs"`: Occupant is descending/ascending a staircase edge at stair velocity ($0.85\text{ m/s}$).
  5. `"out"`: Occupant has passed an exit node and successfully evacuated. (Occupant coordinates freeze at exit node).
