import pandas as pd
from tqdm import tqdm

# Archivos de entrada y salida
INPUT_EXCEL = "data_iztapalapa_con_calles.xlsx"
OUTPUT_EXCEL = "analisis_calles_iztapalapa.xlsx"

print("📥 Leyendo archivo con calles geocodificadas...")
df = pd.read_excel(INPUT_EXCEL, engine='openpyxl')
print(f"✔️ Se leyeron {len(df):,} reportes")

print("\n🔍 Analizando calles más reportadas...")

# Filtrar solo registros con calle válida
calles_validas = ['Sin nombre de calle', 'No disponible', 'Timeout', 'Error', 'Error de servicio']
df_con_calle = df[~df['CALLE_NOMINATIM'].isin(calles_validas)].copy()

print(f"  📍 Reportes con calle identificada: {len(df_con_calle):,}")

# Contar reportes por calle
print("\n⏳ Contando reportes por calle...")
conteo_calles = df_con_calle['CALLE_NOMINATIM'].value_counts().reset_index()
conteo_calles.columns = ['CALLE', 'NUM_REPORTES']

# Agregar información detallada por calle
calles_detalle = []

print(f"⏳ Procesando {len(conteo_calles)} calles únicas...")
for idx, row in tqdm(conteo_calles.iterrows(), total=len(conteo_calles), desc="Analizando calles"):
    calle = row['CALLE']
    num_reportes = row['NUM_REPORTES']
    
    # Obtener reportes de esta calle
    reportes_calle = df_con_calle[df_con_calle['CALLE_NOMINATIM'] == calle]
    
    # Tipos de reporte en esta calle
    tipos = reportes_calle['reporte'].value_counts().to_dict()
    tipos_str = ', '.join([f"{k}: {v}" for k, v in tipos.items()])
    
    # Colonias asociadas a esta calle
    colonias = reportes_calle['COLONIA_NOMINATIM'].value_counts().head(3).to_dict()
    colonias_str = ', '.join([f"{k} ({v})" for k, v in colonias.items()])
    
    calles_detalle.append({
        'CALLE': calle,
        'NUM_REPORTES': num_reportes,
        'TIPOS_REPORTE': tipos_str,
        'COLONIAS_PRINCIPALES': colonias_str,
        'COORDENADA_PROMEDIO_LAT': reportes_calle['latitud'].mean(),
        'COORDENADA_PROMEDIO_LON': reportes_calle['longitud'].mean(),
        'REPORTE_MAS_COMUN': reportes_calle['reporte'].mode()[0] if len(reportes_calle) > 0 else 'N/A',
        'CANTIDAD_REPORTE_MAS_COMUN': tipos[reportes_calle['reporte'].mode()[0]] if len(reportes_calle) > 0 else 0
    })

df_calles = pd.DataFrame(calles_detalle)
df_calles = df_calles.sort_values('NUM_REPORTES', ascending=False)

print(f"✔️ Análisis completado para {len(df_calles):,} calles")

# Mostrar top 10
print(f"\n🏆 Top 10 calles con más reportes:")
for idx, row in df_calles.head(10).iterrows():
    print(f"  {idx+1}. {row['CALLE']}: {row['NUM_REPORTES']} reportes")
    print(f"     └─ Más común: {row['REPORTE_MAS_COMUN']} ({row['CANTIDAD_REPORTE_MAS_COMUN']} casos)")

# Análisis por colonia
print(f"\n🏘️ Analizando colonias más reportadas...")
conteo_colonias = df_con_calle['COLONIA_NOMINATIM'].value_counts().reset_index()
conteo_colonias.columns = ['COLONIA', 'NUM_REPORTES']

colonias_detalle = []
for idx, row in tqdm(conteo_colonias.iterrows(), total=len(conteo_colonias), desc="Analizando colonias"):
    colonia = row['COLONIA']
    num_reportes = row['NUM_REPORTES']
    
    reportes_colonia = df_con_calle[df_con_calle['COLONIA_NOMINATIM'] == colonia]
    
    tipos = reportes_colonia['reporte'].value_counts().to_dict()
    tipos_str = ', '.join([f"{k}: {v}" for k, v in tipos.items()])
    
    # Top 3 calles en esta colonia
    calles_top = reportes_colonia['CALLE_NOMINATIM'].value_counts().head(3).to_dict()
    calles_str = ', '.join([f"{k} ({v})" for k, v in calles_top.items()])
    
    colonias_detalle.append({
        'COLONIA': colonia,
        'NUM_REPORTES': num_reportes,
        'TIPOS_REPORTE': tipos_str,
        'CALLES_PRINCIPALES': calles_str,
        'COORDENADA_PROMEDIO_LAT': reportes_colonia['latitud'].mean(),
        'COORDENADA_PROMEDIO_LON': reportes_colonia['longitud'].mean(),
        'REPORTE_MAS_COMUN': reportes_colonia['reporte'].mode()[0] if len(reportes_colonia) > 0 else 'N/A'
    })

df_colonias = pd.DataFrame(colonias_detalle)
df_colonias = df_colonias.sort_values('NUM_REPORTES', ascending=False)

print(f"✔️ Análisis completado para {len(df_colonias):,} colonias")

print(f"\n🏆 Top 5 colonias con más reportes:")
for idx, row in df_colonias.head(5).iterrows():
    print(f"  {idx+1}. {row['COLONIA']}: {row['NUM_REPORTES']} reportes")

# Análisis de zonas críticas (calle + colonia)
print(f"\n⚠️ Identificando zonas críticas...")
df_con_calle['ZONA'] = df_con_calle['CALLE_NOMINATIM'] + ' - ' + df_con_calle['COLONIA_NOMINATIM']
conteo_zonas = df_con_calle['ZONA'].value_counts().head(20).reset_index()
conteo_zonas.columns = ['ZONA', 'NUM_REPORTES']

# Agregar detalles de zonas
zonas_detalle = []
for idx, row in conteo_zonas.iterrows():
    zona = row['ZONA']
    num_reportes = row['NUM_REPORTES']
    
    reportes_zona = df_con_calle[df_con_calle['ZONA'] == zona]
    tipos = reportes_zona['reporte'].value_counts().to_dict()
    tipos_str = ', '.join([f"{k}: {v}" for k, v in tipos.items()])
    
    zonas_detalle.append({
        'ZONA_CALLE_COLONIA': zona,
        'NUM_REPORTES': num_reportes,
        'TIPOS_REPORTE': tipos_str,
        'COORDENADA_LAT': reportes_zona['latitud'].mean(),
        'COORDENADA_LON': reportes_zona['longitud'].mean()
    })

df_zonas_criticas = pd.DataFrame(zonas_detalle)

# Guardar a Excel con múltiples hojas
print(f"\n💾 Guardando archivo Excel: {OUTPUT_EXCEL}")

with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    # Hoja 1: Calles más reportadas
    print("  📄 Guardando hoja: 'Calles_Mas_Reportadas'")
    df_calles.to_excel(writer, sheet_name='Calles_Mas_Reportadas', index=False)
    
    # Hoja 2: Colonias más reportadas
    print("  📄 Guardando hoja: 'Colonias_Mas_Reportadas'")
    df_colonias.to_excel(writer, sheet_name='Colonias_Mas_Reportadas', index=False)
    
    # Hoja 3: Zonas críticas (top 20)
    print("  📄 Guardando hoja: 'Zonas_Criticas'")
    df_zonas_criticas.to_excel(writer, sheet_name='Zonas_Criticas', index=False)
    
    # Hoja 4: Resumen general
    print("  📄 Guardando hoja: 'Resumen'")
    resumen_data = {
        'Métrica': [
            'Total de reportes analizados',
            'Reportes con calle identificada',
            'Calles únicas identificadas',
            'Colonias únicas identificadas',
            'Calle con más reportes',
            'Colonia con más reportes',
            'Tipo de reporte más común',
            'Porcentaje de geocodificación exitosa'
        ],
        'Valor': [
            f"{len(df):,}",
            f"{len(df_con_calle):,}",
            f"{len(df_calles):,}",
            f"{len(df_colonias):,}",
            f"{df_calles.iloc[0]['CALLE']} ({df_calles.iloc[0]['NUM_REPORTES']} reportes)",
            f"{df_colonias.iloc[0]['COLONIA']} ({df_colonias.iloc[0]['NUM_REPORTES']} reportes)",
            f"{df['reporte'].mode()[0]} ({df['reporte'].value_counts().iloc[0]} reportes)",
            f"{len(df_con_calle)/len(df)*100:.1f}%"
        ]
    }
    df_resumen = pd.DataFrame(resumen_data)
    df_resumen.to_excel(writer, sheet_name='Resumen', index=False)

print(f"\n🎉 ¡Análisis completado exitosamente!")
print(f"📊 Resumen:")
print(f"   • Calles analizadas: {len(df_calles):,}")
print(f"   • Colonias analizadas: {len(df_colonias):,}")
print(f"   • Zonas críticas identificadas: {len(df_zonas_criticas):,}")
print(f"   • Archivo guardado: {OUTPUT_EXCEL}")
print(f"\n📁 El Excel contiene las siguientes hojas:")
print(f"   1. Calles_Mas_Reportadas - Ranking completo de calles")
print(f"   2. Colonias_Mas_Reportadas - Ranking completo de colonias")
print(f"   3. Zonas_Criticas - Top 20 zonas (calle + colonia)")
print(f"   4. Resumen - Estadísticas generales")
