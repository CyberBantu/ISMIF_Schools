# Suscetibilidade ISMIF — Escolas Municipais do Rio de Janeiro

**[PT]** Dashboard interativo que cruza o Índice ISMIF (suscetibilidade física a inundações) com a localização das 1.590 escolas municipais do Rio de Janeiro. Permite filtrar por Região Administrativa, Bairro e Grau de Suscetibilidade, visualizar o raster do índice sobre o mapa e baixar os dados filtrados.

**[EN]** Interactive dashboard crossing the ISMIF flood susceptibility index with the location of 1,590 municipal schools in Rio de Janeiro. Filter by Administrative Region, Neighborhood and Susceptibility Grade, visualize the raster layer and download filtered data.

---

## Run locally / Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

> The `data/` folder is already included — no extra setup needed.  
> A pasta `data/` já está incluída no repositório.

---

## Packages / Pacotes

| Package | Use |
|---|---|
| `streamlit` | Web app framework |
| `streamlit-folium` | Embed Folium maps in Streamlit |
| `folium` | Interactive Leaflet map |
| `geopandas` | Spatial data (shapefiles, GeoJSON) |
| `rasterio` | Read and clip GeoTIFF raster |
| `numpy` | Array operations |
| `pandas` | Tabular data |
| `matplotlib` | Colormap for raster rendering |
| `Pillow` | Convert raster array to PNG overlay |
| `plotly` | Charts |
| `shapely` | Geometry operations |

---

## Data / Dados

| File | Source |
|---|---|
| `ISMIF_RJ_cidade.tif` | INEA-RJ — clipped to Rio municipality |
| `escolas_risco.geojson` | Data.Rio / IPP |
| `bairros.geojson` | Data.Rio / IPP |

---

**Elaborado por Christian Basilio · [linkedin.com/in/christianbasilioo](https://www.linkedin.com/in/christianbasilioo/)**
