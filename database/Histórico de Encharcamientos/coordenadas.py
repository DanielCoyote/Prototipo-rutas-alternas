import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import json
import re

INPUT_EXCEL = "calles_recurrentes_iztapalapa.xlsx"
OUTPUT_EXCEL = "calles_coordenadas.xlsx"
OUTPUT_GEOJSON = "calles_coordenadas.geojson"

print("📥 Cargando archivo...")
df = pd.read_excel(INPUT_EXCEL, sheet_name=0)

print(f"✔ Registros cargados: {len(df)}")
print(df.columns.tolist())

# ------------------------------------------------
# 1. NORMALIZAR COLONIA PARA MEJOR GEOCODING
# ------------------------------------------------
def limpiar_colonia(col):
    if pd.isna(col):
        return ""
    col = str(col).strip().upper()

    # Quitar sufijos redundantes
    col = re.sub(r"\s+U\.?H\.?", " UNIDAD HABITACIONAL", col)
    col = re.sub(r"\s+UH\.?", " UNIDAD HABITACIONAL", col)

    # Quitar espacios múltiples
    col = re.sub(r"\s+", " ", col)

    return col.title()  # Lo regresamos con mayúscula inicial

df["COLONIA_LIMPIA"] = df["COLONIA"].apply(limpiar_colonia)

# ------------------------------------------------
# 2. CONSTRUIR DIRECCIÓN COMPLETA
# ------------------------------------------------
def construir_direccion(row):
    calle = str(row["CALLE"]).strip()
    segmento = str(row["SEGMENTO"]).strip()

    if segmento.upper() in ["SIN ESPECIFICAR", "NAN"]:
        segmento = ""

    colonia = row["COLONIA_LIMPIA"]

    direccion = f"{calle} {segmento}, {colonia}, Iztapalapa, Ciudad de México, México"
    direccion = re.sub(r"\s+", " ", direccion).strip()

    return direccion

df["DIRECCION_BUSQUEDA"] = df.apply(construir_direccion, axis=1)

print("\n🧩 Direcciones generadas:")
print(df["DIRECCION_BUSQUEDA"].head())

# ------------------------------------------------
# 3. GEOCODING (NOMINATIM)
# ------------------------------------------------
geolocator = Nominatim(user_agent="rutas_alternas_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

latitudes = []
longitudes = []

print("\n📡 Buscando coordenadas...")

for i, row in df.iterrows():
    direccion = row["DIRECCION_BUSQUEDA"]
    print(f"\n🔎 [{i+1}/{len(df)}] → {direccion}")

    try:
        loc = geocode(direccion)
        if loc:
            print(f"   ✔ ({loc.latitude}, {loc.longitude})")
            latitudes.append(loc.latitude)
            longitudes.append(loc.longitude)
        else:
            print("   ❌ No encontrado")
            latitudes.append(None)
            longitudes.append(None)
    except Exception as e:
        print(f"   ⚠ Error: {e}")
        latitudes.append(None)
        longitudes.append(None)

    time.sleep(1)

df["LAT"] = latitudes
df["LON"] = longitudes

# ------------------------------------------------
# 4. GUARDAR EXCEL
# ------------------------------------------------
df.to_excel(OUTPUT_EXCEL, index=False)
print(f"\n💾 Guardado: {OUTPUT_EXCEL}")

# ------------------------------------------------
# 5. CREAR GEOJSON
# ------------------------------------------------
features = []

for _, row in df.iterrows():
    if pd.isna(row["LAT"]) or pd.isna(row["LON"]):
        continue

    feature = {
        "type": "Feature",
        "properties": {
            "calle": row["CALLE"],
            "segmento": row["SEGMENTO"],
            "colonia": row["COLONIA_LIMPIA"],
            "num_reportes": row.get("NUM_REPORTES", None),
            "causas": row.get("CAUSAS_PRINCIPALES", "")
        },
        "geometry": {
            "type": "Point",
            "coordinates": [float(row["LON"]), float(row["LAT"])]
        }
    }
    features.append(feature)

geojson = {"type": "FeatureCollection", "features": features}

with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=4)

print(f"🌍 GeoJSON generado: {OUTPUT_GEOJSON}")
print("\n🎉 Proceso terminado con éxito.")
