import geopandas as gpd
import pandas as pd

SHAPEFILE_PATH = "encharcamientos_2000_2017_e.shp"
OUTPUT_EXCEL = "encharcamientos_2000_2017_filtrado.xlsx"

# --------------------------------------------
# 1. LEER EL SHAPEFILE COMPLETO
# --------------------------------------------
print("📥 Leyendo Shapefile con geometrías...")
# Leer shapefile con encoding para acentos y ñ
gdf = gpd.read_file(SHAPEFILE_PATH, encoding='latin-1')

# Convertir a DataFrame regular (sin geometría para Excel)
df = pd.DataFrame(gdf.drop(columns='geometry'))

print("✔️ Columnas cargadas desde el Shapefile:")
print(df.columns.tolist())
print(f"📊 Total de registros iniciales: {len(df)}")

# --------------------------------------------
# 2. FILTRAR POR DELEGACIÓN IZTAPALAPA
# --------------------------------------------
print("\n🔍 Filtrando por delegación IZTAPALAPA...")
df = df[df['DELEGACION'].str.upper().str.strip() == 'IZTAPALAPA']
print(f"✔️ Registros después del filtro de delegación: {len(df)}")

# --------------------------------------------
# 3. FILTRAR POR CAUSAS SELECCIONADAS
# --------------------------------------------
causas_validas = [
    'FALTA DE DRENAJE',
    'FALTA DE INFRAESTRUCTURA',
    'HUNDIMIENTO DE LA CARPETA ASFALTICA',
    'HUNDIMIENTO DE LA CARPETA ASFÁLTICA',
    'HUNDIMIENTO DE PISO',
    'INSUFICIENCIA DE ATARJEA Y COLECTOR',
    'INSUFICIENCIA DE GRIETA',
    'INSUFICIENCA DE ATARJEA Y COLECTOR', 
]

print("\n🔍 Filtrando por causas válidas...")
df = df[df['CAUSA'].str.upper().str.strip().isin([c.upper() for c in causas_validas])]
print(f"✔️ Registros después del filtro de causas: {len(df)}")

print("\n📋 Distribución de causas en los datos filtrados:")
print(df['CAUSA'].value_counts())

# --------------------------------------------
# 4. GUARDAR EXCEL FINAL
# --------------------------------------------
df.to_excel(OUTPUT_EXCEL, index=False)
print(f"\n🎉 Excel generado correctamente: {OUTPUT_EXCEL}")
