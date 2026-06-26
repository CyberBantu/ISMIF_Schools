import io
import base64
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib.colors as mcolors
from PIL import Image

import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Suscetibilidade ISMIF — Escolas do Rio de Janeiro",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constantes ─────────────────────────────────────────────────────────────────
CORES_RISCO = {
    "Muito Baixo": "#1a7a1a",
    "Baixo":       "#8cc63f",
    "Médio":       "#ffe066",
    "Alto":        "#ff8c00",
    "Muito Alto":  "#cc1100",
}
ORDEM_RISCO = ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
CMAP_ISMIF  = mcolors.LinearSegmentedColormap.from_list(
    "ismif", ["#1a7a1a", "#8cc63f", "#ffe066", "#ff8c00", "#cc1100"]
)

# ── Carregamento de dados (cache) ──────────────────────────────────────────────
@st.cache_data
def load_escolas():
    gdf = gpd.read_file("data/escolas_risco.geojson")
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

escolas            = load_escolas()
bairros            = load_bairros()
img_b64, raster_bounds = load_raster_overlay()
total_geral        = len(escolas)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container { padding-top: 5rem; }

  /* Seletor de abas mais visível */
  .stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 2px solid #e0e0e0;
  }
  .stTabs [data-baseweb="tab"] {
    padding: 10px 24px;
    font-size: 0.95rem;
    font-weight: 600;
  }
  .stTabs [data-baseweb="tab-highlight"] {
    background-color: #ff8c00 !important;
    height: 3px !important;
  }

  /* Card de crédito institucional */
  .credit-card {
    background: linear-gradient(135deg, #1a2940 0%, #24415e 100%);
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 8px;
    color: white;
    font-size: 0.80rem;
    line-height: 1.6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  }
  .credit-card .name {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: #f0c060;
  }
  .credit-card a {
    color: #8ec8f8;
    text-decoration: none;
    font-size: 0.78rem;
  }
  .credit-card .label {
    font-size: 0.68rem;
    color: #aaccee;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 2px;
  }

  /* Métricas */
  div[data-testid="metric-container"] { text-align: center; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔎 Filtros")
    st.markdown("---")

    # Região Administrativa (antes CODRA) — filtro primário
    ra_lista  = sorted(escolas["codra_nome"].dropna().unique())
    ra_sel    = st.multiselect("📍 Região Administrativa", ra_lista,
                               placeholder="Todas as regiões")

    # Bairro — lista filtrada pela RA selecionada
    if ra_sel:
        bairros_disponiveis = sorted(
            escolas[escolas["codra_nome"].isin(ra_sel)]["bairro"].dropna().unique()
        )
    else:
        bairros_disponiveis = sorted(escolas["bairro"].dropna().unique())

    bairros_sel = st.multiselect("🏘️ Bairro(s)", bairros_disponiveis,
                                  placeholder="Todos os bairros")

    # Grau de suscetibilidade
    riscos_sel = st.multiselect("🌊 Grau de Suscetibilidade", ORDEM_RISCO,
                                 default=ORDEM_RISCO)

    st.markdown("---")
    st.caption("Opções do mapa")
    show_raster  = st.toggle("Mostrar camada ISMIF",       value=True)
    show_bairros = st.toggle("Mostrar limites de bairros", value=False)
    opacity_r    = st.slider("Opacidade do raster", 0.1, 1.0, 0.25, 0.05)

    # ── Card institucional ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div class="credit-card">
      <div class="label">Elaborado por</div>
      <div class="name">Christian Basilio</div>
      <div style="margin-top:6px;">
        <span style="font-size:0.75rem">🔗 </span>
        <a href="https://www.linkedin.com/in/christianbasilioo/" target="_blank">
          linkedin.com/in/christianbasilioo
        </a>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Aplicar filtros ────────────────────────────────────────────────────────────
df = escolas.copy()
if ra_sel:
    df = df[df["codra_nome"].isin(ra_sel)]
if bairros_sel:
    df = df[df["bairro"].isin(bairros_sel)]
if riscos_sel:
    df = df[df["risco"].isin(riscos_sel)]

total_filtrado = len(df)

# ── Abas ──────────────────────────────────────────────────────────────────────
tab_mapa, tab_sobre = st.tabs(["🗺️ Mapa & Análise", "ℹ️ Sobre o ISMIF"])

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 1 — MAPA & ANÁLISE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_mapa:
    st.title("Suscetibilidade ISMIF — Escolas Municipais do Rio de Janeiro")
    st.caption(
        "Visualização da suscetibilidade física a inundações (Índice ISMIF) associada às escolas municipais. "
        "Use os filtros na barra lateral para explorar por Região Administrativa, Bairro e Grau de Suscetibilidade."
    )

    # ── Métricas (sem seta, só % do total filtrado) ───────────────────────────
    m_cols = st.columns(len(ORDEM_RISCO) + 1)
    m_cols[0].metric("Total filtrado", total_filtrado)
    for i, sust in enumerate(ORDEM_RISCO):
        n   = (df["risco"] == sust).sum()
        pct = n / total_filtrado * 100 if total_filtrado else 0
        m_cols[i + 1].metric(sust, f"{n}  ({pct:.0f}%)")

    st.markdown("---")

    # ── Layout: mapa | tabela ─────────────────────────────────────────────────
    col_map, col_tab = st.columns([3, 1], gap="medium")

    # ── Mapa Folium ───────────────────────────────────────────────────────────
    with col_map:
        m = folium.Map(
            location=[-22.92, -43.45],
            zoom_start=10,
            tiles="CartoDB positron",
            control_scale=True,
        )

        if show_raster:
            folium.raster_layers.ImageOverlay(
                image=f"data:image/png;base64,{img_b64}",
                bounds=raster_bounds,
                opacity=opacity_r,
                name="Índice ISMIF",
                show=True,
                zindex=1,
            ).add_to(m)

        if show_bairros:
            folium.GeoJson(
                bairros[["nome", "regiao_adm", "geometry"]].__geo_interface__,
                name="Bairros",
                style_function=lambda _: {
                    "fillColor": "none", "color": "white",
                    "weight": 0.7, "fillOpacity": 0,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["nome", "regiao_adm"],
                    aliases=["Bairro:", "Região Administrativa:"],
                ),
            ).add_to(m)

        # Escolas
        fg = folium.FeatureGroup(name="Escolas", show=True)
        for _, row in df.iterrows():
            cor     = CORES_RISCO.get(row["risco"], "#999999")
            ismif_v = row.get("valor_ismif", None)
            ismif_s = f"{ismif_v:.3f}" if pd.notna(ismif_v) else "—"
            tooltip = (
                f"<b>{row['denominaca']}</b><br>"
                f"Bairro: {row['bairro']}<br>"
                f"Região Adm.: {row['codra_nome']}<br>"
                f"Suscetibilidade: <b>{row['risco']}</b><br>"
                f"ISMIF: {ismif_s}"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5,
                color="#333333", weight=0.6,
                fill=True, fill_color=cor, fill_opacity=0.92,
                tooltip=tooltip,
            ).add_to(fg)
        fg.add_to(m)

        # Legenda HTML
        legend_html = """
        <div style='position:fixed;bottom:30px;right:10px;z-index:9999;
                    background:rgba(255,255,255,0.96);border-radius:10px;
                    padding:12px 14px;font-size:11.5px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.18);
                    border:1px solid #ddd;min-width:185px;font-family:Arial,sans-serif;'>

          <div style='font-size:12px;font-weight:700;color:#222;
                      border-bottom:2px solid #eee;padding-bottom:6px;margin-bottom:8px;'>
            Suscetibilidade ISMIF
          </div>

          <div style='font-size:9px;color:#aaa;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.05em;margin-bottom:5px;'>
            Escolas
          </div>

          <div style='display:flex;flex-direction:column;gap:4px;margin-bottom:10px'>
            <div style='display:flex;align-items:center;gap:7px'>
              <span style='width:11px;height:11px;border-radius:50%;background:#cc1100;
                           border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
              <span><b>Muito Alto</b> <span style='color:#999;font-size:10px'>&gt; 0,80</span></span>
            </div>
            <div style='display:flex;align-items:center;gap:7px'>
              <span style='width:11px;height:11px;border-radius:50%;background:#ff8c00;
                           border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
              <span><b>Alto</b> <span style='color:#999;font-size:10px'>0,61–0,80</span></span>
            </div>
            <div style='display:flex;align-items:center;gap:7px'>
              <span style='width:11px;height:11px;border-radius:50%;background:#ffe066;
                           border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
              <span><b>Médio</b> <span style='color:#999;font-size:10px'>0,41–0,60</span></span>
            </div>
            <div style='display:flex;align-items:center;gap:7px'>
              <span style='width:11px;height:11px;border-radius:50%;background:#8cc63f;
                           border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
              <span><b>Baixo</b> <span style='color:#999;font-size:10px'>0,21–0,40</span></span>
            </div>
            <div style='display:flex;align-items:center;gap:7px'>
              <span style='width:11px;height:11px;border-radius:50%;background:#1a7a1a;
                           border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
              <span><b>Muito Baixo</b> <span style='color:#999;font-size:10px'>&le; 0,20</span></span>
            </div>
          </div>

          <div style='border-top:1px dashed #e0e0e0;margin-bottom:7px'></div>

          <div style='font-size:9px;color:#aaa;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.05em;margin-bottom:5px;'>
            Raster ISMIF
          </div>

          <div style='width:100%;height:11px;
                      background:linear-gradient(to right,#1a7a1a,#8cc63f,#ffe066,#ff8c00,#cc1100);
                      border-radius:3px;border:1px solid #ccc'></div>
          <div style='display:flex;justify-content:space-between;
                      font-size:9px;color:#888;margin-top:2px'>
            <span>0,0</span><span>0,5</span><span>1,0</span>
          </div>

        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        # Marcadores responsivos ao zoom: raio menor em zoom distante
        zoom_js = folium.Element("""
        <script>
        (function() {
          function applyRadius(map) {
            var zoom = map.getZoom();
            // zoom 9 -> r=2, zoom 10 -> r=3, zoom 11 -> r=5, zoom 13+ -> r=7
            var r = Math.max(2, Math.min(7, zoom - 7));
            map.eachLayer(function(layer) {
              if (layer instanceof L.CircleMarker) {
                layer.setRadius(r);
              }
            });
          }
          document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
              var keys = Object.keys(window).filter(function(k) {
                return k.startsWith('map_');
              });
              if (!keys.length) return;
              var map = window[keys[keys.length - 1]];
              map.on('zoomend', function() { applyRadius(map); });
              applyRadius(map);
            }, 800);
          });
        })();
        </script>
        """)
        m.get_root().html.add_child(zoom_js)

        folium.LayerControl(collapsed=False).add_to(m)

        st_folium(m, height=560, use_container_width=True, returned_objects=[])

    # ── Tabela de distribuição ────────────────────────────────────────────────
    with col_tab:
        st.subheader("Suscetibilidade ISMIF")

        if total_filtrado == 0:
            st.info("Nenhuma escola para os filtros selecionados.")
        else:
            resumo = (
                df["risco"]
                .value_counts()
                .reindex(ORDEM_RISCO, fill_value=0)
            )
            pct_vals = (resumo.values / total_filtrado * 100).round(1)
            tab_df = pd.DataFrame({
                "Suscetibilidade": resumo.index,
                "Qtd": resumo.values,
                "%": pct_vals,
                " ": pct_vals,
            })
            st.dataframe(
                tab_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Qtd": st.column_config.NumberColumn(format="%d"),
                    "%":   st.column_config.NumberColumn(format="%.1f%%"),
                    " ":   st.column_config.ProgressColumn(
                        format=" ", min_value=0, max_value=100
                    ),
                },
            )

            st.markdown("---")

            # Download CSV
            csv_data = (
                df[["denominaca", "bairro", "codra_nome",
                     "risco", "valor_ismif", "lat", "lon"]]
                .rename(columns={"denominaca": "escola",
                                  "codra_nome": "regiao_administrativa",
                                  "risco": "suscetibilidade_ismif"})
                .to_csv(index=False)
            )
            st.download_button(
                "⬇️ Baixar dados filtrados",
                data=csv_data,
                file_name="escolas_suscetibilidade_ismif.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # ── Tabela expandível ─────────────────────────────────────────────────────
    with st.expander(f"📋 Ver tabela completa ({total_filtrado} escolas)"):
        cols_show = ["denominaca", "tipo", "bairro", "codra_nome", "risco", "valor_ismif"]
        cols_show = [c for c in cols_show if c in df.columns]
        st.dataframe(
            df[cols_show].rename(columns={
                "denominaca": "Escola", "tipo": "Tipo",
                "bairro": "Bairro", "codra_nome": "Região Adm.",
                "risco": "Suscetibilidade", "valor_ismif": "ISMIF",
            }).sort_values("Suscetibilidade"),
            hide_index=True,
            use_container_width=True,
        )

    st.markdown(
        "<p style='font-size:0.75rem;color:#aaa;margin-top:16px'>"
        "📁 Bases de dados: Data.Rio · IBGE · CEMADEN · INEA-RJ"
        "</p>",
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 2 — SOBRE O ISMIF
# ═══════════════════════════════════════════════════════════════════════════════
with tab_sobre:
    st.title("ℹ️ Sobre o Índice ISMIF")
    st.caption("Índice de Suscetibilidade do Meio Físico a Inundações")

    col_a, col_b = st.columns([3, 2], gap="large")

    with col_a:
        st.markdown("""
### O que é?

O **ISMIF** é um índice desenvolvido na dissertação de mestrado de Francis Martins Miranda
(COPPE/UFRJ, 2016) como ferramenta de apoio ao planejamento urbano, capaz de identificar
áreas propensas a inundações a partir de características do meio físico. Construído em
ambiente GIS com metodologia multicritério e usando a grade estatística do IBGE
(células de 200 × 200 m), o índice produz um mapeamento contínuo de suscetibilidade
que varia de **0** (menor suscetibilidade) a **1** (maior suscetibilidade).

O resultado foi calibrado e validado com manchas de inundação obtidas por modelagem
hidrológica-hidrodinâmica (HIDRO-FLU e MODCEL) em sub-bacias da cidade do Rio de Janeiro.

---

### Os quatro indicadores

O índice combina quatro aspectos do meio físico, cada um normalizado entre 0 e 100:
""")

        ind_data = pd.DataFrame({
            "Indicador": [
                "📐 Declividade do terreno (IDEC)",
                "🏙️ Impermeabilização do solo (IIMP)",
                "🌊 Proximidade de cursos d'água (IPROX)",
                "⬇️ Cota altimétrica (ICA)",
            ],
            "Como funciona": [
                "Terrenos com baixa declividade drenam mal e acumulam água. Calculado a partir de MDT 1:10.000 (pixel 5×5 m). Abaixo de 0,5%: drenagem deficiente; acima de 8%: drenagem ótima.",
                "Quanto mais impermeável o solo, menor a infiltração e maior o escoamento superficial. Usa o mapa de uso e cobertura do solo (IPP/INEA 2015) com coeficientes de runoff por categoria.",
                "Áreas mais próximas de rios e córregos são mais atingidas em eventos de cheia. Considera distância (até 500 m, limite de APP) e declividade em direção ao curso d'água.",
                "Terrenos em cotas baixas sofrem influência da maré e remanso fluvial, reduzindo a capacidade de escoamento. Áreas abaixo de 2 m têm maior suscetibilidade; o limite é 5 m.",
            ],
        })
        st.dataframe(ind_data, hide_index=True, use_container_width=True,
                     column_config={"Indicador": st.column_config.TextColumn(width="medium"),
                                    "Como funciona": st.column_config.TextColumn(width="large")})

        st.markdown("""
---

### Aplicação neste dashboard

As **1.590 escolas municipais do Rio de Janeiro** foram sobrepostas ao raster ISMIF
usando amostragem com buffer de 100 m em torno de cada ponto, associando a cada escola
o grau de suscetibilidade física da área em que está inserida. O resultado subsidia:

- 🏛️ **Políticas públicas** de prevenção e gestão de ameaças naturais
- 🔧 **Priorização de intervenções** nas unidades escolares
- 🚸 **Planejamento de contingência** e evacuação

---
> **Referência:** Miranda, F. M. (2016). *Índice de Susceptibilidade do Meio Físico a Inundações
> como Ferramenta para o Planejamento Urbano*. Dissertação de Mestrado — COPPE/UFRJ.
> **Dados:** INEA-RJ · IPP · IBGE &nbsp;|&nbsp; **Resolução:** ~30 m &nbsp;|&nbsp; **Projeção:** WGS 84
""")

    with col_b:
        st.markdown("#### Classificação do índice")
        class_data = pd.DataFrame({
            "Valor ≤": ["0,20", "0,40", "0,60", "0,80", "1,00"],
            "Classificação": ORDEM_RISCO,
            "Descrição": [
                "Baixíssima suscetibilidade a inundações",
                "Suscetibilidade reduzida",
                "Suscetibilidade moderada",
                "Alta suscetibilidade; monitoramento recomendado",
                "Área crítica; suscetibilidade muito elevada",
            ],
        })
        st.dataframe(class_data, hide_index=True, use_container_width=True)

        st.markdown("#### Distribuição das escolas (total geral)")
        resumo_geral = (
            escolas["risco"]
            .value_counts()
            .reindex(ORDEM_RISCO, fill_value=0)
        )
        pct_geral = (resumo_geral.values / total_geral * 100).round(1)
        tot_df = pd.DataFrame({
            "Suscetibilidade": resumo_geral.index,
            "Qtd": resumo_geral.values,
            "%": pct_geral,
            " ": pct_geral,
        })
        st.dataframe(
            tot_df, hide_index=True, use_container_width=True,
            column_config={
                "Qtd": st.column_config.NumberColumn(format="%d"),
                "%":   st.column_config.NumberColumn(format="%.1f%%"),
                " ":   st.column_config.ProgressColumn(
                    format=" ", min_value=0, max_value=100
                ),
            },
        )


