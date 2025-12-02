from dbfread import DBF
import pandas as pd

DBF_PATH = "encharcamientos_2000_2017_e.dbf"
DICT_PATH = "diccionario_datos_encharcamiento_2000_2017_e.csv"
OUTPUT_EXCEL = "encharcamientos_2000_2017.xlsx"

# --------------------------------------------
# 1. LEER EL DBF SIN PARSEAR FECHAS
# --------------------------------------------
print("📥 Leyendo DBF sin convertir fechas...")
table = DBF(DBF_PATH, load=True, char_decode_errors='ignore')

# Convertir a DataFrame
df = pd.DataFrame(iter(table))

print("✔️ Columnas cargadas desde el DBF:")
print(df.columns.tolist())

# --------------------------------------------
# 2. LEER DICCIONARIO DE DATOS
# --------------------------------------------
print("\n📥 Leyendo diccionario...")
diccionario = pd.read_csv(DICT_PATH)

cols_dict = diccionario.columns.tolist()
print("✔️ Columnas encontradas en diccionario:", cols_dict)

# Posibles nombres de columnas
posibles_nombres_campo = ["campo", "nombre", "columna", "atributo", "nombre_campo"]
posibles_nombres_desc = ["descripcion", "descripción", "nombre_limpio", "nombre_amigable"]

col_campo = next((c for c in posibles_nombres_campo if c in cols_dict), None)
col_desc = next((c for c in posibles_nombres_desc if c in cols_dict), None)

if col_campo and col_desc:
    rename_map = {
        row[col_campo]: row[col_desc]
        for _, row in diccionario.iterrows()
        if row[col_campo] in df.columns
    }
    print("\n🔄 Renombrando columnas con el diccionario:")
    print(rename_map)

    df = df.rename(columns=rename_map)
else:
    print("⚠️ No se encontraron columnas válidas para renombrar.")

# --------------------------------------------
# 3. GUARDAR EXCEL FINAL
# --------------------------------------------
df.to_excel(OUTPUT_EXCEL, index=False)
print(f"\n🎉 Excel generado correctamente: {OUTPUT_EXCEL}")
