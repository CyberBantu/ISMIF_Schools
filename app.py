import streamlit as st

from config import APP_CSS
from data import load_escolas, load_bairros, load_raster_overlay
from views import render_sidebar, render_tab_mapa, render_tab_sobre

st.set_page_config(
    page_title="Suscetibilidade ISMIF — Escolas do Rio de Janeiro",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)

# Carregamento de dados 
escolas= load_escolas()
bairros= load_bairros()
img_b64, raster_bounds = load_raster_overlay()
total_geral= len(escolas)

# Sidebar
ra_sel, bairros_sel, riscos_sel, show_raster, show_bairros, opacity_r = (
    render_sidebar(escolas)
)

# Filtros 
df = escolas.copy()
if ra_sel:
    df = df[df["codra_nome"].isin(ra_sel)]
if bairros_sel:
    df = df[df["bairro"].isin(bairros_sel)]
if riscos_sel:
    df = df[df["risco"].isin(riscos_sel)]

# Abas
tab_mapa, tab_sobre = st.tabs(["🗺️ Mapa & Análise", "ℹ️ Sobre o ISMIF"])

with tab_mapa:
    render_tab_mapa(df, bairros, img_b64, raster_bounds,
                    show_raster, show_bairros, opacity_r)

with tab_sobre:
    render_tab_sobre(escolas, total_geral)
