import pandas as pd
import numpy as np
import json
from shapely.geometry import shape, Polygon
from shapely.ops import unary_union
from tqdm import tqdm
import geopandas as gpd

# Archivos de entrada y salida
INPUT_CSV = "atlas-de-riesgo-inundaciones.csv"
OUTPUT_EXCEL = "analisis_atlas_filtrado_alta_intensidad.xlsx"
OUTPUT_GEOJSON = "atlas_iztapalapa_alta_intensidad.geojson"

print("📥 Leyendo archivo CSV del Atlas de Riesgo...")
df = pd.read_csv(INPUT_CSV, encoding='latin-1')
print(f"✔️ Se leyeron {len(df):,} polígonos de toda la CDMX")

# ===== FILTRADO =====
print("\n🔍 Aplicando filtros...")

# Filtro 1: Solo Iztapalapa
print("  🏘️ Filtro 1: Alcaldía = Iztapalapa")
df_filtrado = df[df['alcaldia'] == 'Iztapalapa'].copy()
print(f"    ✔️ Registros en Iztapalapa: {len(df_filtrado):,}")

# Mostrar distribución de intensidades antes del filtro
print("\n  📊 Distribución de intensidades en Iztapalapa:")
intensidades = df_filtrado['intensidad'].value_counts()
for intensidad, cantidad in intensidades.items():
    print(f"    • {intensidad}: {cantidad} polígonos")

# Filtro 2: Solo intensidad "Muy Alto" y "Alto"
print("\n  ⚠️ Filtro 2: Intensidad = 'Muy Alto' o 'Alto'")
df_filtrado = df_filtrado[df_filtrado['intensidad'].isin(['Muy Alto', 'Alto'])].copy()
print(f"    ✔️ Registros después del filtro: {len(df_filtrado):,}")

# Mostrar distribución después del filtro
print("\n  📊 Distribución de intensidades filtradas:")
intensidades_filtradas = df_filtrado['intensidad'].value_counts()
for intensidad, cantidad in intensidades_filtradas.items():
    print(f"    • {intensidad}: {cantidad} polígonos")

# ===== ANÁLISIS DE DATOS GENERALES =====
print("\n📋 Análisis de datos filtrados:")

# Fenómenos
fenomenos = df_filtrado['fenomeno'].value_counts()
print(f"  • Fenómenos: {', '.join(fenomenos.index.tolist())}")

# R_P_V_E
rpve = df_filtrado['r_p_v_e'].value_counts()
print(f"  • Clasificación R_P_V_E: {', '.join(rpve.index.tolist())}")

# Fuentes
fuentes = df_filtrado['fuente'].value_counts()
print(f"  • Fuentes: {len(fuentes)} únicas")

# ===== CONVERTIR GEOMETRÍAS =====
print("\n🗺️ Convirtiendo geometrías GeoJSON a objetos Shapely...")

geometrias = []
indices_validos = []

for idx, row in tqdm(df_filtrado.iterrows(), total=len(df_filtrado), desc="Procesando geometrías"):
    try:
        geo_json = json.loads(row['geo_shape'])
        geom = shape(geo_json)
        geometrias.append(geom)
        indices_validos.append(idx)
    except Exception as e:
        print(f"  ⚠️ Error en fila {idx}: {e}")
        continue

print(f"✔️ Geometrías válidas procesadas: {len(geometrias)}")

# Crear GeoDataFrame
df_filtrado_valido = df_filtrado.loc[indices_validos].copy()
gdf = gpd.GeoDataFrame(df_filtrado_valido, geometry=geometrias, crs="EPSG:4326")

# Convertir a sistema métrico para cálculos de área
print("\n🔄 Convirtiendo a sistema de coordenadas métrico (EPSG:6369)...")
gdf_metrico = gdf.to_crs(epsg=6369)

# ===== ANÁLISIS DE TAMAÑOS =====
print("\n📏 Analizando tamaños de polígonos...")

# Calcular área en m² y km²
gdf_metrico['area_calculada_m2'] = gdf_metrico.geometry.area
gdf_metrico['area_km2'] = gdf_metrico['area_calculada_m2'] / 1_000_000

# Calcular perímetro
gdf_metrico['perimetro_calculado_m'] = gdf_metrico.geometry.length

# Estadísticas de área
area_stats = {
    'Mínima': gdf_metrico['area_calculada_m2'].min(),
    'Máxima': gdf_metrico['area_calculada_m2'].max(),
    'Media': gdf_metrico['area_calculada_m2'].mean(),
    'Mediana': gdf_metrico['area_calculada_m2'].median(),
    'Desv. Estándar': gdf_metrico['area_calculada_m2'].std(),
    'Total': gdf_metrico['area_calculada_m2'].sum()
}

print("\n📊 Estadísticas de áreas:")
print(f"  • Mínima: {area_stats['Mínima']:,.2f} m² ({area_stats['Mínima']/10_000:.2f} ha)")
print(f"  • Máxima: {area_stats['Máxima']:,.2f} m² ({area_stats['Máxima']/10_000:.2f} ha)")
print(f"  • Media: {area_stats['Media']:,.2f} m² ({area_stats['Media']/10_000:.2f} ha)")
print(f"  • Mediana: {area_stats['Mediana']:,.2f} m² ({area_stats['Mediana']/10_000:.2f} ha)")
print(f"  • Área total: {area_stats['Total']:,.2f} m² ({area_stats['Total']/1_000_000:.2f} km²)")

# Clasificar por tamaño
def clasificar_tamano(area_m2):
    if area_m2 < 10_000:  # < 1 hectárea
        return 'Muy pequeño (< 1 ha)'
    elif area_m2 < 50_000:  # 1-5 hectáreas
        return 'Pequeño (1-5 ha)'
    elif area_m2 < 100_000:  # 5-10 hectáreas
        return 'Mediano (5-10 ha)'
    elif area_m2 < 500_000:  # 10-50 hectáreas
        return 'Grande (10-50 ha)'
    elif area_m2 < 1_000_000:  # 50-100 hectáreas
        return 'Muy grande (50-100 ha)'
    else:  # > 100 hectáreas
        return 'Enorme (> 100 ha)'

gdf_metrico['clasificacion_tamano'] = gdf_metrico['area_calculada_m2'].apply(clasificar_tamano)

print("\n📈 Distribución por tamaño:")
distribucion = gdf_metrico['clasificacion_tamano'].value_counts()
for categoria, cantidad in distribucion.items():
    porcentaje = (cantidad / len(gdf_metrico)) * 100
    print(f"  • {categoria}: {cantidad} polígonos ({porcentaje:.1f}%)")

# Identificar polígonos grandes (> 10 hectáreas)
UMBRAL_GRANDE = 100_000  # 10 hectáreas
poligonos_grandes = gdf_metrico[gdf_metrico['area_calculada_m2'] > UMBRAL_GRANDE].copy()
print(f"\n⚠️ Polígonos grandes (> 10 ha): {len(poligonos_grandes)} de {len(gdf_metrico)} ({len(poligonos_grandes)/len(gdf_metrico)*100:.1f}%)")

if len(poligonos_grandes) > 0:
    area_total_grandes = poligonos_grandes['area_calculada_m2'].sum()
    print(f"  • Área total de polígonos grandes: {area_total_grandes/1_000_000:.2f} km² ({area_total_grandes/area_stats['Total']*100:.1f}% del total)")
    print(f"\n  Top 10 polígonos más grandes:")
    for idx, row in poligonos_grandes.nlargest(10, 'area_calculada_m2').iterrows():
        print(f"    • ID {row['id']}: {row['area_calculada_m2']:,.2f} m² ({row['area_calculada_m2']/10_000:.2f} ha) - Intensidad: {row['intensidad']}")

# Polígonos enormes (> 100 ha)
poligonos_enormes = gdf_metrico[gdf_metrico['area_calculada_m2'] > 1_000_000]
if len(poligonos_enormes) > 0:
    print(f"\n⛔ Polígonos ENORMES (> 100 ha): {len(poligonos_enormes)}")

# ===== ANÁLISIS DE SOBREPOSICIONES =====
print("\n🔍 Analizando sobreposiciones entre polígonos...")
print("  Creando índice espacial...")
sindex = gdf_metrico.sindex

sobreposiciones = []

for idx, row in tqdm(gdf_metrico.iterrows(), total=len(gdf_metrico), desc="Verificando sobreposiciones"):
    possible_matches_index = list(sindex.intersection(row.geometry.bounds))
    possible_matches = gdf_metrico.iloc[possible_matches_index]
    
    for idx2, row2 in possible_matches.iterrows():
        if idx < idx2:
            if row.geometry.intersects(row2.geometry):
                interseccion = row.geometry.intersection(row2.geometry)
                area_interseccion = interseccion.area
                
                if area_interseccion > 1:
                    porcentaje_poly1 = (area_interseccion / row['area_calculada_m2']) * 100
                    porcentaje_poly2 = (area_interseccion / row2['area_calculada_m2']) * 100
                    
                    sobreposiciones.append({
                        'ID_Poligono_1': row['id'],
                        'ID_Poligono_2': row2['id'],
                        'Intensidad_1': row['intensidad'],
                        'Intensidad_2': row2['intensidad'],
                        'Area_Interseccion_m2': area_interseccion,
                        'Porcentaje_Poly1': porcentaje_poly1,
                        'Porcentaje_Poly2': porcentaje_poly2
                    })

print(f"\n✔️ Análisis de sobreposiciones completado")
print(f"  • Sobreposiciones encontradas: {len(sobreposiciones)}")

df_sobreposiciones = None
if len(sobreposiciones) > 0:
    df_sobreposiciones = pd.DataFrame(sobreposiciones)
    df_sobreposiciones = df_sobreposiciones.sort_values('Area_Interseccion_m2', ascending=False)
    
    area_total_sobreposicion = df_sobreposiciones['Area_Interseccion_m2'].sum()
    print(f"  • Área total de sobreposición: {area_total_sobreposicion:,.2f} m² ({area_total_sobreposicion/1_000_000:.4f} km²)")
    
    sobreposiciones_significativas = df_sobreposiciones[
        (df_sobreposiciones['Porcentaje_Poly1'] > 10) | 
        (df_sobreposiciones['Porcentaje_Poly2'] > 10)
    ]
    print(f"  • Sobreposiciones significativas (> 10%): {len(sobreposiciones_significativas)}")
    
    print(f"\n  Top 5 mayores sobreposiciones:")
    for idx, row in df_sobreposiciones.head(5).iterrows():
        print(f"    • IDs {row['ID_Poligono_1']} ({row['Intensidad_1']}) ↔ {row['ID_Poligono_2']} ({row['Intensidad_2']})")
        print(f"      └─ Área: {row['Area_Interseccion_m2']:,.2f} m² ({row['Porcentaje_Poly1']:.1f}% / {row['Porcentaje_Poly2']:.1f}%)")

# ===== ANÁLISIS DE FORMA =====
print("\n📐 Analizando complejidad de formas...")
gdf_metrico['indice_compacidad'] = (4 * np.pi * gdf_metrico['area_calculada_m2']) / (gdf_metrico['perimetro_calculado_m'] ** 2)
print(f"  • Índice de compacidad promedio: {gdf_metrico['indice_compacidad'].mean():.3f}")

# ===== COMPARACIÓN CON DATASET COMPLETO =====
print("\n📊 COMPARACIÓN: Dataset completo vs. Filtrado (Alta intensidad)")
print("="*70)
print(f"{'Métrica':<40} {'Completo':>12} {'Filtrado':>12}")
print("-"*70)
print(f"{'Polígonos':<40} {916:>12,} {len(gdf_metrico):>12,}")
print(f"{'Área total (km²)':<40} {226.17:>12.2f} {area_stats['Total']/1_000_000:>12.2f}")
print(f"{'% de área respecto al total':<40} {'100%':>12} {(area_stats['Total']/226_166_871.86*100):>11.1f}%")
print(f"{'Polígonos grandes (> 10 ha)':<40} {750:>12} {len(poligonos_grandes):>12}")
print(f"{'% polígonos grandes':<40} {'81.9%':>12} {(len(poligonos_grandes)/len(gdf_metrico)*100):>11.1f}%")

# ===== RECOMENDACIONES =====
print("\n💡 EVALUACIÓN PARA LA APLICACIÓN DE RUTAS:")
print("="*70)

cobertura_km2 = area_stats['Total'] / 1_000_000
print(f"📊 COBERTURA TOTAL (Alta intensidad): {cobertura_km2:.2f} km²")
print(f"   Reducción del {(1 - area_stats['Total']/226_166_871.86)*100:.1f}% respecto al dataset completo")

if len(poligonos_grandes) > 0:
    area_total_grandes = poligonos_grandes['area_calculada_m2'].sum()
    porcentaje_area = (area_total_grandes / area_stats['Total']) * 100
    print(f"\n⚠️ ALERTA: {len(poligonos_grandes)} polígonos grandes (> 10 ha)")
    print(f"   Cubren {area_total_grandes/1_000_000:.2f} km² ({porcentaje_area:.1f}% del área filtrada)")

if len(poligonos_enormes) > 0:
    print(f"\n⛔ CRÍTICO: {len(poligonos_enormes)} polígonos ENORMES (> 100 ha)")

if len(sobreposiciones) > 0:
    print(f"\n⚠️ SOBREPOSICIONES: {len(sobreposiciones)} intersecciones")
    if len(sobreposiciones_significativas) > 0:
        print(f"   {len(sobreposiciones_significativas)} son significativas (> 10%)")

# ===== GUARDAR RESULTADOS =====
print(f"\n💾 Guardando resultados...")

# Guardar Excel
with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    print(f"  📄 Excel: {OUTPUT_EXCEL}")
    
    # Resumen
    df_resumen = pd.DataFrame({
        'Métrica': [
            'Alcaldía',
            'Intensidades incluidas',
            'Total de polígonos filtrados',
            'Área total (m²)',
            'Área total (km²)',
            'Área promedio (m²)',
            'Polígono más grande (m²)',
            'Polígonos grandes (> 10 ha)',
            'Polígonos enormes (> 100 ha)',
            'Sobreposiciones detectadas',
            'Reducción vs. dataset completo'
        ],
        'Valor': [
            'Iztapalapa',
            'Muy Alto, Alto',
            len(gdf_metrico),
            f"{area_stats['Total']:,.2f}",
            f"{area_stats['Total']/1_000_000:.2f}",
            f"{area_stats['Media']:,.2f}",
            f"{area_stats['Máxima']:,.2f}",
            len(poligonos_grandes),
            len(poligonos_enormes),
            len(sobreposiciones),
            f"{(1 - area_stats['Total']/226_166_871.86)*100:.1f}%"
        ]
    })
    df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    
    # Todos los polígonos
    df_exportar = gdf_metrico.drop(columns='geometry').copy()
    df_exportar = df_exportar.sort_values('area_calculada_m2', ascending=False)
    df_exportar.to_excel(writer, sheet_name='Todos_Poligonos', index=False)
    
    # Polígonos grandes
    if len(poligonos_grandes) > 0:
        df_grandes = poligonos_grandes.drop(columns='geometry').copy()
        df_grandes = df_grandes.sort_values('area_calculada_m2', ascending=False)
        df_grandes.to_excel(writer, sheet_name='Poligonos_Grandes', index=False)
    
    # Sobreposiciones
    if df_sobreposiciones is not None:
        df_sobreposiciones.to_excel(writer, sheet_name='Sobreposiciones', index=False)
    
    # Distribución
    df_dist = pd.DataFrame({
        'Categoría': distribucion.index,
        'Cantidad': distribucion.values,
        'Porcentaje': (distribucion.values / len(gdf_metrico) * 100).round(1)
    })
    df_dist.to_excel(writer, sheet_name='Distribucion_Tamanos', index=False)

# Guardar GeoJSON filtrado (en WGS84)
print(f"  📄 GeoJSON: {OUTPUT_GEOJSON}")
gdf_wgs84 = gdf.copy()  # Ya está en WGS84
gdf_wgs84.to_file(OUTPUT_GEOJSON, driver='GeoJSON')

print(f"\n🎉 ¡Análisis completado!")
print(f"\n📁 Archivos generados:")
print(f"   • {OUTPUT_EXCEL} - Análisis detallado")
print(f"   • {OUTPUT_GEOJSON} - GeoJSON filtrado (Muy Alto y Alto)")
