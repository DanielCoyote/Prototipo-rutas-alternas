import logging
import os
import json
from fastapi import APIRouter, HTTPException
from shapely.geometry import shape, mapping
from shapely.ops import transform as shapely_transform
from pyproj import Transformer

logger = logging.getLogger("backend.polygons")

router = APIRouter()

@router.get("/api/polygons")
async def polygons(bbox: str = None, mode: str = "raw", simplify_tol: float = 0.00005):
    """Serve polygons GeoJSON from backend data folder.
    Always reprojects to EPSG:4326 (required by ORS).
    Simplifies polygons for efficiency (ORS has limits on complexity).
    Query params:
      - bbox: str (minLon,minLat,maxLon,maxLat) to filter by bounding box
      - simplify_tol: float (default 0.001 degrees ~100m) to control polygon simplification
    """
    # data file lives in backend/app/data
    data_file = os.path.join(os.path.dirname(__file__), "..", "data", "zonas_historicamente_inundables_(2024).geojson")
    if not os.path.exists(data_file):
        logger.error("Polygons request but data file missing: %s", data_file)
        raise HTTPException(status_code=404, detail="Polygons dataset not found on server")

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            geo = json.load(f)
    except Exception:
        logger.exception("Failed reading polygons file")
        raise HTTPException(status_code=500, detail="Failed reading polygons data")

    # Validate basic structure
    if not isinstance(geo, dict) or geo.get('type') != 'FeatureCollection':
        logger.error("Polygons file is not a FeatureCollection")
        raise HTTPException(status_code=500, detail="Polygons data invalid: expected FeatureCollection")

    # ALWAYS reproject to EPSG:4326 (required by ORS)
    src_crs = geo.get('crs', {}).get('properties', {}).get('name') or 'EPSG:6369'
    target_crs = 'EPSG:4326'
    
    new_feats = []
    if src_crs and '4326' not in src_crs:
        logger.info('Reprojecting GeoJSON from %s to %s', src_crs, target_crs)
        try:
            transformer = Transformer.from_crs(src_crs, target_crs, always_xy=True)
        except Exception:
            logger.exception('Failed to create transformer for reprojection')
            raise HTTPException(status_code=500, detail='Failed to reproject polygons (invalid source CRS)')

        for f in geo.get('features', []):
            geom = f.get('geometry')
            if not geom:
                continue
            try:
                shap = shape(geom)
                # Reproject
                proj_shap = shapely_transform(transformer.transform, shap)
                # Simplify aggressively (reduce verts for ORS compatibility)
                simplified = proj_shap.simplify(simplify_tol, preserve_topology=True)
                new_f = f.copy()
                new_f['geometry'] = mapping(simplified)
                new_feats.append(new_f)
            except Exception:
                logger.exception('Failed to reproject/simplify a feature; skipping')
    else:
        # Already in EPSG:4326, just simplify
        for f in geo.get('features', []):
            geom = f.get('geometry')
            if not geom:
                continue
            try:
                shap = shape(geom)
                simplified = shap.simplify(simplify_tol, preserve_topology=True)
                new_f = f.copy()
                new_f['geometry'] = mapping(simplified)
                new_feats.append(new_f)
            except Exception:
                logger.exception('Failed to simplify feature; skipping')

    geo_out = {'type': 'FeatureCollection', 'features': new_feats}

    # If client requested a bbox, filter
    if not bbox:
        return geo_out

    try:
        minLon, minLat, maxLon, maxLat = map(float, bbox.split(','))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid bbox parameter. Use minLon,minLat,maxLon,maxLat")

    def feature_bbox(feature):
        geom = feature.get('geometry', {})
        coords = geom.get('coordinates', [])
        lons = []
        lats = []

        def collect(points):
            for p in points:
                if isinstance(p[0], (float, int)):
                    lons.append(p[0]); lats.append(p[1])
                else:
                    collect(p)

        collect(coords)
        if not lons:
            return None
        return (min(lons), min(lats), max(lons), max(lats))

    filtered = []
    for f in geo_out.get('features', []):
        fb = feature_bbox(f)
        if not fb:
            continue
        fminLon, fminLat, fmaxLon, fmaxLat = fb
        # check bbox intersection
        if fmaxLon < minLon or fminLon > maxLon or fmaxLat < minLat or fminLat > maxLat:
            continue
        filtered.append(f)

    return {"type": "FeatureCollection", "features": filtered}
