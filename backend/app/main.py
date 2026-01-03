import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform as shapely_transform, unary_union
from pyproj import Transformer
from typing import Optional

load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

ORS_KEY = os.getenv("ORS_API_KEY")
if not ORS_KEY:
    # don't raise here; we'll return errors if not set
    ORS_KEY = None

app = FastAPI(title="Proxy for OpenRouteService")

# Allow only local dev frontend origin by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutocompleteReq(BaseModel):
    text: str

class RouteReq(BaseModel):
    origin: list  # [lon, lat]
    destination: list
    profile: str = "driving-car"
    avoid_polygons: Optional[dict] = None
    simplify_tolerance: Optional[float] = 0.0001

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/routes")
async def list_routes():
    """Return a list of registered route paths for debugging."""
    paths = sorted({r.path for r in app.routes if getattr(r, 'path', None)})
    return {"routes": paths}


@app.get("/api/autocomplete")
async def autocomplete_get(q: str):
    """Debug-friendly GET autocomplete for quick checks via browser/curl"""
    if not ORS_KEY:
        logger.error("Autocomplete (GET) called but ORS_API_KEY not configured")
        raise HTTPException(status_code=500, detail="ORS_API_KEY not configured on server")

    if not q or len(q.strip()) < 3:
        return []

    # Restrict autocomplete to CDMX area (boundary.rect: minLon,minLat,maxLon,maxLat)
    url = f"https://api.openrouteservice.org/geocode/autocomplete?api_key={ORS_KEY}&text={q}&boundary.rect=-99.36,19.01,-98.90,19.59"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
    except httpx.HTTPError as e:
        logger.exception("Network error when calling ORS autocomplete (GET)")
        raise HTTPException(status_code=502, detail=f"Network error when contacting ORS: {str(e)}")

    if r.status_code == 429:
        logger.warning("ORS rate limited (429)")
        raise HTTPException(status_code=502, detail="ORS rate limit reached (429)")

    if r.status_code != 200:
        logger.error("ORS returned error for autocomplete (GET): %s %s", r.status_code, r.text)
        raise HTTPException(status_code=502, detail=f"ORS error: {r.status_code}")

    data = r.json()
    features = data.get("features", [])
    results = []
    for f in features:
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates")
        if not coords:
            continue
        results.append({"label": props.get("label"), "coords": coords})

    return results


@app.post("/api/autocomplete")
async def autocomplete(req: AutocompleteReq):
    if not ORS_KEY:
        logger.error("Autocomplete called but ORS_API_KEY not configured")
        raise HTTPException(status_code=500, detail="ORS_API_KEY not configured on server")

    # guard short queries to avoid unnecessary calls
    if not req.text or len(req.text.strip()) < 3:
        return []

    url = f"https://api.openrouteservice.org/geocode/autocomplete?api_key={ORS_KEY}&text={req.text}&boundary.country=MEX"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
    except httpx.HTTPError as e:
        logger.exception("Network error when calling ORS autocomplete")
        raise HTTPException(status_code=502, detail=f"Network error when contacting ORS: {str(e)}")

    if r.status_code == 429:
        logger.warning("ORS rate limited (429)")
        raise HTTPException(status_code=502, detail="ORS rate limit reached (429)")

    if r.status_code != 200:
        logger.error("ORS returned error for autocomplete: %s %s", r.status_code, r.text)
        raise HTTPException(status_code=502, detail=f"ORS error: {r.status_code}")

    data = r.json()
    features = data.get("features", [])
    results = []
    for f in features:
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates")
        if not coords:
            continue
        results.append({"label": props.get("label"), "coords": coords})

    return results

# Import routers
from .api.auth import router as auth_router
from .api.routes import router as routes_router
from .api.polygons import router as polygons_router

app.include_router(auth_router)
app.include_router(routes_router)
app.include_router(polygons_router)
