import pandas as pd
from tqdm import tqdm

# Archivos de entrada y salida
INPUT_CSV = "data-2025-09-18.csv"
OUTPUT_EXCEL = "data_iztapalapa_filtrada.xlsx"

print("📥 Leyendo archivo CSV...")
print("⏳ Este archivo es grande, puede tomar un momento...")

# Leer CSV con codificación latin-1 para preservar caracteres especiales (ñ, acentos)
df = pd.read_csv(INPUT_CSV, encoding='latin-1')
print(f"✔️ Se leyeron {len(df):,} reportes en total")

# Mostrar información del dataset
print(f"\n📊 Columnas disponibles: {df.columns.tolist()}")

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

# Análisis de calles más reportadas
print("\n🔍 Analizando calles con más reportes...")

# Intentar identificar columna de calle (puede variar según el dataset)
columnas_posibles_calle = ['calle', 'nombre_calle', 'direccion', 'domicilio', 'colonia_catalogo']
columna_calle = None

for col in columnas_posibles_calle:
    if col in df_filtrado.columns:
        columna_calle = col
        break

if columna_calle:
    print(f"  📍 Usando columna: '{columna_calle}' para análisis de calles")
    
    # Contar reportes por calle
    df_filtrado_con_calle = df_filtrado[df_filtrado[columna_calle].notna()].copy()
    conteo_calles = df_filtrado_con_calle[columna_calle].value_counts().reset_index()
    conteo_calles.columns = ['CALLE', 'NUM_REPORTES']
    
    # Agregar información adicional
    calles_detalle = []
    
    print(f"  ⏳ Procesando {len(conteo_calles)} calles únicas...")
    for idx, row in tqdm(conteo_calles.iterrows(), total=len(conteo_calles), desc="Analizando calles"):
        calle = row['CALLE']
        num_reportes = row['NUM_REPORTES']
        
        # Obtener reportes de esta calle
        reportes_calle = df_filtrado_con_calle[df_filtrado_con_calle[columna_calle] == calle]
        
        # Tipos de reporte en esta calle
        tipos = reportes_calle['reporte'].value_counts().to_dict()
        tipos_str = ', '.join([f"{k}: {v}" for k, v in tipos.items()])
        
        calles_detalle.append({
            'CALLE': calle,
            'NUM_REPORTES': num_reportes,
            'TIPOS_REPORTE': tipos_str,
            'COORDENADA_PROMEDIO_LAT': reportes_calle['latitud'].mean(),
            'COORDENADA_PROMEDIO_LON': reportes_calle['longitud'].mean()
        })
    
    df_calles = pd.DataFrame(calles_detalle)
    df_calles = df_calles.sort_values('NUM_REPORTES', ascending=False)
    
    print(f"  ✔️ Análisis completado para {len(df_calles):,} calles")
    print(f"\n  🏆 Top 5 calles con más reportes:")
    for idx, row in df_calles.head(5).iterrows():
        print(f"     {row['CALLE']}: {row['NUM_REPORTES']} reportes")
else:
    print(f"  ⚠️ No se encontró columna de calle en: {df_filtrado.columns.tolist()}")
    df_calles = None

# Guardar a Excel con múltiples hojas
print(f"\n💾 Guardando archivo Excel: {OUTPUT_EXCEL}")

with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    # Hoja 1: Datos filtrados
    print("  📄 Guardando hoja: 'Datos_Filtrados'")
    df_filtrado.to_excel(writer, sheet_name='Datos_Filtrados', index=False)
    
    # Hoja 2: Conteo de calles (si existe)
    if df_calles is not None:
        print("  📄 Guardando hoja: 'Calles_Mas_Reportadas'")
        df_calles.to_excel(writer, sheet_name='Calles_Mas_Reportadas', index=False)
    
    # Hoja 3: Resumen estadístico
    print("  📄 Guardando hoja: 'Resumen'")
    resumen_data = {
        'Métrica': [
            'Total de reportes en dataset original',
            'Reportes en Iztapalapa',
            'Reportes filtrados (tipos relevantes)',
            'Reportes con coordenadas válidas',
            'Tipos de reporte incluidos',
            'Rango de fechas'
        ],
        'Valor': [
            f"{len(df):,}",
            f"{len(df[df['alcaldia_catalogo'] == 'Iztapalapa']):,}",
            f"{len(df_filtrado):,}",
            f"{len(df_filtrado):,}",
            ', '.join(reportes_relevantes),
            f"{df_filtrado['fecha_reporte'].min()} a {df_filtrado['fecha_reporte'].max()}" if 'fecha_reporte' in df_filtrado.columns else 'N/A'
        ]
    }
    df_resumen = pd.DataFrame(resumen_data)
    df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    
    # Hoja 4: Distribución por tipo de reporte
    print("  📄 Guardando hoja: 'Distribucion_Reportes'")
    df_distribucion = conteo_reportes.reset_index()
    df_distribucion.columns = ['TIPO_REPORTE', 'CANTIDAD']
    df_distribucion.to_excel(writer, sheet_name='Distribucion_Reportes', index=False)

print(f"\n🎉 ¡Proceso completado exitosamente!")
print(f"📊 Resumen:")
print(f"   • Reportes filtrados: {len(df_filtrado):,}")
print(f"   • Alcaldía: Iztapalapa")
print(f"   • Tipos de reporte: {len(reportes_relevantes)}")
if df_calles is not None:
    print(f"   • Calles analizadas: {len(df_calles):,}")
print(f"   • Archivo guardado: {OUTPUT_EXCEL}")
print(f"\n📁 El Excel contiene las siguientes hojas:")
print(f"   1. Datos_Filtrados - Todos los reportes filtrados")
if df_calles is not None:
    print(f"   2. Calles_Mas_Reportadas - Conteo y análisis por calle")
print(f"   3. Resumen - Estadísticas generales")
print(f"   4. Distribucion_Reportes - Conteo por tipo de reporte")
