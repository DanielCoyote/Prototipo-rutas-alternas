import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from tqdm import tqdm
import json
import os

# Archivos de entrada y salida
INPUT_CSV = "data-2025-09-18.csv"
OUTPUT_EXCEL = "data_iztapalapa_con_calles.xlsx"
CACHE_FILE = "cache_geocoding.json"

print("📥 Leyendo archivo CSV...")
print("⏳ Este archivo es grande, puede tomar un momento...")

# Leer CSV con codificación latin-1 para preservar caracteres especiales (ñ, acentos)
df = pd.read_csv(INPUT_CSV, encoding='latin-1')
print(f"✔️ Se leyeron {len(df):,} reportes en total")

print("\n🔍 Filtrando datos...")

# Filtro 1: Solo alcaldía Iztapalapa
print("  🏘️ Filtrando por alcaldía: Iztapalapa")
df_filtrado = df[df['alcaldia_catalogo'] == 'Iztapalapa'].copy()
print(f"  ✔️ Reportes en Iztapalapa: {len(df_filtrado):,}")

# Filtro 2: Solo tipos de reporte relevantes para inundaciones y rutas alternas
reportes_relevantes = [
    'Encharcamiento',
    'Drenaje Obstruido',
    'Coladera sin tapa',
    'Boca de tormenta',
    'Hundimiento',
    'Socavon',
    'Pozo de visita'
]

print(f"\n  📋 Filtrando por tipos de reporte relevantes:")
for reporte in reportes_relevantes:
    print(f"     • {reporte}")

df_filtrado = df_filtrado[df_filtrado['reporte'].isin(reportes_relevantes)].copy()
print(f"\n  ✔️ Reportes después del filtro: {len(df_filtrado):,}")

# Eliminar filas con coordenadas faltantes
print("\n  🗺️ Eliminando registros sin coordenadas...")
registros_antes = len(df_filtrado)
df_filtrado = df_filtrado.dropna(subset=['latitud', 'longitud'])
print(f"  ✔️ Registros válidos con coordenadas: {len(df_filtrado):,} (eliminados: {registros_antes - len(df_filtrado):,})")

# Estadísticas por tipo de reporte
print("\n📈 Distribución de reportes filtrados:")
conteo_reportes = df_filtrado['reporte'].value_counts()
for reporte, cantidad in conteo_reportes.items():
    print(f"  • {reporte}: {cantidad:,}")

# ===== GEOCODIFICACIÓN INVERSA CON NOMINATIM =====
print("\n" + "="*70)
print("🗺️ INICIANDO GEOCODIFICACIÓN INVERSA CON NOMINATIM")
print("="*70)
print("⏳ Esto tomará aproximadamente 50-60 minutos para 2,928 registros")
print("💾 El progreso se guarda automáticamente cada 50 registros")
print("🔄 Si se interrumpe, el script continuará desde donde se quedó")
print()

# Cargar caché si existe
cache = {}
if os.path.exists(CACHE_FILE):
    print("📂 Cargando caché de geocodificación existente...")
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"  ✔️ Caché cargado: {len(cache):,} coordenadas ya procesadas")
    except:
        print("  ⚠️ Error al cargar caché, se creará uno nuevo")
        cache = {}

# Inicializar geocodificador de Nominatim
geolocator = Nominatim(user_agent="iztapalapa_flood_routes_v1", timeout=10)

def obtener_calle(lat, lon, max_reintentos=3):
    """Obtiene la información de calle usando geocodificación inversa"""
    # Crear clave única para caché
    cache_key = f"{lat:.6f},{lon:.6f}"
    
    # Verificar si ya está en caché
    if cache_key in cache:
        return cache[cache_key]['calle'], cache[cache_key]['colonia']
    
    for intento in range(max_reintentos):
        try:
            # Respetar límite de 1 solicitud por segundo de Nominatim
            time.sleep(1.1)
            
            location = geolocator.reverse(f"{lat}, {lon}", language='es')
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                # Intentar obtener la calle en orden de preferencia
                calle = (address.get('road') or 
                        address.get('pedestrian') or 
                        address.get('path') or 
                        address.get('footway') or
                        address.get('street') or
                        'Sin nombre de calle')
                
                colonia = (address.get('neighbourhood') or 
                          address.get('suburb') or 
                          address.get('quarter') or
                          'N/A')
                
                # Guardar en caché
                cache[cache_key] = {'calle': calle, 'colonia': colonia}
                
                return calle, colonia
            else:
                cache[cache_key] = {'calle': 'No disponible', 'colonia': 'N/A'}
                return 'No disponible', 'N/A'
                
        except GeocoderTimedOut:
            if intento < max_reintentos - 1:
                time.sleep(2)
                continue
            else:
                cache[cache_key] = {'calle': 'Timeout', 'colonia': 'N/A'}
                return 'Timeout', 'N/A'
                
        except GeocoderServiceError as e:
            cache[cache_key] = {'calle': 'Error de servicio', 'colonia': 'N/A'}
            return 'Error de servicio', 'N/A'
            
        except Exception as e:
            print(f"  ⚠️ Error inesperado: {e}")
            cache[cache_key] = {'calle': 'Error', 'colonia': 'N/A'}
            return 'Error', 'N/A'
    
    return 'Error', 'N/A'

def guardar_cache():
    """Guarda el caché en disco"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# Resetear índice para facilitar iteración
df_filtrado = df_filtrado.reset_index(drop=True)

# Aplicar geocodificación inversa a cada zona
calles = []
colonias_nominatim = []
total = len(df_filtrado)
contador_guardado = 0

print(f"🚀 Procesando {total:,} reportes...")
print()

for idx in tqdm(range(total), desc="Geocodificando", unit="reporte"):
    row = df_filtrado.iloc[idx]
    lat = row['latitud']
    lon = row['longitud']
    
    calle, colonia = obtener_calle(lat, lon)
    calles.append(calle)
    colonias_nominatim.append(colonia)
    
    # Guardar caché cada 50 registros
    contador_guardado += 1
    if contador_guardado >= 50:
        guardar_cache()
        contador_guardado = 0

# Guardar caché final
guardar_cache()
print("\n✔️ Geocodificación completada")

# Agregar columnas al DataFrame
df_filtrado['CALLE_NOMINATIM'] = calles
df_filtrado['COLONIA_NOMINATIM'] = colonias_nominatim

# Estadísticas de geocodificación
print("\n📊 Resultados de geocodificación:")
calles_encontradas = sum(1 for c in calles if c not in ['Sin nombre de calle', 'No disponible', 'Timeout', 'Error', 'Error de servicio'])
print(f"  • Calles identificadas: {calles_encontradas:,} ({calles_encontradas/total*100:.1f}%)")
print(f"  • Sin nombre: {calles.count('Sin nombre de calle'):,}")
print(f"  • No disponible: {calles.count('No disponible'):,}")
print(f"  • Errores/Timeout: {calles.count('Timeout') + calles.count('Error') + calles.count('Error de servicio'):,}")

# Guardar a Excel
print(f"\n💾 Guardando archivo Excel: {OUTPUT_EXCEL}")
df_filtrado.to_excel(OUTPUT_EXCEL, index=False, engine='openpyxl')

print(f"\n🎉 ¡Proceso completado exitosamente!")
print(f"📊 Resumen:")
print(f"   • Reportes procesados: {len(df_filtrado):,}")
print(f"   • Calles identificadas: {calles_encontradas:,}")
print(f"   • Archivo guardado: {OUTPUT_EXCEL}")
print(f"   • Caché guardado: {CACHE_FILE} ({len(cache):,} coordenadas)")
print(f"\n✅ Ahora puedes ejecutar el script de conteo de calles")
