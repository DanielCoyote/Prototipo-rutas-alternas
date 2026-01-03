"""
Script para extraer puntos estratégicos cercanos a zonas de inundación
Analiza el GeoJSON y encuentra centroides de polígonos para tests
"""

import json
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer

# Ruta al GeoJSON
GEOJSON_PATH = "app/data/zonas_historicamente_inundables_(2024).geojson"

# Transformador de coordenadas EPSG:6369 → EPSG:4326 (WGS84)
transformer = Transformer.from_crs('EPSG:6369', 'EPSG:4326', always_xy=True)

def transform_geom(geom):
    """Reproyecta geometría de EPSG:6369 a EPSG:4326"""
    return transform(transformer.transform, geom)

def main():
    print("Cargando GeoJSON...")
    with open(GEOJSON_PATH, encoding='utf-8') as f:
        geojson = json.load(f)
    
    features = geojson['features']
    print(f"Total de polígonos: {len(features)}\n")
    
    print("=" * 80)
    print("CENTROIDES DE POLÍGONOS (primeros 20)")
    print("=" * 80)
    
    puntos = []
    
    for i, feature in enumerate(features[:20]):
        # Crear geometría shapely
        geom_6369 = shape(feature['geometry'])
        
        # Calcular centroide en EPSG:6369
        centroid_6369 = geom_6369.centroid
        
        # Reproyectar a WGS84
        centroid_4326 = transform_geom(centroid_6369)
        lon, lat = centroid_4326.x, centroid_4326.y
        
        # Calcular área (aproximada)
        geom_4326 = transform_geom(geom_6369)
        area = geom_4326.area  # En grados cuadrados (aproximado)
        
        puntos.append({
            'id': i + 1,
            'lon': lon,
            'lat': lat,
            'area': area
        })
        
        print(f"{i+1:2d}. Lon: {lon:.6f}, Lat: {lat:.6f} | Área: {area:.8f}")
    
    print("\n" + "=" * 80)
    print("5 POLÍGONOS MÁS GRANDES (mayor área)")
    print("=" * 80)
    
    # Ordenar por área descendente
    puntos_grandes = sorted(puntos, key=lambda p: p['area'], reverse=True)[:5]
    
    for i, p in enumerate(puntos_grandes):
        print(f"{i+1}. ID {p['id']}: [{p['lon']:.6f}, {p['lat']:.6f}] - Área: {p['area']:.8f}")
    
    print("\n" + "=" * 80)
    print("FORMATO PARA TESTS (copiar a flood-zones-routes.spec.ts)")
    print("=" * 80)
    print("\nconst DIRECCIONES = [")
    for i, p in enumerate(puntos_grandes):
        nombre = f"Zona Inundable {i+1}"
        print(f"  {{ nombre: '{nombre}', coords: [{p['lon']:.6f}, {p['lat']:.6f}] }},")
    print("];\n")
    
    print("=" * 80)
    print("PUNTOS ALEATORIOS DISTRIBUIDOS")
    print("=" * 80)
    
    # Seleccionar polígonos distribuidos (inicio, 25%, 50%, 75%, final)
    indices = [0, len(features)//4, len(features)//2, 3*len(features)//4, len(features)-1]
    
    print("\nconst DIRECCIONES_DISTRIBUIDAS = [")
    for idx in indices:
        feature = features[idx]
        geom_6369 = shape(feature['geometry'])
        centroid_4326 = transform_geom(geom_6369.centroid)
        lon, lat = centroid_4326.x, centroid_4326.y
        print(f"  {{ nombre: 'Punto {idx+1}', coords: [{lon:.6f}, {lat:.6f}] }},")
    print("];\n")

if __name__ == "__main__":
    main()
