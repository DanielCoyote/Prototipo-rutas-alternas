import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json

# Configuración
ARCHIVO_EXCEL = 'analisis_calles_iztapalapa.xlsx'
HOJA = 'Calles_Mas_Reportadas'
ARCHIVO_SALIDA = 'calles_inundables_iztapalapa.geojson'
RADIO_METROS = 50
PUNTOS_CIRCULO = 32

print("Leyendo datos del archivo Excel...")
# Leer datos del Excel
df = pd.read_excel(ARCHIVO_EXCEL, sheet_name=HOJA)

print(f"Total de registros leídos: {len(df)}")

# Filtrar: excluir calles con solo 1 reporte
df_filtrado = df[df['NUM_REPORTES'] > 1].copy()
print(f"Registros después de filtrar (NUM_REPORTES > 1): {len(df_filtrado)}")

# Clasificar severidad
def clasificar_severidad(num_reportes):
    if 2 <= num_reportes <= 5:
        return 1
    elif 6 <= num_reportes <= 12:
        return 2
    else:  # > 12
        return 3

df_filtrado['severidad'] = df_filtrado['NUM_REPORTES'].apply(clasificar_severidad)

print("\nGenerando polígonos circulares...")
# Crear geometrías (puntos)
geometry = [Point(lon, lat) for lon, lat in 
            zip(df_filtrado['COORDENADA_PROMEDIO_LON'], 
                df_filtrado['COORDENADA_PROMEDIO_LAT'])]

# Crear GeoDataFrame en WGS84
gdf = gpd.GeoDataFrame(df_filtrado, geometry=geometry, crs='EPSG:4326')

# Proyectar a UTM zona 14N (CDMX) para cálculos métricos
gdf_utm = gdf.to_crs('EPSG:32614')

# Crear círculos (buffer) de 50m con 32 segmentos
gdf_utm['geometry'] = gdf_utm.geometry.buffer(RADIO_METROS, resolution=PUNTOS_CIRCULO)

# Calcular área y perímetro en metros
gdf_utm['area_m2'] = gdf_utm.geometry.area
gdf_utm['perime_m'] = gdf_utm.geometry.length

# Reproyectar de vuelta a WGS84 (EPSG:4326)
gdf_final = gdf_utm.to_crs('EPSG:4326')

print("Construyendo estructura GeoJSON...")
# Construir la estructura GeoJSON manualmente para que coincida con el formato original
features = []

for idx, row in gdf_final.iterrows():
    # Obtener coordenadas del polígono
    coords = list(row.geometry.exterior.coords)
    
    # Crear feature con propiedades similares al GeoJSON original
    feature = {
        "type": "Feature",
        "properties": {
            "objectid": idx + 1,
            "id": idx + 1,
            "fenomeno": "HIDROMETEOROLOGICO",
            "taxonomia": "INUNDACIONES",
            "r_p_v_e": "PELIGRO",
            "intensidad": str(row['severidad']),
            "descripcio": "CALLES CON REPORTES DE INUNDACION EN IZTAPALAPA",
            "detalles": f"ZONA DE INUNDACION BASADA EN {int(row['NUM_REPORTES'])} REPORTES HISTORICOS",
            "nombre": str(row['CALLE']),
            "fuente": "ANALISIS REPORTES",
            "magni_uni": "N/A",
            "magni_num": "N/A",
            "cve_mun": "09007",
            "alcaldia": "IZTAPALAPA",
            "entidad": "CDMX",
            "area_m2": round(row['area_m2'], 2),
            "perime_m": round(row['perime_m'], 2)
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    }
    
    features.append(feature)

# Crear FeatureCollection con CRS
geojson_dict = {
    "type": "FeatureCollection",
    "name": "calles_inundables_iztapalapa",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },
    "features": features
}

# Guardar archivo GeoJSON
print(f"\nGuardando archivo GeoJSON: {ARCHIVO_SALIDA}")
with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
    json.dump(geojson_dict, f, ensure_ascii=False, indent=2)

print(f"\n✓ Proceso completado exitosamente!")
print(f"✓ Total de zonas generadas: {len(features)}")
print(f"✓ Distribución por severidad:")
print(f"  - Severidad 1 (2-5 reportes): {len(df_filtrado[df_filtrado['severidad'] == 1])}")
print(f"  - Severidad 2 (6-12 reportes): {len(df_filtrado[df_filtrado['severidad'] == 2])}")
print(f"  - Severidad 3 (>12 reportes): {len(df_filtrado[df_filtrado['severidad'] == 3])}")
print(f"\nArchivo generado: {ARCHIVO_SALIDA}")
