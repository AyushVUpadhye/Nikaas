"""HTTP API (FastAPI). Run locally: uvicorn nikaas.api:app --reload
Contract: docs/CONTRACT.md. Abhijeet wraps this for Lambda (Mangum) in the SAM template."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

from .building import load, nearest_plan, validate
from .sim import simulate

app = FastAPI(title="Nikaas")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
# frames are large (5 MB for 528 people over 7 min); gzip keeps responses far below the 6 MB Lambda limit
app.add_middleware(GZipMiddleware, minimum_size=1000)


class SimRequest(BaseModel):
    building: dict
    plan: dict | None = None  # room -> exit; null = nearest open exit
    blocked: list[str] = []
    frame_every: float = 1.0  # seconds of simulated time between frames (bigger = smaller response)


try:  # AWS Lambda entry point (template.yaml points at nikaas.api.handler)
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # local runs do not need mangum
    handler = None


@app.get("/health")
def health():
    return {"ok": True}


class BuildingRequest(BaseModel):
    building: dict


@app.post("/validate")
def check(req: BuildingRequest):
    probs = validate(req.building)
    return {"ok": not probs, "problems": probs}


@app.post("/simulate")
def run(req: SimRequest):
    probs = validate(req.building)
    if probs:
        raise HTTPException(422, {"problems": probs})
    try:
        b = load(req.building)
        plan = req.plan or nearest_plan(b, set(req.blocked))
        out = simulate(b, plan, set(req.blocked), frame_every=max(0.25, req.frame_every))
    except (KeyError, ValueError) as e:
        raise HTTPException(422, str(e))
    out["plan"] = plan
    return out
