import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from fastapi.concurrency import run_in_threadpool

logger = logging.getLogger("backend.routes")

router = APIRouter()

class RouteReq(BaseModel):
    origin: list  # [lon, lat]
    destination: list
    profile: str = "driving-car"
    avoid_polygons: Optional[dict] = None
    simplify_tolerance: Optional[float] = 0.0001


from .route import call_ors_directions


async def _round_coords_in_geom(geom, ndigits=6):
    """Round all float coordinates in a GeoJSON geometry recursively."""
    typ = geom.get('type')
    if typ == 'Polygon':
        return {'type': 'Polygon', 'coordinates': [[[round(float(x), ndigits), round(float(y), ndigits)] for (x, y) in ring] for ring in geom.get('coordinates', [])]}
    if typ == 'MultiPolygon':
        new_mp = []
        for poly in geom.get('coordinates', []):
            new_poly = [[[round(float(x), ndigits), round(float(y), ndigits)] for (x, y) in ring] for ring in poly]
            new_mp.append(new_poly)
        return {'type': 'MultiPolygon', 'coordinates': new_mp}
    # Fallback: return as-is
    return geom


async def try_ors_with_avoid(url, body, unioned_geom, initial_tol):
    tol = initial_tol or 0.0001
    max_attempts = 3
    attempt = 0
    last_resp = None
    async with httpx.AsyncClient(timeout=30) as client:
        while attempt < max_attempts:
            attempt += 1
            try:
                simplified = unioned_geom.simplify(tol, preserve_topology=True)
            except Exception:
                logger.exception('Simplify failed; using unioned geometry')
                simplified = unioned_geom

            geom = mapping(simplified)
            # Ensure ORS receives a MultiPolygon when possible
            if geom.get('type') == 'Polygon':
                geom = {'type': 'MultiPolygon', 'coordinates': [geom.get('coordinates', [])]}

            geom = await _round_coords_in_geom(geom)

            # ORS expects avoid_polygons to be a GeoJSON geometry object (NOT a FeatureCollection)
            # Correct format: {"type": "MultiPolygon", "coordinates": [...]}
            local_body = {**body, 'options': {"avoid_polygons": geom}}

            # For debugging large payloads, log a short summary (count of coordinate characters)
            coord_count = len(str(geom.get('coordinates')))
            logger.info('Attempt %s: simplify_tol=%s, geom_type=%s, coords_len=%s', 
                       attempt, tol, geom.get('type'), coord_count)

            try:
                last_resp = await client.post(url, json=local_body)
            except httpx.HTTPError:
                logger.exception('Network error when calling ORS directions (attempt %s)', attempt)
                tol *= 10
                continue

            if last_resp and last_resp.status_code == 200:
                return last_resp

            if last_resp and (last_resp.status_code >= 500 or last_resp.status_code in (413, 429, 504)):
                logger.warning('ORS returned %s on attempt %s; increasing simplify tol (%s) and retrying', last_resp.status_code, attempt, tol)
                tol *= 10
                continue

            # 400 with avoid_polygons often means format issues; try a more conservative representation
            if last_resp and last_resp.status_code == 400:
                logger.warning('ORS returned 400 for avoid_polygons; attempting bbox + convex-hull approximations and retry')
                tried = False
                try:
                    # Try a bbox approximation of the unioned geometry as a simple polygon
                    minx, miny, maxx, maxy = unioned_geom.bounds
                    bbox_geom = {'type': 'MultiPolygon', 'coordinates': [[[[minx, miny], [minx, maxy], [maxx, maxy], [maxx, miny], [minx, miny]]]]}
                    tried = True
                    last_resp = await client.post(url, json={**body, 'options': {'avoid_polygons': bbox_geom}})
                except Exception:
                    logger.exception('Failed to send bbox approximation to ORS')
                    last_resp = None

                if last_resp and last_resp.status_code == 200:
                    return last_resp

                # Try convex hull (simpler geometry)
                try:
                    hull = unioned_geom.convex_hull
                    hull_geom = mapping(hull)
                    if hull_geom.get('type') == 'Polygon':
                        hull_geom = {'type': 'MultiPolygon', 'coordinates': [hull_geom.get('coordinates', [])]}
                    hull_geom = await _round_coords_in_geom(hull_geom)
                    last_resp = await client.post(url, json={**body, 'options': {'avoid_polygons': hull_geom}})
                except Exception:
                    logger.exception('Failed to send convex hull approximation to ORS')
                    last_resp = None

                if last_resp and last_resp.status_code == 200:
                    return last_resp

                # Try simplified hull if still failing
                try:
                    simp = unioned_geom.simplify(tol * 10, preserve_topology=True)
                    simp_hull = simp.convex_hull
                    simp_geom = mapping(simp_hull)
                    if simp_geom.get('type') == 'Polygon':
                        simp_geom = {'type': 'MultiPolygon', 'coordinates': [simp_geom.get('coordinates', [])]}
                    simp_geom = await _round_coords_in_geom(simp_geom)
                    last_resp = await client.post(url, json={**body, 'options': {'avoid_polygons': simp_geom}})
                except Exception:
                    logger.exception('Failed to send simplified hull to ORS')
                    last_resp = None

                if last_resp and last_resp.status_code == 200:
                    return last_resp

            logger.error('ORS returned %s during avoid_polygons attempt: %s', last_resp.status_code if last_resp else 'no_resp', (last_resp.text[:200] if last_resp else ''))
            break

    return None


# Import local routing helpers with multiple fallbacks to support different uvicorn invocation styles
try:
    # Preferred when running as package (uvicorn app.main:app)
    from ..models.route_model import compute_local_route_sync, compute_local_route_penalty
except Exception:
    try:
        # When running from parent folder or with top-level package 'app'
        from app.models.route_model import compute_local_route_sync, compute_local_route_penalty
    except Exception:
        # Last resort: try importing as a sibling module when running from inside `app` folder
        from models.route_model import compute_local_route_sync, compute_local_route_penalty



@router.post("/api/route")
async def route(req: RouteReq, debug: bool = False, force_local: bool = False):  # debug=True enables extra metadata for troubleshooting
    # force_local=True bypasses ORS and executes local fallback directly (useful for testing)
    ORS_KEY = os.getenv("ORS_API_KEY")
    if not ORS_KEY:
        logger.error("Route called but ORS_API_KEY not configured")
        raise HTTPException(status_code=500, detail="ORS_API_KEY not configured on server")

    url = f"https://api.openrouteservice.org/v2/directions/{req.profile}/geojson?api_key={ORS_KEY}"
    body = {"coordinates": [req.origin, req.destination]}

    # If force_local is set, skip ORS entirely and try the local routing fallback directly
    if force_local:
        logger.info('force_local=True: skipping ORS and using local routing')
        try:
            coords_local = await run_in_threadpool(compute_local_route_sync, req.origin, req.destination, req.avoid_polygons)
            if debug:
                return {"coords": coords_local, "source": "local"}
            return {"coords": coords_local}
        except Exception:
            logger.exception('Local fallback failed when forced')
            raise HTTPException(status_code=502, detail='Local fallback failed or unavailable')

    r = None
    if req.avoid_polygons:
        logger.info('avoid_polygons received in request; processing...')
        try:
            geo = req.avoid_polygons
            feats = []
            if geo.get('type') == 'FeatureCollection':
                feats = geo.get('features', [])
                logger.info('Received FeatureCollection with %s features', len(feats))
            elif geo.get('type') == 'Feature':
                feats = [geo]
                logger.info('Received single Feature')
            elif 'geometry' in geo:
                feats = [geo]
                logger.info('Received geometry dict directly')

            geoms = []
            for f in feats:
                geom = f.get('geometry') if f.get('type') == 'Feature' else f
                if not geom:
                    continue
                try:
                    geoms.append(shape(geom))
                except Exception:
                    logger.exception('Invalid geometry in avoid_polygons feature; skipping')

            if geoms:
                logger.info('Successfully parsed %s geometries; computing union...', len(geoms))
                unioned = unary_union(geoms)
                logger.info('Union complete; calling ORS with avoid_polygons...')
                r = await try_ors_with_avoid(url, body, unioned, req.simplify_tolerance or 0.0001)
                
                if r and r.status_code == 200:
                    logger.info('ORS accepted avoid_polygons and returned route successfully')
                else:
                    logger.warning('ORS rejected avoid_polygons (status: %s)', r.status_code if r else 'None')

                # If ORS failed to compute with avoid_polygons, try a penalty-based local routing that
                # prefers routes with less overlap instead of hard-blocking edges.
                if r is None:
                    try:
                        coords_penalty = await run_in_threadpool(compute_local_route_penalty, req.origin, req.destination, unioned)
                        if coords_penalty:
                            logger.info('Local penalty-based route found')
                            if debug:
                                return {"coords": coords_penalty, "source": "local-penalty"}
                            return {"coords": coords_penalty}
                    except Exception:
                        logger.exception('Penalty-based local routing failed; will try other fallbacks')
        except Exception:
            logger.exception('Failed to process avoid_polygons')

    if r is None:
        try:
            r = await call_ors_directions(url, body)
        except httpx.HTTPError as e:
            logger.exception("Network error when calling ORS directions")
            raise HTTPException(status_code=502, detail=f"Network error when contacting ORS: {str(e)}")

    if r.status_code == 200:
        data = r.json()
        features = data.get("features")
        if not features:
            raise HTTPException(status_code=404, detail="No route found")
        feat = features[0]
        coords = feat["geometry"]["coordinates"]
        converted = [[lat, lon] for lon, lat in coords]
        # Return only the coordinates (no summary/raw) so frontend doesn't show route calculation details
        if debug:
            return {"coords": converted, "source": "ors"}
        return {"coords": converted}

    logger.error("ORS returned error for route: %s %s", r.status_code, r.text)
    # Try local fallback
    try:
        coords_local = await run_in_threadpool(compute_local_route_sync, req.origin, req.destination, req.avoid_polygons)
        if debug:
            return {"coords": coords_local, "source": "local"}
        return {"coords": coords_local}
    except Exception:
        logger.exception("Local fallback failed or is unavailable")
        raise HTTPException(status_code=502, detail="ORS error and local fallback failed or unavailable")
