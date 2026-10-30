"""HTTP API (FastAPI). Run locally: uvicorn nikaas.api:app --reload
Contract: docs/CONTRACT.md. Abhijeet wraps this for Lambda (Mangum) in the SAM template."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .building import load, nearest_plan, validate
from .sim import simulate

app = FastAPI(title="Nikaas")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class SimRequest(BaseModel):
    building: dict
    plan: dict | None = None  # room -> exit; null = nearest open exit
    blocked: list[str] = []


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
        out = simulate(b, plan, set(req.blocked))
    except (KeyError, ValueError) as e:
        raise HTTPException(422, str(e))
    out["plan"] = plan
    return out
