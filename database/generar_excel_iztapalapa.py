import geopandas as gpd
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from tqdm import tqdm

# Archivos de entrada y salida
INPUT_GEOJSON = "zonas_historicamente_inundables_(2024).geojson"
OUTPUT_EXCEL = "zonas_inundables_iztapalapa.xlsx"

print("📥 Leyendo archivo GeoJSON...")
# Leer GeoJSON con proyección original (EPSG:6369)
gdf = gpd.read_file(INPUT_GEOJSON)
print(f"✔️ Se leyeron {len(gdf)} zonas inundables")

print("🔄 Convirtiendo coordenadas a WGS84 (EPSG:4326)...")
# Convertir de EPSG:6369 (proyección local México) a EPSG:4326 (WGS84 para mapas web)
gdf = gdf.to_crs(epsg=4326)
print("✔️ Coordenadas convertidas a WGS84")

print("📍 Calculando centroides y número de vértices...")
# Calcular centroide de cada polígono
gdf['CENTROID_LON'] = gdf.geometry.centroid.x
gdf['CENTROID_LAT'] = gdf.geometry.centroid.y

# Calcular número de vértices en el polígono
gdf['NUM_VERTICES'] = gdf.geometry.apply(lambda g: len(g.exterior.coords) - 1)

print("🗺️ Obteniendo información de calles con geocodificación inversa...")
print("⏳ Esto puede tomar varios minutos (respetando límites de Nominatim)...")

# Inicializar geocodificador de Nominatim
geolocator = Nominatim(user_agent="zonas_inundables_iztapalapa_app", timeout=10)

def obtener_calle(lat, lon, max_reintentos=3):
    """Obtiene la información de calle usando geocodificación inversa"""
    for intento in range(max_reintentos):
        try:
            # Respetar límite de 1 solicitud por segundo de Nominatim
            time.sleep(1)
            
            location = geolocator.reverse(f"{lat}, {lon}", language='es')
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                # Intentar obtener la calle en orden de preferencia
                calle = (address.get('road') or 
                        address.get('pedestrian') or 
                        address.get('path') or 
                        address.get('footway') or
                        address.get('neighbourhood') or
                        address.get('suburb') or
                        'Sin nombre de calle')
                
                colonia = address.get('neighbourhood') or address.get('suburb') or 'N/A'
                
                return calle, colonia
            else:
                return 'No disponible', 'N/A'
                
        except GeocoderTimedOut:
            if intento < max_reintentos - 1:
                time.sleep(2)
                continue
            else:
                return 'Timeout', 'N/A'
                
        except GeocoderServiceError as e:
            return 'Error de servicio', 'N/A'
            
        except Exception as e:
            return 'Error', 'N/A'
    
    return 'Error', 'N/A'

# Aplicar geocodificación inversa a cada zona con barra de progreso
calles = []
colonias = []

for idx, row in tqdm(gdf.iterrows(), total=len(gdf), desc="🔍 Geocodificando zonas", unit="zona"):
    lat = row.geometry.centroid.y
    lon = row.geometry.centroid.x
    
    calle, colonia = obtener_calle(lat, lon)
    calles.append(calle)
    colonias.append(colonia)

gdf['CALLE'] = calles
gdf['COLONIA'] = colonias
print("✔️ Geocodificación completada")

print("📋 Preparando DataFrame para Excel...")
# Convertir a DataFrame sin la columna de geometría
df = pd.DataFrame(gdf.drop(columns='geometry'))

# Renombrar columnas para mejor legibilidad en Excel
df = df.rename(columns={
    'objectid': 'OBJECTID',
    'id': 'ID',
    'fenomeno': 'FENOMENO',
    'taxonomia': 'TAXONOMIA',
    'r_p_v_e': 'R_P_V_E',
    'intensidad': 'INTENSIDAD',
    'descripcio': 'DESCRIPCION',
    'detalles': 'DETALLES',
    'nombre': 'NOMBRE',
    'fuente': 'FUENTE',
    'magni_uni': 'MAGNI_UNI',
    'magni_num': 'MAGNI_NUM',
    'cve_mun': 'CVE_MUN',
    'alcaldia': 'ALCALDIA',
    'entidad': 'ENTIDAD',
    'area_m2': 'AREA_M2',
    'perime_m': 'PERIMETRO_M'
})

# Reordenar columnas para mejor organización
columnas_ordenadas = [
    'OBJECTID',
    'ID',
    'NOMBRE',
    'CALLE',
    'COLONIA',
    'ALCALDIA',
    'CVE_MUN',
    'ENTIDAD',
    'AREA_M2',
    'PERIMETRO_M',
    'CENTROID_LAT',
    'CENTROID_LON',
    'NUM_VERTICES',
    'FENOMENO',
    'TAXONOMIA',
    'R_P_V_E',
    'INTENSIDAD',
    'DESCRIPCION',
    'DETALLES',
    'FUENTE',
    'MAGNI_UNI',
    'MAGNI_NUM'
]

df = df[columnas_ordenadas]

print(f"💾 Guardando archivo Excel: {OUTPUT_EXCEL}")
# Guardar a Excel
df.to_excel(OUTPUT_EXCEL, index=False, engine='openpyxl')

print(f"🎉 ¡Archivo Excel generado exitosamente!")
print(f"📊 Total de zonas inundables: {len(df)}")
print(f"📈 Área total: {df['AREA_M2'].sum():,.2f} m²")
print(f"📏 Área promedio por zona: {df['AREA_M2'].mean():,.2f} m²")
print(f"📍 Archivo guardado: {OUTPUT_EXCEL}")
