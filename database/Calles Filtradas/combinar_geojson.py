import json

# Archivos de entrada
ARCHIVO_ZONAS = 'zonas_iztapalapa_4326.geojson'
ARCHIVO_CALLES = 'calles_inundables_iztapalapa.geojson'
ARCHIVO_SALIDA = 'zonas_inundables_iztapalapa_completo.geojson'

print("Leyendo archivos GeoJSON...")


# Leer archivo de zonas históricas
with open(ARCHIVO_ZONAS, 'r', encoding='utf-8') as f:
    zonas_data = json.load(f)
    
# Leer archivo de calles
with open(ARCHIVO_CALLES, 'r', encoding='utf-8') as f:
    calles_data = json.load(f)

print(f"Zonas históricas: {len(zonas_data['features'])} features")
print(f"Calles con reportes: {len(calles_data['features'])} features")

# Combinar features
features_combinados = []

# Agregar zonas históricas (mantener sus IDs originales y asignar severidad 3)
for feature in zonas_data['features']:
    # Asignar severidad 3 a las zonas históricas
    feature['properties']['intensidad'] = '3'
    features_combinados.append(feature)

# Agregar calles (ajustar IDs para que sean secuenciales)
offset_id = len(zonas_data['features'])
for idx, feature in enumerate(calles_data['features']):
    # Ajustar objectid e id para que sean secuenciales
    feature['properties']['objectid'] = offset_id + idx + 1
    feature['properties']['id'] = offset_id + idx + 1
    features_combinados.append(feature)

print(f"\nTotal de features combinados: {len(features_combinados)}")

# Crear GeoJSON combinado con el mismo formato
geojson_combinado = {
    "type": "FeatureCollection",
    "name": "zonas_inundables_iztapalapa_completo",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },
    "features": features_combinados
}

# Guardar archivo combinado
print(f"\nGuardando archivo combinado: {ARCHIVO_SALIDA}")
with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
    json.dump(geojson_combinado, f, ensure_ascii=False, indent=2)

print(f"\n✓ Archivo combinado generado exitosamente!")
print(f"✓ Total de zonas de inundación: {len(features_combinados)}")
print(f"  - Zonas históricas (IDs 1-{len(zonas_data['features'])}): {len(zonas_data['features'])}")
print(f"  - Calles con reportes (IDs {offset_id + 1}-{len(features_combinados)}): {len(calles_data['features'])}")
print(f"\nArchivo listo para Supabase: {ARCHIVO_SALIDA}")
