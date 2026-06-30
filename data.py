import io
import base64
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import geopandas as gpd
import rasterio
import matplotlib.colors as mcolors
from PIL import Image
import streamlit as st

from config import CMAP_ISMIF

# Controles de carregamento de dados

@st.cache_data
def load_escolas():
    gdf = gpd.read_file("data/escolas_risco.geojson") # base principal de dados interpolados
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y
    return gdf


@st.cache_data
def load_bairros():
    return gpd.read_file("data/bairros.geojson")


@st.cache_data
def load_raster_overlay():
    with rasterio.open("data/ISMIF_RJ_cidade.tif") as src:
        band   = src.read(1).astype(float)
        nodata = src.nodata
        b      = src.bounds

    nodata_mask = (band == nodata) | np.isnan(band)
    norm = mcolors.Normalize(vmin=0, vmax=1)
    rgba = CMAP_ISMIF(norm(np.where(nodata_mask, 0, band)))
    rgba[..., 3] = np.where(nodata_mask, 0.0, 0.80)

    img_uint8 = (rgba * 255).astype(np.uint8)
    pil_img   = Image.fromarray(img_uint8, mode="RGBA")
    buf       = io.BytesIO()
    pil_img.save(buf, format="PNG")
    img_b64   = base64.b64encode(buf.getvalue()).decode()

    folium_bounds = [[b.bottom, b.left], [b.top, b.right]]
    return img_b64, folium_bounds
