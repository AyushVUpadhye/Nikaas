# Shared contract (frozen at 11:45, change only via the build lead)

## Building graph JSON (`data/*.json`)
- `nodes[]`: `id`, `type` (`room` | `corridor` | `exit`), `x`, `z` in metres; rooms also `w`, `d`, `people`; exits may have `label`.
- `edges[]`: `from`, `to`, `width` (clear width, m); optional `length` (m, defaults to straight-line distance) and `kind` (`door` | `corridor` | `stair`; defaults to `door` if a room is involved, else `corridor`).
- Example: `data/sample_floor.json` (provisional until the CSE Labs photo is digitised into `data/cse_labs.json`).

## API
`POST /simulate` body `{"building": {...}, "plan": {"room": "exit"} | null, "blocked": ["exitId"]}`
returns `{"total_time_s", "completed", "people", "per_exit": {exit: count}, "bottleneck": "a-b", "peak_queue", "edge_load": {"a-b": peak queue, busiest first}, "plan", "frames": [{"t", "people": [[x, z, state]]}]}`.
`state` ∈ `inside | walking | queuing | stairs | out`. Frames are every 1 s of simulated time.

`POST /optimise` (Ayush) same body, returns `{"plan", "total_time_s", "lower_bound_s"}`.
