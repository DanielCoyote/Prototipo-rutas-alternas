-- Función para obtener zonas de riesgo en formato GeoJSON
-- Ejecutar en Supabase SQL Editor

CREATE OR REPLACE FUNCTION get_risk_zones_geojson()
RETURNS TABLE (
  id uuid,
  severity int,
  source text,
  description text,
  geom_geojson text
) 
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    risk_zones.id,
    risk_zones.severity,
    risk_zones.source,
    risk_zones.description,
    ST_AsGeoJSON(risk_zones.geom)::text as geom_geojson
  FROM risk_zones;
END;
$$;
