import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from tqdm import tqdm
import matplotlib.pyplot as plt

# Archivo de entrada
INPUT_GEOJSON = "zonas_historicamente_inundables_(2024).geojson"
OUTPUT_EXCEL = "analisis_poligonos_zonas_inundables.xlsx"

print("📥 Leyendo GeoJSON de zonas inundables...")
gdf = gpd.read_file(INPUT_GEOJSON)
print(f"✔️ Se leyeron {len(gdf)} polígonos")

# Convertir a proyección métrica para análisis de áreas (si no está ya)
print("\n🔄 Verificando sistema de coordenadas...")
print(f"  CRS actual: {gdf.crs}")

# Si está en EPSG:6369 (México), mantenerlo para cálculos de área
# Si queremos WGS84, convertimos
gdf_metrico = gdf.copy()
if gdf.crs.to_epsg() != 6369:
    print("  Convirtiendo a EPSG:6369 para cálculos métricos...")
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
print(f"  • Mínima: {area_stats['Mínima']:,.2f} m² ({area_stats['Mínima']/1000:.2f} km²)")
print(f"  • Máxima: {area_stats['Máxima']:,.2f} m² ({area_stats['Máxima']/1_000_000:.4f} km²)")
print(f"  • Media: {area_stats['Media']:,.2f} m² ({area_stats['Media']/1_000_000:.4f} km²)")
print(f"  • Mediana: {area_stats['Mediana']:,.2f} m² ({area_stats['Mediana']/1_000_000:.4f} km²)")
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
    else:  # > 50 hectáreas
        return 'Muy grande (> 50 ha)'

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
    print(f"  Top 5 polígonos más grandes:")
    for idx, row in poligonos_grandes.nlargest(5, 'area_calculada_m2').iterrows():
        print(f"    • ID {row['objectid']}: {row['area_calculada_m2']:,.2f} m² ({row['area_calculada_m2']/10_000:.2f} ha)")

# ===== ANÁLISIS DE SOBREPOSICIONES =====
print("\n🔍 Analizando sobreposiciones entre polígonos...")
print("⏳ Esto puede tomar un momento...")

sobreposiciones = []
total_comparaciones = (len(gdf_metrico) * (len(gdf_metrico) - 1)) // 2

# Crear un índice espacial para optimizar las búsquedas
print("  Creando índice espacial...")
sindex = gdf_metrico.sindex

contador = 0
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
                        'ID_Poligono_1': row['objectid'],
                        'ID_Poligono_2': row2['objectid'],
                        'Area_Interseccion_m2': area_interseccion,
                        'Porcentaje_Poly1': porcentaje_poly1,
                        'Porcentaje_Poly2': porcentaje_poly2,
                        'Area_Poly1_m2': row['area_calculada_m2'],
                        'Area_Poly2_m2': row2['area_calculada_m2']
                    })
                    contador += 1

print(f"\n✔️ Análisis de sobreposiciones completado")
print(f"  • Sobreposiciones encontradas: {len(sobreposiciones)}")

if len(sobreposiciones) > 0:
    df_sobreposiciones = pd.DataFrame(sobreposiciones)
    df_sobreposiciones = df_sobreposiciones.sort_values('Area_Interseccion_m2', ascending=False)
    
    area_total_sobreposicion = df_sobreposiciones['Area_Interseccion_m2'].sum()
    print(f"  • Área total de sobreposición: {area_total_sobreposicion:,.2f} m² ({area_total_sobreposicion/1_000_000:.4f} km²)")
    
    # Sobreposiciones significativas (> 10% de cualquier polígono)
    sobreposciones_significativas = df_sobreposiciones[
        (df_sobreposiciones['Porcentaje_Poly1'] > 10) | 
        (df_sobreposiciones['Porcentaje_Poly2'] > 10)
    ]
    print(f"  • Sobreposiciones significativas (> 10%): {len(sobreposciones_significativas)}")
    
    if len(df_sobreposiciones) > 0:
        print(f"\n  Top 5 mayores sobreposiciones:")
        for idx, row in df_sobreposiciones.head(5).iterrows():
            print(f"    • IDs {int(row['ID_Poligono_1'])} ↔ {int(row['ID_Poligono_2'])}: {row['Area_Interseccion_m2']:,.2f} m²")
            print(f"      └─ Cubre {row['Porcentaje_Poly1']:.1f}% del primero y {row['Porcentaje_Poly2']:.1f}% del segundo")
else:
    print("  ✔️ No se encontraron sobreposiciones entre polígonos")
    df_sobreposiciones = None

# ===== ANÁLISIS DE FORMA =====
print("\n📐 Analizando complejidad de formas...")

# Calcular índice de compacidad (relación área/perímetro)
gdf_metrico['indice_compacidad'] = (4 * np.pi * gdf_metrico['area_calculada_m2']) / (gdf_metrico['perimetro_calculado_m'] ** 2)
# Valor de 1 = círculo perfecto, menor = más irregular

print(f"  • Índice de compacidad promedio: {gdf_metrico['indice_compacidad'].mean():.3f}")
print(f"    (1.0 = circular, < 0.5 = muy irregular)")

# Número de vértices
gdf_metrico['num_vertices'] = gdf_metrico.geometry.apply(lambda g: len(g.exterior.coords) - 1)
print(f"  • Vértices promedio por polígono: {gdf_metrico['num_vertices'].mean():.1f}")
print(f"  • Polígono más complejo: {gdf_metrico['num_vertices'].max()} vértices")

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

# Sobreposiciones
if len(sobreposiciones) > 0:
    print(f"\n⚠️ SOBREPOSICIONES: {len(sobreposiciones)} intersecciones detectadas")
    if len(sobreposciones_significativas) > 0:
        print(f"   {len(sobreposciones_significativas)} son significativas (> 10%)")
    print(f"   Recomendación: Fusionar o eliminar sobreposiciones duplicadas")

# Cobertura total
cobertura_km2 = area_stats['Total'] / 1_000_000
print(f"\n📊 COBERTURA TOTAL: {cobertura_km2:.2f} km²")
print(f"   Equivalente a {cobertura_km2 * 100} hectáreas")

# ===== GUARDAR RESULTADOS =====
print(f"\n💾 Guardando análisis en Excel: {OUTPUT_EXCEL}")

with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    # Hoja 1: Resumen estadístico
    print("  📄 Guardando hoja: 'Resumen'")
    df_resumen = pd.DataFrame({
        'Métrica': [
            'Total de polígonos',
            'Área total (m²)',
            'Área total (km²)',
            'Área promedio (m²)',
            'Área mediana (m²)',
            'Polígono más pequeño (m²)',
            'Polígono más grande (m²)',
            'Polígonos grandes (> 10 ha)',
            'Sobreposiciones detectadas',
            'Área de sobreposición total (m²)',
            'Vértices promedio',
            'Índice compacidad promedio'
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
            len(sobreposiciones),
            f"{df_sobreposiciones['Area_Interseccion_m2'].sum():,.2f}" if df_sobreposiciones is not None else "0",
            f"{gdf_metrico['num_vertices'].mean():.1f}",
            f"{gdf_metrico['indice_compacidad'].mean():.3f}"
        ]
    })
    df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    
    # Hoja 2: Todos los polígonos con métricas
    print("  📄 Guardando hoja: 'Todos_Poligonos'")
    df_poligonos = gdf_metrico.drop(columns='geometry').copy()
    df_poligonos = df_poligonos.sort_values('area_calculada_m2', ascending=False)
    df_poligonos.to_excel(writer, sheet_name='Todos_Poligonos', index=False)
    
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

print(f"\n🎉 ¡Análisis completado!")
print(f"📊 Archivo guardado: {OUTPUT_EXCEL}")
print(f"\n📁 El Excel contiene:")
print(f"   1. Resumen - Estadísticas generales")
print(f"   2. Todos_Poligonos - Lista completa con métricas")
if len(poligonos_grandes) > 0:
    print(f"   3. Poligonos_Grandes - {len(poligonos_grandes)} polígonos > 10 ha")
if df_sobreposiciones is not None and len(df_sobreposiciones) > 0:
    print(f"   4. Sobreposiciones - {len(sobreposiciones)} intersecciones detectadas")
print(f"   5. Distribucion_Tamanos - Categorización por tamaño")
