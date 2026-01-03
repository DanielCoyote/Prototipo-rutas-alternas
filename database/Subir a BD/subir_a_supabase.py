import json
from supabase import create_client

SUPABASE_URL = "https://gohmisbqxbelivigqyyd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdvaG1pc2JxeGJlbGl2aWdxeXlkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDUzNDAwMSwiZXhwIjoyMDgwMTEwMDAxfQ.68RwLsWJzqDXAYYQkvPVxV3UBgu3nY78mRSpaF80ZY8"  # ideal para scripts privados (NO frontend)

GEOJSON_PATH = "zonas_inundables_iztapalapa_completo.geojson"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Limpia la tabla antes de insertar
supabase.rpc("reset_risk_zones", {}).execute()

with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
    fc = json.load(f)

for feat in fc["features"]:
    props = feat.get("properties") or {}
    geom = feat.get("geometry")
    if not geom:
        continue

    supabase.rpc("insert_risk_zone", {
        "p_source": props.get("fuente", "DGSU"),
        "p_severity": props.get("intensidad", 3),
        "p_description": props.get("detalles") or props.get("descripcio") or "Zona inundable",
        "p_geom_geojson": json.dumps(geom, ensure_ascii=False)
    }).execute()

print("✅ Listo")
