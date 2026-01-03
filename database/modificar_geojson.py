import geopandas as gpd

# 1) Lee tu geojson original
in_path = "zonas_historicamente_inundables_(2024).geojson"
gdf = gpd.read_file(in_path)

print("CRS original:", gdf.crs)

# 2) Si no trae CRS detectado, asígnalo manualmente
# (por tu ejemplo, es EPSG:6369)
if gdf.crs is None:
    gdf = gdf.set_crs(epsg=6369)

# 3) Transforma a WGS84 (lat/lon)
gdf_4326 = gdf.to_crs(epsg=4326)

# 4) (Opcional) Asegurar MultiPolygon
gdf_4326["geometry"] = gdf_4326["geometry"].apply(
    lambda geom: geom if geom.geom_type == "MultiPolygon" else geom.buffer(0)
)

# 5) Guardar el nuevo geojson listo para web / leaflet
out_path = "zonas_iztapalapa_4326.geojson"
gdf_4326.to_file(out_path, driver="GeoJSON")

print("Guardado:", out_path)
