import pandas as pd
import numpy as np
import json
from shapely.geometry import shape, Polygon
from shapely.ops import unary_union
from tqdm import tqdm
import geopandas as gpd

# Archivos de entrada y salida
INPUT_CSV = "atlas-de-riesgo-inundaciones.csv"
OUTPUT_EXCEL = "analisis_atlas_riesgo_inundaciones.xlsx"

print("📥 Leyendo archivo CSV del Atlas de Riesgo...")
df = pd.read_csv(INPUT_CSV, encoding='latin-1')
print(f"✔️ Se leyeron {len(df):,} polígonos de toda la CDMX")

# Mostrar columnas disponibles
print(f"\n📊 Columnas disponibles:")
for col in df.columns:
    print(f"  • {col}")

# Filtrar solo Iztapalapa
print("\n🔍 Filtrando datos de Iztapalapa...")
df_iztapalapa = df[df['alcaldia'] == 'Iztapalapa'].copy()
print(f"✔️ Registros de Iztapalapa: {len(df_iztapalapa):,}")

# ===== ANÁLISIS DE DATOS GENERALES =====
print("\n📋 Análisis de datos generales:")

# Fenómenos
print("\n  Fenómenos:")
fenomenos = df_iztapalapa['fenomeno'].value_counts()
for fenomeno, cantidad in fenomenos.items():
    print(f"    • {fenomeno}: {cantidad}")

# Taxonomía
print("\n  Taxonomía:")
taxonomias = df_iztapalapa['taxonomia'].value_counts()
for taxonomia, cantidad in taxonomias.items():
    print(f"    • {taxonomia}: {cantidad}")

# R_P_V_E (Riesgo, Peligro, Vulnerabilidad, Exposición)
print("\n  Clasificación R_P_V_E:")
rpve = df_iztapalapa['r_p_v_e'].value_counts()
for categoria, cantidad in rpve.items():
    print(f"    • {categoria}: {cantidad}")

# Fuentes
print("\n  Fuentes de datos:")
fuentes = df_iztapalapa['fuente'].value_counts()
for fuente, cantidad in fuentes.items():
    print(f"    • {fuente}: {cantidad}")

# ===== CONVERTIR GEOMETRÍAS =====
print("\n🗺️ Convirtiendo geometrías GeoJSON a objetos Shapely...")
print("⏳ Esto puede tomar un momento...")

geometrias = []
indices_validos = []

for idx, row in tqdm(df_iztapalapa.iterrows(), total=len(df_iztapalapa), desc="Procesando geometrías"):
    try:
        # Parsear el JSON de geo_shape
        geo_json = json.loads(row['geo_shape'])
        geom = shape(geo_json)
        geometrias.append(geom)
        indices_validos.append(idx)
    except Exception as e:
        print(f"  ⚠️ Error en fila {idx}: {e}")
        continue

print(f"✔️ Geometrías válidas procesadas: {len(geometrias)}")

# Crear GeoDataFrame
df_iztapalapa_valido = df_iztapalapa.loc[indices_validos].copy()
gdf = gpd.GeoDataFrame(df_iztapalapa_valido, geometry=geometrias, crs="EPSG:4326")

# Convertir a sistema métrico para cálculos de área
print("\n🔄 Convirtiendo a sistema de coordenadas métrico (EPSG:6369)...")
gdf_metrico = gdf.to_crs(epsg=6369)

# ===== ANÁLISIS DE TAMAÑOS =====
print("\n📏 Analizando tamaños de polígonos...")

# Calcular área en m² y km²
gdf_metrico['area_calculada_m2'] = gdf_metrico.geometry.area
gdf_metrico['area_km2'] = gdf_metrico['area_calculada_m2'] / 1_000_000

# Comparar con área reportada
gdf_metrico['diferencia_area'] = abs(gdf_metrico['area_calculada_m2'] - gdf_metrico['area_m2'])
gdf_metrico['diferencia_porcentaje'] = (gdf_metrico['diferencia_area'] / gdf_metrico['area_m2']) * 100

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

print("\n📊 Estadísticas de áreas (calculadas):")
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

# Identificar polígonos grandes (> 10 hectáreas = 100,000 m²)
UMBRAL_GRANDE = 100_000  # 10 hectáreas
poligonos_grandes = gdf_metrico[gdf_metrico['area_calculada_m2'] > UMBRAL_GRANDE].copy()
print(f"\n⚠️ Polígonos grandes (> 10 ha): {len(poligonos_grandes)} de {len(gdf_metrico)} ({len(poligonos_grandes)/len(gdf_metrico)*100:.1f}%)")

if len(poligonos_grandes) > 0:
    area_total_grandes = poligonos_grandes['area_calculada_m2'].sum()
    print(f"  • Área total de polígonos grandes: {area_total_grandes/1_000_000:.2f} km² ({area_total_grandes/area_stats['Total']*100:.1f}% del total)")
    print(f"\n  Top 10 polígonos más grandes:")
    for idx, row in poligonos_grandes.nlargest(10, 'area_calculada_m2').iterrows():
        print(f"    • ID {row['id']}: {row['area_calculada_m2']:,.2f} m² ({row['area_calculada_m2']/10_000:.2f} ha)")
        print(f"      └─ {row['descripcio']}")

# ===== ANÁLISIS DE SOBREPOSICIONES =====
print("\n🔍 Analizando sobreposiciones entre polígonos...")
print("⏳ Esto puede tomar varios minutos para 916 polígonos...")

sobreposiciones = []

# Crear un índice espacial para optimizar las búsquedas
print("  Creando índice espacial...")
sindex = gdf_metrico.sindex

for idx, row in tqdm(gdf_metrico.iterrows(), total=len(gdf_metrico), desc="Verificando sobreposiciones"):
    # Obtener polígonos candidatos que intersectan el bbox
    possible_matches_index = list(sindex.intersection(row.geometry.bounds))
    possible_matches = gdf_metrico.iloc[possible_matches_index]
    
    # Verificar intersecciones reales
    for idx2, row2 in possible_matches.iterrows():
        if idx < idx2:  # Evitar duplicados y auto-intersección
            if row.geometry.intersects(row2.geometry):
                interseccion = row.geometry.intersection(row2.geometry)
                area_interseccion = interseccion.area
                
                # Solo contar sobreposiciones significativas (> 1 m²)
                if area_interseccion > 1:
                    porcentaje_poly1 = (area_interseccion / row['area_calculada_m2']) * 100
                    porcentaje_poly2 = (area_interseccion / row2['area_calculada_m2']) * 100
                    
                    sobreposiciones.append({
                        'ID_Poligono_1': row['id'],
                        'ID_Poligono_2': row2['id'],
                        'Area_Interseccion_m2': area_interseccion,
                        'Porcentaje_Poly1': porcentaje_poly1,
                        'Porcentaje_Poly2': porcentaje_poly2,
                        'Area_Poly1_m2': row['area_calculada_m2'],
                        'Area_Poly2_m2': row2['area_calculada_m2'],
                        'Tipo_Poly1': row['r_p_v_e'],
                        'Tipo_Poly2': row2['r_p_v_e']
                    })

print(f"\n✔️ Análisis de sobreposiciones completado")
print(f"  • Sobreposiciones encontradas: {len(sobreposiciones)}")

df_sobreposiciones = None
if len(sobreposiciones) > 0:
    df_sobreposiciones = pd.DataFrame(sobreposiciones)
    df_sobreposiciones = df_sobreposiciones.sort_values('Area_Interseccion_m2', ascending=False)
    
    area_total_sobreposicion = df_sobreposiciones['Area_Interseccion_m2'].sum()
    print(f"  • Área total de sobreposición: {area_total_sobreposicion:,.2f} m² ({area_total_sobreposicion/1_000_000:.4f} km²)")
    
    # Sobreposiciones significativas (> 10% de cualquier polígono)
    sobreposiciones_significativas = df_sobreposiciones[
        (df_sobreposiciones['Porcentaje_Poly1'] > 10) | 
        (df_sobreposiciones['Porcentaje_Poly2'] > 10)
    ]
    print(f"  • Sobreposiciones significativas (> 10%): {len(sobreposiciones_significativas)}")
    
    if len(df_sobreposiciones) > 0:
        print(f"\n  Top 10 mayores sobreposiciones:")
        for idx, row in df_sobreposiciones.head(10).iterrows():
            print(f"    • IDs {row['ID_Poligono_1']} ({row['Tipo_Poly1']}) ↔ {row['ID_Poligono_2']} ({row['Tipo_Poly2']})")
            print(f"      └─ Área: {row['Area_Interseccion_m2']:,.2f} m² ({row['Porcentaje_Poly1']:.1f}% / {row['Porcentaje_Poly2']:.1f}%)")
else:
    print("  ✔️ No se encontraron sobreposiciones entre polígonos")

# ===== ANÁLISIS DE FORMA =====
print("\n📐 Analizando complejidad de formas...")

# Calcular índice de compacidad
gdf_metrico['indice_compacidad'] = (4 * np.pi * gdf_metrico['area_calculada_m2']) / (gdf_metrico['perimetro_calculado_m'] ** 2)

print(f"  • Índice de compacidad promedio: {gdf_metrico['indice_compacidad'].mean():.3f}")
print(f"    (1.0 = circular, < 0.5 = muy irregular)")

# ===== RECOMENDACIONES =====
print("\n💡 RECOMENDACIONES PARA LA APLICACIÓN DE RUTAS:")
print("="*70)

# Polígonos grandes
if len(poligonos_grandes) > 0:
    area_total_grandes = poligonos_grandes['area_calculada_m2'].sum()
    porcentaje_area = (area_total_grandes / area_stats['Total']) * 100
    print(f"⚠️ ALERTA: {len(poligonos_grandes)} polígonos grandes (> 10 ha)")
    print(f"   Cubren {area_total_grandes/1_000_000:.2f} km² ({porcentaje_area:.1f}% del área total)")
    print(f"   Recomendación: Considerar subdividir estos polígonos")

# Polígonos enormes (> 100 ha)
poligonos_enormes = gdf_metrico[gdf_metrico['area_calculada_m2'] > 1_000_000]
if len(poligonos_enormes) > 0:
    print(f"\n⛔ CRÍTICO: {len(poligonos_enormes)} polígonos ENORMES (> 100 ha)")
    print(f"   Estos bloquearán áreas muy extensas en tu app")

# Sobreposiciones
if len(sobreposiciones) > 0:
    print(f"\n⚠️ SOBREPOSICIONES: {len(sobreposiciones)} intersecciones detectadas")
    if len(sobreposiciones_significativas) > 0:
        print(f"   {len(sobreposiciones_significativas)} son significativas (> 10%)")
    print(f"   Recomendación: Revisar y posiblemente fusionar polígonos sobrelapados")

# Cobertura total
cobertura_km2 = area_stats['Total'] / 1_000_000
print(f"\n📊 COBERTURA TOTAL DE IZTAPALAPA: {cobertura_km2:.2f} km²")
print(f"   Equivalente a {cobertura_km2 * 100:.2f} hectáreas")

# ===== GUARDAR RESULTADOS =====
print(f"\n💾 Guardando análisis en Excel: {OUTPUT_EXCEL}")

with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    # Hoja 1: Resumen estadístico
    print("  📄 Guardando hoja: 'Resumen'")
    df_resumen = pd.DataFrame({
        'Métrica': [
            'Total de polígonos (Iztapalapa)',
            'Área total (m²)',
            'Área total (km²)',
            'Área promedio (m²)',
            'Área mediana (m²)',
            'Polígono más pequeño (m²)',
            'Polígono más grande (m²)',
            'Polígonos grandes (> 10 ha)',
            'Polígonos enormes (> 100 ha)',
            'Sobreposiciones detectadas',
            'Sobreposiciones significativas (> 10%)',
            'Índice compacidad promedio',
            'Fenómenos únicos',
            'Clasificaciones R_P_V_E'
        ],
        'Valor': [
            len(gdf_metrico),
            f"{area_stats['Total']:,.2f}",
            f"{area_stats['Total']/1_000_000:.2f}",
            f"{area_stats['Media']:,.2f}",
            f"{area_stats['Mediana']:,.2f}",
            f"{area_stats['Mínima']:,.2f}",
            f"{area_stats['Máxima']:,.2f}",
            len(poligonos_grandes),
            len(poligonos_enormes),
            len(sobreposiciones),
            len(sobreposiciones_significativas) if df_sobreposiciones is not None else 0,
            f"{gdf_metrico['indice_compacidad'].mean():.3f}",
            ', '.join(fenomenos.index.tolist()),
            ', '.join(rpve.index.tolist())
        ]
    })
    df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    
    # Hoja 2: Todos los polígonos con métricas
    print("  📄 Guardando hoja: 'Todos_Poligonos'")
    df_exportar = gdf_metrico.drop(columns='geometry').copy()
    df_exportar = df_exportar.sort_values('area_calculada_m2', ascending=False)
    df_exportar.to_excel(writer, sheet_name='Todos_Poligonos', index=False)
    
    # Hoja 3: Polígonos grandes
    if len(poligonos_grandes) > 0:
        print("  📄 Guardando hoja: 'Poligonos_Grandes'")
        df_grandes = poligonos_grandes.drop(columns='geometry').copy()
        df_grandes = df_grandes.sort_values('area_calculada_m2', ascending=False)
        df_grandes.to_excel(writer, sheet_name='Poligonos_Grandes', index=False)
    
    # Hoja 4: Sobreposiciones
    if df_sobreposiciones is not None and len(df_sobreposiciones) > 0:
        print("  📄 Guardando hoja: 'Sobreposiciones'")
        df_sobreposiciones.to_excel(writer, sheet_name='Sobreposiciones', index=False)
    
    # Hoja 5: Distribución por tamaño
    print("  📄 Guardando hoja: 'Distribucion_Tamanos'")
    df_dist = pd.DataFrame({
        'Categoría': distribucion.index,
        'Cantidad': distribucion.values,
        'Porcentaje': (distribucion.values / len(gdf_metrico) * 100).round(1)
    })
    df_dist.to_excel(writer, sheet_name='Distribucion_Tamanos', index=False)
    
    # Hoja 6: Distribución por tipo R_P_V_E
    print("  📄 Guardando hoja: 'Clasificacion_RPVE'")
    df_rpve = pd.DataFrame({
        'Clasificación': rpve.index,
        'Cantidad': rpve.values,
        'Porcentaje': (rpve.values / len(df_iztapalapa) * 100).round(1)
    })
    df_rpve.to_excel(writer, sheet_name='Clasificacion_RPVE', index=False)

print(f"\n🎉 ¡Análisis completado!")
print(f"📊 Archivo guardado: {OUTPUT_EXCEL}")
print(f"\n📁 El Excel contiene:")
print(f"   1. Resumen - Estadísticas generales")
print(f"   2. Todos_Poligonos - Lista completa con métricas")
if len(poligonos_grandes) > 0:
    print(f"   3. Poligonos_Grandes - {len(poligonos_grandes)} polígonos > 10 ha")
if df_sobreposiciones is not None and len(df_sobreposiciones) > 0:
    print(f"   4. Sobreposiciones - {len(sobreposiciones)} intersecciones")
print(f"   5. Distribucion_Tamanos - Categorización por tamaño")
print(f"   6. Clasificacion_RPVE - Distribución por tipo de riesgo")
