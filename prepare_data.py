
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

import geopandas as gpd
import rasterio
import rasterio.mask
from shapely.geometry import mapping

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUTDIR, exist_ok=True)

print("Lendo dados de entrada...")
municipios = gpd.read_file(os.path.join(ROOT, "RJ_Municipios_2024.shp"))
gdf_rj     = municipios[municipios["NM_MUN"] == "Rio de Janeiro"].to_crs("EPSG:4326")
bairros    = gpd.read_file(os.path.join(ROOT, "Limite_de_Bairros.shp")).to_crs("EPSG:4326")
escolas    = gpd.read_file(os.path.join(ROOT, "Escolas_com_risco_ismif.shp")).to_crs("EPSG:4326")

# Shapefile trunca nomes de coluna a 10 chars — normalizar
escolas = escolas.rename(columns={
    "valor_ismi": "valor_ismif",   # truncado pelo .shp
    "regiao_adm": "codra_nome",
})
print("Colunas escolas (pos-rename):", list(escolas.columns))

# 1. GeoJSONs
print("Exportando bairros.geojson...")
bairros[["nome", "regiao_adm", "codra", "geometry"]].to_file(
    os.path.join(OUTDIR, "bairros.geojson"), driver="GeoJSON"
)

print("Exportando escolas_risco.geojson...")
cols_keep = [c for c in ["denominaca", "tipo", "cre", "bairro", "codra",
                          "codra_nome", "valor_ismif", "risco", "geometry"]
             if c in escolas.columns]
escolas[cols_keep].to_file(
    os.path.join(OUTDIR, "escolas_risco.geojson"), driver="GeoJSON"
)

# 2. Raster recortado ao municipio do Rio de Janeiro
print("Recortando raster ISMIF...")
raster_src = os.path.join(ROOT, "ISMFI_RJ-Inea_detalhado.tif")
shapes_rj  = [mapping(geom) for geom in gdf_rj.geometry]

with rasterio.open(raster_src) as src:
    out_image, out_transform = rasterio.mask.mask(
        src, shapes_rj, crop=True, nodata=src.nodata
    )
    out_meta = src.meta.copy()

out_meta.update({
    "driver":    "GTiff",
    "height":    out_image.shape[1],
    "width":     out_image.shape[2],
    "transform": out_transform,
    "compress":  "lzw",
    "dtype":     "float32",
})

raster_out = os.path.join(OUTDIR, "ISMIF_RJ_cidade.tif")
with rasterio.open(raster_out, "w", **out_meta) as dst:
    dst.write(out_image.astype("float32"))

size_mb = os.path.getsize(raster_out) / 1_048_576
print(f"Raster salvo: {raster_out}  ({size_mb:.1f} MB)")
print("Concluido!")
