"""HTTP API (FastAPI). Run locally: uvicorn nikaas.api:app --reload
Contract: docs/CONTRACT.md. Abhijeet wraps this for Lambda (Mangum) in the SAM template."""
import base64
import binascii
import json
import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

from .building import load, nearest_plan, validate
from .crowd import analyse as crowd_analyse
from .optimise import beat_nikaas_score, optimise
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


class OptimiseRequest(BaseModel):
    building: dict
    blocked: list[str] = []


try:  # AWS Lambda entry point (template.yaml points at nikaas.api.handler)
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # local runs do not need mangum
    handler = None


@app.get("/health")
def health():
    # lists the POST routes this deployment serves, so a stale deploy is obvious (e.g. no "optimise")
    routes = sorted(r.path.strip("/") for r in app.routes if "POST" in getattr(r, "methods", set()))
    return {"ok": True, "routes": routes}


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
    # crowd density analysis: crush-risk on every corridor/door edge over time
    try:
        out["crowd"] = crowd_analyse(out, req.building)
    except Exception:  # never fail /simulate because of crowd analysis
        out["crowd"] = None
    return out


@app.post("/optimise")
def run_optimise(req: OptimiseRequest):
    probs = validate(req.building)
    if probs:
        raise HTTPException(422, {"problems": probs})
    try:
        b = load(req.building)
        out = optimise(b, set(req.blocked))
    except (KeyError, ValueError) as e:
        raise HTTPException(422, str(e))
    return out

class VisionRequest(BaseModel):
    image: str  # base64 photo (png/jpeg/webp), with or without a "data:image/...;base64," prefix
    width_m: float = 80.0  # the building's real east-west length in metres (photos have no scale)
    name: str | None = None


MAX_PHOTO = 3_750_000  # Bedrock's image size limit (bytes)


def photo_format(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if b[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "webp"
    return None


def save(key, body, content_type):
    """Keep uploads and results in the photo bucket (set on Lambda by template.yaml; skipped locally)."""
    bucket = os.environ.get("PHOTO_BUCKET")
    if not bucket:
        return None
    import boto3

    boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
    return key


@app.post("/vision")
def vision(req: VisionRequest):
    """Photo of a floor plan -> building graph (docs/CONTRACT.md). Takes ~15-20 s (Amazon Bedrock)."""
    from .vision import read_map

    data = req.image.split(",", 1)[1] if req.image.startswith("data:") else req.image
    try:
        img = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(400, "image must be base64")
    fmt = photo_format(img)
    if not fmt:
        raise HTTPException(415, "photo must be PNG, JPEG or WebP")
    if len(img) > MAX_PHOTO:
        raise HTTPException(413, f"photo is {len(img) / 1e6:.1f} MB; max 3.75 MB (resize it first)")
    if not 5 <= req.width_m <= 2000:
        raise HTTPException(422, "width_m must be the building length in metres (5-2000)")
    try:
        building, probs = read_map(img, fmt, width_m=req.width_m, name=req.name or "building from photo")
    except Exception as e:  # Bedrock down, throttled or no access: say so instead of a bare 500
        raise HTTPException(502, f"vision service failed: {type(e).__name__}: {e}")
    rid = uuid.uuid4().hex[:12]
    stored = None
    try:
        stored = save(f"photos/{rid}.{fmt}", img, f"image/{fmt}")
        save(f"results/{rid}.json", json.dumps({"building": building, "problems": probs}), "application/json")
    except Exception:  # storage is for our records; never fail the user's request over it
        stored = None
    return {"ok": not probs, "id": rid, "building": building, "problems": probs, "photo_key": stored}


class BeatRequest(BaseModel):
    building: dict
    plan: dict  # the judge's own plan: room -> exit
    blocked: list[str] = []


@app.post("/beat")
def beat(req: BeatRequest):
    """'Beat Nikaas': time a judge's hand-made plan against the optimiser (Ayush's beat_nikaas_score)."""
    probs = validate(req.building)
    if probs:
        raise HTTPException(422, {"problems": probs})
    try:
        b = load(req.building)
        missing = [r for r in b.rooms if r not in req.plan]
        if missing:
            raise ValueError(f"plan has no exit for rooms: {missing}")
        return beat_nikaas_score(b, req.plan, set(req.blocked))
    except (KeyError, ValueError) as e:
        raise HTTPException(422, str(e))
