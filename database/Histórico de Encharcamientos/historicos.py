import pandas as pd
import re

INPUT_EXCEL = "encharcamientos_2000_2017_filtrado.xlsx"
OUTPUT_EXCEL = "calles_recurrentes_iztapalapa.xlsx"

# --------------------------------------------
# 1. LEER DATOS FILTRADOS
# --------------------------------------------
print("📥 Leyendo archivo filtrado...")
df = pd.read_excel(INPUT_EXCEL)
print(f"✔️ Total de registros: {len(df)}")
print(f"📋 Columnas disponibles: {df.columns.tolist()}")

# --------------------------------------------
# 2. FUNCIONES PARA NORMALIZAR
# --------------------------------------------
def normalizar_calle(nombre_calle):
    """
    Normaliza el nombre de una calle eliminando números, manzanas, lotes, etc.
    EXCEPCIÓN: Mantiene números que son parte del nombre de la calle
    (ej: "1A. CALLE DE LUIS ARAIZA" -> "CALLE DE LUIS ARAIZA", pero "CALLE 11" -> "CALLE 11")
    """
    if pd.isna(nombre_calle) or nombre_calle == '':
        return None
    
    # Convertir a string y mayúsculas
    calle = str(nombre_calle).upper().strip()
    
    # Eliminar patrones comunes:
    # - Números al inicio SOLO si hay más texto después (ej: "1A. CALLE X" -> "CALLE X")
    # - PERO mantener si el número es parte del nombre (ej: "CALLE 11" se mantiene)
    calle = re.sub(r'^[\d]+[A-Z]*\.?\s+(?=\D)', '', calle)  # Solo elimina si después hay no-dígitos
    
    # - Eliminar # y todo lo que sigue
    calle = re.sub(r'#.*$', '', calle)
    
    # - Eliminar MZ y todo lo que sigue
    calle = re.sub(r'\s+MZ\.?.*$', '', calle, flags=re.IGNORECASE)
    
    # - Eliminar LT y todo lo que sigue
    calle = re.sub(r'\s+LT\.?.*$', '', calle, flags=re.IGNORECASE)
    
    # - Eliminar S/N (sin número)
    calle = re.sub(r'\s+S/N.*$', '', calle, flags=re.IGNORECASE)
    
    # - Eliminar números sueltos al final SOLO si no son el nombre de la calle
    # EXCEPCIÓN: No eliminar si la calle termina en palabras clave + número (Av. 11, Calle 11, etc.)
    if not re.search(r'(^|\s)(AV\.?|CALLE|PRIV\.?|CDA\.?|RT\.?|CALLEJON|C\.)\s+\d+\s*$', calle, re.IGNORECASE):
        if not re.match(r'^[A-Z]?\s*\d+\s*$', calle):  # Si NO es solo "A 11" o "11"
            calle = re.sub(r'\s+\d+\s*$', '', calle)
    
    # Limpiar espacios múltiples y trim
    calle = re.sub(r'\s+', ' ', calle).strip()
    
    return calle if calle else None

def normalizar_entre_calles(entre_call):
    """
    Normaliza la columna ENTRE_CALL para identificar segmentos específicos.
    Maneja casos como:
    - "TODA LA CALLE" -> "TODA LA CALLE"
    - "ENTRE X Y Y" -> "ENTRE X Y Y"
    - "ESQ: X" -> "ESQ. X"
    - "(FRENTE A X)" -> "FRENTE A X"
    IMPORTANTE: Mantiene números que son nombres de calles (ej: "FRENTE A 11")
    """
    if pd.isna(entre_call) or entre_call == '':
        return "SIN ESPECIFICAR"
    
    # Convertir a string y mayúsculas
    entre = str(entre_call).upper().strip()
    
    # Normalizar paréntesis
    entre = entre.replace('(', '').replace(')', '')
    
    # Normalizar variaciones de "esquina"
    entre = re.sub(r'^ESQ\.?\s*:', 'ESQ.', entre)
    entre = re.sub(r'^ESQUINA\s*:', 'ESQ.', entre)
    
    # Normalizar "TODA LA CALLE"
    if 'TODA LA CALLE' in entre:
        return "TODA LA CALLE"
    
    # Normalizar "ENTRE X Y Y"
    if entre.startswith('ENTRE '):
        # Limpiar números de direcciones SOLO si tienen #
        entre = re.sub(r'#\s*\d+', '', entre)
        # NO eliminar números al final si son parte del nombre de la calle
    
    # Normalizar "FRENTE A"
    if 'FRENTE' in entre:
        entre = re.sub(r'FRENTE\s+A\s+', 'FRENTE A ', entre)
        # NO eliminar números después de "FRENTE A" ya que pueden ser nombres de calles
    
    # Para ESQ. también mantener los números que son nombres
    # No hacer nada adicional, ya están protegidos
    
    # Limpiar espacios múltiples
    entre = re.sub(r'\s+', ' ', entre).strip()
    
    return entre if entre else "SIN ESPECIFICAR"

def crear_segmento_unico(calle_norm, entre_norm):
    """
    Crea un identificador único combinando calle normalizada y el segmento.
    """
    if entre_norm == "TODA LA CALLE":
        return f"{calle_norm} [TODA LA CALLE]"
    elif entre_norm == "SIN ESPECIFICAR":
        return f"{calle_norm} [SIN ESPECIFICAR]"
    else:
        return f"{calle_norm} [{entre_norm}]"

# --------------------------------------------
# 3. NORMALIZAR CALLES Y SEGMENTOS
# --------------------------------------------
print("\n🔧 Normalizando nombres de calles y segmentos...")
df['CALLE_NORMALIZADA'] = df['CALLE'].apply(normalizar_calle)
df['ENTRE_NORMALIZADO'] = df['ENTRE_CALL'].apply(normalizar_entre_calles)
df['SEGMENTO_UNICO'] = df.apply(lambda row: crear_segmento_unico(
    row['CALLE_NORMALIZADA'], 
    row['ENTRE_NORMALIZADO']
), axis=1)

# Eliminar registros sin calle
df = df[df['CALLE_NORMALIZADA'].notna()]
print(f"✔️ Registros con calle válida: {len(df)}")

# --------------------------------------------
# 4. CONTAR OCURRENCIAS POR SEGMENTO
# --------------------------------------------
print("\n📊 Contando ocurrencias por segmento de calle...")

# Detectar columna de colonia
colonia_col = None
for col in df.columns:
    if 'COLONIA' in col.upper():
        colonia_col = col
        break

if colonia_col:
    print(f"✔️ Columna de colonia encontrada: {colonia_col}")
else:
    print("⚠️ No se encontró columna de colonia")

conteo_segmentos = df.groupby('SEGMENTO_UNICO').agg({
    'CALLE': 'count',
    'CAUSA': lambda x: x.value_counts().to_dict(),
    'CALLE_NORMALIZADA': 'first',
    'ENTRE_NORMALIZADO': 'first',
    colonia_col: 'first' if colonia_col else lambda x: 'N/A'
}).reset_index()

conteo_segmentos.columns = ['SEGMENTO_UNICO', 'NUM_REPORTES', 'CAUSAS_DISTRIBUCION', 
                             'CALLE_NORMALIZADA', 'ENTRE_NORMALIZADO', 'COLONIA']

# Ordenar por número de reportes descendente
conteo_segmentos = conteo_segmentos.sort_values('NUM_REPORTES', ascending=False)

# --------------------------------------------
# 5. FILTRAR SEGMENTOS CON MÁS DE 1 REPORTE
# --------------------------------------------
segmentos_recurrentes = conteo_segmentos[conteo_segmentos['NUM_REPORTES'] > 1].copy()
print(f"\n✔️ Segmentos con más de 1 reporte: {len(segmentos_recurrentes)}")
print(f"📊 Total de reportes en segmentos recurrentes: {segmentos_recurrentes['NUM_REPORTES'].sum()}")

# --------------------------------------------
# 6. CREAR DATAFRAME DETALLADO
# --------------------------------------------
print("\n📋 Generando detalle de segmentos recurrentes...")
detalles = []

# Detectar columnas de coordenadas
coord_cols = [col for col in df.columns if 'LON' in col.upper() or 'LAT' in col.upper()]

for _, row in segmentos_recurrentes.iterrows():
    segmento = row['SEGMENTO_UNICO']
    registros_segmento = df[df['SEGMENTO_UNICO'] == segmento]
    
    # Obtener coordenadas si existen
    if len(coord_cols) >= 2:
        lon_col = [c for c in coord_cols if 'LON' in c.upper()][0]
        lat_col = [c for c in coord_cols if 'LAT' in c.upper()][0]
        
        # Obtener todas las coordenadas del segmento (útil para GeoJSON)
        coords_list = registros_segmento[[lat_col, lon_col]].values.tolist()
        coordenadas = f"[{coords_list[0][1]}, {coords_list[0][0]}]"  # [lon, lat] formato GeoJSON
        num_puntos = len(coords_list)
    else:
        coordenadas = "N/A"
        num_puntos = 0
    
    detalles.append({
        'CALLE': row['CALLE_NORMALIZADA'],
        'COLONIA': row['COLONIA'],
        'SEGMENTO': row['ENTRE_NORMALIZADO'],
        'NUM_REPORTES': row['NUM_REPORTES'],
        'CAUSAS_PRINCIPALES': ', '.join([f"{k}: {v}" for k, v in 
                                        registros_segmento['CAUSA'].value_counts().head(3).items()]),
        'NOMBRES_ORIGINALES_CALLE': ' | '.join(registros_segmento['CALLE'].unique()[:3]),
        'COORDENADAS_PRIMERA': coordenadas,
        'TOTAL_PUNTOS_GPS': num_puntos
    })

df_detalle = pd.DataFrame(detalles)

# --------------------------------------------
# 7. ESTADÍSTICAS ADICIONALES
# --------------------------------------------
print("\n📊 Estadísticas por tipo de segmento:")
tipo_segmento = df_detalle['SEGMENTO'].value_counts()
print(f"  - TODA LA CALLE: {tipo_segmento.get('TODA LA CALLE', 0)}")
print(f"  - ENTRE (específico): {len([s for s in df_detalle['SEGMENTO'] if s.startswith('ENTRE')])}")
print(f"  - ESQUINA: {len([s for s in df_detalle['SEGMENTO'] if s.startswith('ESQ')])}")
print(f"  - FRENTE A: {len([s for s in df_detalle['SEGMENTO'] if 'FRENTE' in s])}")
print(f"  - SIN ESPECIFICAR: {tipo_segmento.get('SIN ESPECIFICAR', 0)}")

# --------------------------------------------
# 8. GUARDAR RESULTADOS
# --------------------------------------------
print(f"\n💾 Guardando resultados en {OUTPUT_EXCEL}...")

with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    # Hoja 1: Resumen de segmentos recurrentes
    df_detalle.to_excel(writer, sheet_name='Segmentos Recurrentes', index=False)
    
    # Hoja 2: Todos los reportes de segmentos recurrentes
    segmentos_nombres = segmentos_recurrentes['SEGMENTO_UNICO'].tolist()
    df_filtrado = df[df['SEGMENTO_UNICO'].isin(segmentos_nombres)].copy()
    
    # Seleccionar columnas relevantes para GeoJSON
    columnas_relevantes = ['CALLE', 'CALLE_NORMALIZADA', 'ENTRE_CALL', 'ENTRE_NORMALIZADO', 
                          'SEGMENTO_UNICO', 'CAUSA', 'DELEGACION']
    if colonia_col:
        columnas_relevantes.append(colonia_col)
    columnas_relevantes += coord_cols
    columnas_disponibles = [col for col in columnas_relevantes if col in df_filtrado.columns]
    
    df_filtrado[columnas_disponibles].to_excel(writer, sheet_name='Detalle Completo', index=False)
    
    # Hoja 3: Resumen por calle (sin considerar segmento)
    agg_dict = {'CALLE': 'count'}
    if colonia_col:
        agg_dict[colonia_col] = 'first'
    
    conteo_calles_general = df.groupby('CALLE_NORMALIZADA').agg(agg_dict).reset_index()
    
    if colonia_col:
        conteo_calles_general.columns = ['CALLE', 'TOTAL_REPORTES', 'COLONIA']
    else:
        conteo_calles_general.columns = ['CALLE', 'TOTAL_REPORTES']
    
    conteo_calles_general = conteo_calles_general.sort_values('TOTAL_REPORTES', ascending=False)
    conteo_calles_general.to_excel(writer, sheet_name='Resumen por Calle', index=False)

print(f"\n🎉 Análisis completado!")
print(f"\n📈 Top 10 segmentos con más reportes:")
print(df_detalle.head(10)[['CALLE', 'COLONIA', 'SEGMENTO', 'NUM_REPORTES', 'CAUSAS_PRINCIPALES']])