import logging
import json
from fastapi import APIRouter, HTTPException
from ..core.config import supabase

logger = logging.getLogger("backend.polygons")

router = APIRouter()

@router.get("/api/polygons")
async def polygons(bbox: str = None):
    """
    Serve polygons GeoJSON from Supabase risk_zones table.
    Returns polygons with severity information for color coding.
    Query params:
      - bbox: str (minLon,minLat,maxLon,maxLat) to filter by bounding box (optional)
    """
    try:
        # Query risk_zones from Supabase
        # ST_AsGeoJSON converts PostGIS geometry to GeoJSON format
        response = supabase.rpc(
            'get_risk_zones_geojson',
            {}
        ).execute()
        
        if not response.data:
            logger.warning("No risk zones found in database")
            return {"type": "FeatureCollection", "features": []}
        
        # Build FeatureCollection
        features = []
        for zone in response.data:
            if not zone.get('geom_geojson'):
                continue
                
            try:
                geometry = json.loads(zone['geom_geojson'])
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id": zone.get('id'),
                        "severity": zone.get('severity', 3),
                        "source": zone.get('source', 'DGSU'),
                        "description": zone.get('description', 'Zona inundable')
                    },
                    "geometry": geometry
                }
                features.append(feature)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse geometry for zone {zone.get('id')}")
                continue
        
        geo_out = {
            "type": "FeatureCollection",
            "features": features
        }
        
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
                        lons.append(p[0])
                        lats.append(p[1])
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
        
    except Exception as e:
        logger.exception("Failed to load polygons from Supabase")
        raise HTTPException(status_code=500, detail=f"Failed to load risk zones: {str(e)}")
