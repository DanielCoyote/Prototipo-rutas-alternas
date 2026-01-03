import json

with open('zonas_inundables_iztapalapa_completo.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total features: {len(data["features"])}')
print('\nPrimeras 3 zonas históricas:')
for i in range(3):
    print(f'  {i+1}. {data["features"][i]["properties"]["nombre"]} - {data["features"][i]["properties"]["fuente"]} - Severidad {data["features"][i]["properties"]["intensidad"]}')

print('\nPrimeras 3 calles (ID 169+):')
for i in range(168, 171):
    print(f'  {data["features"][i]["properties"]["id"]}. {data["features"][i]["properties"]["nombre"]} - Severidad {data["features"][i]["properties"]["intensidad"]}')

print(f'\nÚltima zona:')
print(f'  {data["features"][-1]["properties"]["id"]}. {data["features"][-1]["properties"]["nombre"]} - Severidad {data["features"][-1]["properties"]["intensidad"]}')

print(f'\nTamaño del archivo: {len(json.dumps(data))/1024/1024:.2f} MB')
