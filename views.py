import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import streamlit as st

from config import (
    CORES_RISCO, ORDEM_RISCO, CREDITO_HTML,
    LEGEND_HTML, ZOOM_JS,
)


# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar(escolas):
    with st.sidebar:
        st.title("🔎 Filtros")
        st.markdown("---")

        ra_lista = sorted(escolas["codra_nome"].dropna().unique())
        ra_sel   = st.multiselect("📍 Região Administrativa", ra_lista,
                                   placeholder="Todas as regiões")

        if ra_sel:
            bairros_disp = sorted(
                escolas[escolas["codra_nome"].isin(ra_sel)]["bairro"].dropna().unique()
            )
        else:
            bairros_disp = sorted(escolas["bairro"].dropna().unique())

        bairros_sel = st.multiselect("🏘️ Bairro(s)", bairros_disp,
                                      placeholder="Todos os bairros")

        riscos_sel = st.multiselect("🌊 Grau de Suscetibilidade", ORDEM_RISCO,
                                     default=ORDEM_RISCO)

        st.markdown("---")
        st.caption("Opções do mapa")
        show_raster  = st.toggle("Mostrar camada ISMIF",       value=True)
        show_bairros = st.toggle("Mostrar limites de bairros", value=False)
        opacity_r    = st.slider("Opacidade do raster", 0.1, 1.0, 0.25, 0.05)

        st.markdown("---")
        st.markdown(CREDITO_HTML, unsafe_allow_html=True)

    return ra_sel, bairros_sel, riscos_sel, show_raster, show_bairros, opacity_r


# ── Aba: Mapa & Análise ────────────────────────────────────────────────────────
def render_tab_mapa(df, bairros, img_b64, raster_bounds,
                    show_raster, show_bairros, opacity_r):
    total = len(df)

    st.title("Suscetibilidade ISMIF — Escolas Municipais do Rio de Janeiro")
    st.caption(
        "Visualização da suscetibilidade física a inundações (Índice ISMIF) associada "
        "às escolas municipais. Use os filtros na barra lateral para explorar por "
        "Região Administrativa, Bairro e Grau de Suscetibilidade."
    )

    # Métricas
    m_cols = st.columns(len(ORDEM_RISCO) + 1)
    m_cols[0].metric("Total filtrado", total)
    for i, sust in enumerate(ORDEM_RISCO):
        n   = (df["risco"] == sust).sum()
        pct = n / total * 100 if total else 0
        m_cols[i + 1].metric(sust, f"{n}  ({pct:.0f}%)")

    st.markdown("---")

    col_map, col_tab = st.columns([3, 1], gap="medium")

    with col_map:
        _render_map(df, bairros, img_b64, raster_bounds,
                    show_raster, show_bairros, opacity_r)

    with col_tab:
        _render_distribution_table(df, total)

    with st.expander(f"📋 Ver tabela completa ({total} escolas)"):
        _render_full_table(df)

    render_insights(df)

    st.markdown(
        "<p style='font-size:0.75rem;color:#aaa;margin-top:16px'>"
        "📁 Bases de dados: Data.Rio · IBGE · CEMADEN · INEA-RJ</p>",
        unsafe_allow_html=True,
    )


def _render_map(df, bairros, img_b64, raster_bounds,
                show_raster, show_bairros, opacity_r):
    m = folium.Map(location=[-22.92, -43.45], zoom_start=10,
                   tiles="CartoDB positron", control_scale=True)

    if show_raster:
        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{img_b64}",
            bounds=raster_bounds, opacity=opacity_r,
            name="Índice ISMIF", show=True, zindex=1,
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

    fg = folium.FeatureGroup(name="Escolas", show=True)
    for _, row in df.iterrows():
        cor     = CORES_RISCO.get(row["risco"], "#999999")
        ismif_v = row.get("valor_ismif", None)
        ismif_s = f"{ismif_v:.3f}" if pd.notna(ismif_v) else "—"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=5, color="#333333", weight=0.6,
            fill=True, fill_color=cor, fill_opacity=0.92,
            tooltip=(
                f"<b>{row['denominaca']}</b><br>"
                f"Bairro: {row['bairro']}<br>"
                f"Região Adm.: {row['codra_nome']}<br>"
                f"Suscetibilidade: <b>{row['risco']}</b><br>"
                f"ISMIF: {ismif_s}"
            ),
        ).add_to(fg)
    fg.add_to(m)

    m.get_root().html.add_child(folium.Element(LEGEND_HTML))
    m.get_root().html.add_child(folium.Element(f"<script>{ZOOM_JS}</script>"))
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, height=560, use_container_width=True, returned_objects=[])


def _render_distribution_table(df, total):
    st.subheader("Suscetibilidade ISMIF")
    if total == 0:
        st.info("Nenhuma escola para os filtros selecionados.")
        return

    resumo   = df["risco"].value_counts().reindex(ORDEM_RISCO, fill_value=0)
    pct_vals = (resumo.values / total * 100).round(1)
    st.dataframe(
        pd.DataFrame({
            "Suscetibilidade": resumo.index,
            "Qtd": resumo.values,
            "%":   pct_vals,
            " ":   pct_vals,
        }),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Qtd": st.column_config.NumberColumn(format="%d"),
            "%":   st.column_config.NumberColumn(format="%.1f%%"),
            " ":   st.column_config.ProgressColumn(format=" ", min_value=0, max_value=100),
        },
    )

    st.markdown("---")
    csv_data = (
        df[["denominaca", "bairro", "codra_nome", "risco", "valor_ismif", "lat", "lon"]]
        .rename(columns={"denominaca": "escola",
                          "codra_nome": "regiao_administrativa",
                          "risco": "suscetibilidade_ismif"})
        .to_csv(index=False)
    )
    st.download_button("⬇️ Baixar dados filtrados", data=csv_data,
                       file_name="escolas_suscetibilidade_ismif.csv",
                       mime="text/csv", use_container_width=True)


def _render_full_table(df):
    cols = [c for c in ["denominaca", "tipo", "bairro", "codra_nome", "risco", "valor_ismif"]
            if c in df.columns]
    st.dataframe(
        df[cols].rename(columns={
            "denominaca": "Escola", "tipo": "Tipo",
            "bairro": "Bairro", "codra_nome": "Região Adm.",
            "risco": "Suscetibilidade", "valor_ismif": "ISMIF",
        }).sort_values("Suscetibilidade"),
        hide_index=True, use_container_width=True,
    )


# ── Insights ───────────────────────────────────────────────────────────────────
def render_insights(df):
    st.markdown("---")
    st.subheader("📊 Insights")

    n = len(df)
    if n == 0:
        st.info("Sem dados para os filtros selecionados.")
        return

    alto_mask  = df["risco"].isin(["Alto", "Muito Alto"])
    baixo_mask = df["risco"].isin(["Muito Baixo", "Baixo"])
    n_alto     = alto_mask.sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Região c/ mais escolas\nem alto grau",
              df[alto_mask]["codra_nome"].value_counts().idxmax() if alto_mask.any() else "—")
    c2.metric("Bairro c/ mais escolas\nem alto grau",
              df[alto_mask]["bairro"].value_counts().idxmax() if alto_mask.any() else "—")
    c3.metric("Região c/ mais escolas\nem baixo grau",
              df[baixo_mask]["codra_nome"].value_counts().idxmax() if baixo_mask.any() else "—")
    c4.metric("Escolas em Alto/Muito Alto", f"{n_alto}  ({n_alto/n*100:.0f}%)")

    st.markdown("")
    col_ra, col_bairro = st.columns(2, gap="medium")

    with col_ra:
        st.markdown("**Por Região Administrativa**")
        ra_tab = (
            df.groupby(["codra_nome", "risco"]).size().unstack(fill_value=0)
            .reindex(columns=ORDEM_RISCO, fill_value=0)
        )
        ra_tab["TOTAL"]    = ra_tab.sum(axis=1)
        ra_tab["% Alto+MA"] = (
            (ra_tab.get("Alto", 0) + ra_tab.get("Muito Alto", 0))
            / ra_tab["TOTAL"] * 100
        ).round(1)

        fig = go.Figure()
        for r in ORDEM_RISCO:
            if r not in ra_tab.columns:
                continue
            ra_s = ra_tab.sort_values("TOTAL", ascending=True)
            fig.add_trace(go.Bar(
                name=r, x=ra_s[r], y=ra_s.index,
                orientation="h",
                marker_color=CORES_RISCO[r],
                marker_line_width=0.3, marker_line_color="white",
                hovertemplate=f"<b>{{y}}</b><br>{r}: %{{x}} escolas<extra></extra>",
            ))
        fig.update_layout(
            barmode="stack", height=max(320, len(ra_tab) * 22),
            margin=dict(l=10, r=10, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.01,
                        xanchor="left", x=0, font_size=9),
            xaxis_title="Escolas", plot_bgcolor="white",
            paper_bgcolor="white", font=dict(family="Arial", size=10),
            xaxis=dict(gridcolor="#eee"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_bairro:
        st.markdown("**Top 20 Bairros (por total de escolas)**")
        b_tab = (
            df.dropna(subset=["bairro"])
            .groupby(["bairro", "risco"]).size().unstack(fill_value=0)
            .reindex(columns=ORDEM_RISCO, fill_value=0)
        )
        b_tab["TOTAL"] = b_tab.sum(axis=1)
        top20 = b_tab.nlargest(20, "TOTAL").sort_values("TOTAL", ascending=True)

        fig2 = go.Figure()
        for r in ORDEM_RISCO:
            if r not in top20.columns:
                continue
            fig2.add_trace(go.Bar(
                name=r, x=top20[r], y=top20.index,
                orientation="h", showlegend=False,
                marker_color=CORES_RISCO[r],
                marker_line_width=0.3, marker_line_color="white",
                hovertemplate=f"<b>{{y}}</b><br>{r}: %{{x}} escolas<extra></extra>",
            ))
        fig2.update_layout(
            barmode="stack", height=520,
            margin=dict(l=10, r=10, t=10, b=30),
            xaxis_title="Escolas", plot_bgcolor="white",
            paper_bgcolor="white", font=dict(family="Arial", size=10),
            xaxis=dict(gridcolor="#eee"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📋 Tabela completa por Região Administrativa"):
        ra_show = ra_tab.drop(columns="TOTAL").copy()
        ra_show.insert(0, "Total", ra_tab["TOTAL"])
        ra_show.insert(1, "% Alto+MA",
                       ra_tab["% Alto+MA"].apply(lambda v: f"{v:.1f}%"))
        st.dataframe(ra_show.sort_values("Total", ascending=False),
                     use_container_width=True)


# ── Aba: Sobre o ISMIF ────────────────────────────────────────────────────────
def render_tab_sobre(escolas, total_geral):
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
        st.dataframe(pd.DataFrame({
            "Indicador": [
                "📐 Declividade do terreno (IDEC)",
                "🏙️ Impermeabilização do solo (IIMP)",
                "🌊 Proximidade de cursos d'água (IPROX)",
                "⬇️ Cota altimétrica (ICA)",
            ],
            "Como funciona": [
                "Terrenos com baixa declividade drenam mal e acumulam água. MDT 1:10.000 (pixel 5×5 m). Abaixo de 0,5%: drenagem deficiente; acima de 8%: ótima.",
                "Quanto mais impermeável o solo, menor a infiltração. Usa mapa de uso do solo (IPP/INEA 2015) com coeficientes de runoff por categoria.",
                "Áreas mais próximas de rios são mais atingidas em cheias. Considera distância (até 500 m, limite APP) e declividade até o curso d'água.",
                "Terrenos baixos sofrem influência da maré e remanso fluvial. Áreas abaixo de 2 m têm maior suscetibilidade; limite superior em 5 m.",
            ],
        }), hide_index=True, use_container_width=True,
            column_config={
                "Indicador":    st.column_config.TextColumn(width="medium"),
                "Como funciona": st.column_config.TextColumn(width="large"),
            })

        st.markdown("""
---

### Aplicação neste dashboard

As **1.590 escolas municipais do Rio de Janeiro** foram sobrepostas ao raster ISMIF
usando amostragem com buffer de 100 m, associando a cada escola o grau de suscetibilidade
física da área em que está inserida. O resultado subsidia:

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
        st.dataframe(pd.DataFrame({
            "Valor ≤":       ["0,20", "0,40", "0,60", "0,80", "1,00"],
            "Classificação": ORDEM_RISCO,
            "Descrição": [
                "Baixíssima suscetibilidade a inundações",
                "Suscetibilidade reduzida",
                "Suscetibilidade moderada",
                "Alta suscetibilidade; monitoramento recomendado",
                "Área crítica; suscetibilidade muito elevada",
            ],
        }), hide_index=True, use_container_width=True)

        st.markdown("#### Distribuição das escolas (total geral)")
        resumo_geral = (
            escolas["risco"].value_counts().reindex(ORDEM_RISCO, fill_value=0)
        )
        pct_geral = (resumo_geral.values / total_geral * 100).round(1)
        st.dataframe(
            pd.DataFrame({
                "Suscetibilidade": resumo_geral.index,
                "Qtd": resumo_geral.values,
                "%":   pct_geral,
                " ":   pct_geral,
            }),
            hide_index=True, use_container_width=True,
            column_config={
                "Qtd": st.column_config.NumberColumn(format="%d"),
                "%":   st.column_config.NumberColumn(format="%.1f%%"),
                " ":   st.column_config.ProgressColumn(format=" ", min_value=0, max_value=100),
            },
        )

import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import streamlit as st

from config import (
    CORES_RISCO, ORDEM_RISCO, CREDITO_HTML,
    LEGEND_HTML, ZOOM_JS,
)


# Sidebar 
def render_sidebar(escolas):
    with st.sidebar:
        st.title("🔎 Filtros")
        st.markdown("---")

        ra_lista = sorted(escolas["codra_nome"].dropna().unique())
        ra_sel   = st.multiselect("📍 Região Administrativa", ra_lista,
                                   placeholder="Todas as regiões")

        if ra_sel:
            bairros_disp = sorted(
                escolas[escolas["codra_nome"].isin(ra_sel)]["bairro"].dropna().unique()
            )
        else:
            bairros_disp = sorted(escolas["bairro"].dropna().unique())

        bairros_sel = st.multiselect("🏘️ Bairro(s)", bairros_disp,
                                      placeholder="Todos os bairros")

        riscos_sel = st.multiselect("🌊 Grau de Suscetibilidade", ORDEM_RISCO,
                                     default=ORDEM_RISCO)

        st.markdown("---")
        st.caption("Opções do mapa")
        show_raster  = st.toggle("Mostrar camada ISMIF",       value=True)
        show_bairros = st.toggle("Mostrar limites de bairros", value=False)
        opacity_r    = st.slider("Opacidade do raster", 0.1, 1.0, 0.25, 0.05)

        st.markdown("---")
        st.markdown(CREDITO_HTML, unsafe_allow_html=True)

    return ra_sel, bairros_sel, riscos_sel, show_raster, show_bairros, opacity_r


#Mapa e Análise 
def render_tab_mapa(df, bairros, img_b64, raster_bounds,
                    show_raster, show_bairros, opacity_r):
    total = len(df)

    st.title("Suscetibilidade ISMIF — Escolas Municipais do Rio de Janeiro")
    st.caption(
        "Visualização da suscetibilidade física a inundações (Índice ISMIF) associada "
        "às escolas municipais. Use os filtros na barra lateral para explorar por "
        "Região Administrativa, Bairro e Grau de Suscetibilidade."
    )

    # Métricas
    m_cols = st.columns(len(ORDEM_RISCO) + 1)
    m_cols[0].metric("Total filtrado", total)
    for i, sust in enumerate(ORDEM_RISCO):
        n   = (df["risco"] == sust).sum()
        pct = n / total * 100 if total else 0
        m_cols[i + 1].metric(sust, f"{n}  ({pct:.0f}%)")

    st.markdown("---")

    col_map, col_tab = st.columns([3, 1], gap="medium")

    with col_map:
        _render_map(df, bairros, img_b64, raster_bounds,
                    show_raster, show_bairros, opacity_r)

    with col_tab:
        _render_distribution_table(df, total)

    with st.expander(f"📋 Ver tabela completa ({total} escolas)"):
        _render_full_table(df)

    st.markdown(
        "<p style='font-size:0.75rem;color:#aaa;margin-top:16px'>"
        "📁 Bases de dados: Data.Rio · IBGE · CEMADEN · INEA-RJ</p>",
        unsafe_allow_html=True,
    )


def _render_map(df, bairros, img_b64, raster_bounds,
                show_raster, show_bairros, opacity_r):
    m = folium.Map(location=[-22.92, -43.45], zoom_start=10,
                   tiles="CartoDB positron", control_scale=True)

    if show_raster:
        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{img_b64}",
            bounds=raster_bounds, opacity=opacity_r,
            name="Índice ISMIF", show=True, zindex=1,
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

    fg = folium.FeatureGroup(name="Escolas", show=True)
    for _, row in df.iterrows():
        cor     = CORES_RISCO.get(row["risco"], "#999999")
        ismif_v = row.get("valor_ismif", None)
        ismif_s = f"{ismif_v:.3f}" if pd.notna(ismif_v) else "—"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=5, color="#333333", weight=0.6,
            fill=True, fill_color=cor, fill_opacity=0.92,
            tooltip=(
                f"<b>{row['denominaca']}</b><br>"
                f"Bairro: {row['bairro']}<br>"
                f"Região Adm.: {row['codra_nome']}<br>"
                f"Suscetibilidade: <b>{row['risco']}</b><br>"
                f"ISMIF: {ismif_s}"
            ),
        ).add_to(fg)
    fg.add_to(m)

    m.get_root().html.add_child(folium.Element(LEGEND_HTML))
    m.get_root().html.add_child(folium.Element(f"<script>{ZOOM_JS}</script>"))
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, height=560, use_container_width=True, returned_objects=[])


def _render_distribution_table(df, total):
    st.subheader("Suscetibilidade ISMIF")
    if total == 0:
        st.info("Nenhuma escola para os filtros selecionados.")
        return

    resumo   = df["risco"].value_counts().reindex(ORDEM_RISCO, fill_value=0)
    pct_vals = (resumo.values / total * 100).round(1)
    st.dataframe(
        pd.DataFrame({
            "Suscetibilidade": resumo.index,
            "Qtd": resumo.values,
            "%":   pct_vals,
            " ":   pct_vals,
        }),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Qtd": st.column_config.NumberColumn(format="%d"),
            "%":   st.column_config.NumberColumn(format="%.1f%%"),
            " ":   st.column_config.ProgressColumn(format=" ", min_value=0, max_value=100),
        },
    )

    st.markdown("---")
    csv_data = (
        df[["denominaca", "bairro", "codra_nome", "risco", "valor_ismif", "lat", "lon"]]
        .rename(columns={"denominaca": "escola",
                          "codra_nome": "regiao_administrativa",
                          "risco": "suscetibilidade_ismif"})
        .to_csv(index=False)
    )
    st.download_button("⬇️ Baixar dados filtrados", data=csv_data,
                       file_name="escolas_suscetibilidade_ismif.csv",
                       mime="text/csv", use_container_width=True)


def _render_full_table(df):
    cols = [c for c in ["denominaca", "tipo", "bairro", "codra_nome", "risco", "valor_ismif"]
            if c in df.columns]
    st.dataframe(
        df[cols].rename(columns={
            "denominaca": "Escola", "tipo": "Tipo",
            "bairro": "Bairro", "codra_nome": "Região Adm.",
            "risco": "Suscetibilidade", "valor_ismif": "ISMIF",
        }).sort_values("Suscetibilidade"),
        hide_index=True, use_container_width=True,
    )


# ABA sobre o ISMIF
def render_tab_sobre(escolas, total_geral):
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
        st.dataframe(pd.DataFrame({
            "Indicador": [
                "📐 Declividade do terreno (IDEC)",
                "🏙️ Impermeabilização do solo (IIMP)",
                "🌊 Proximidade de cursos d'água (IPROX)",
                "⬇️ Cota altimétrica (ICA)",
            ],
            "Como funciona": [
                "Terrenos com baixa declividade drenam mal e acumulam água. MDT 1:10.000 (pixel 5×5 m). Abaixo de 0,5%: drenagem deficiente; acima de 8%: ótima.",
                "Quanto mais impermeável o solo, menor a infiltração. Usa mapa de uso do solo (IPP/INEA 2015) com coeficientes de runoff por categoria.",
                "Áreas mais próximas de rios são mais atingidas em cheias. Considera distância (até 500 m, limite APP) e declividade até o curso d'água.",
                "Terrenos baixos sofrem influência da maré e remanso fluvial. Áreas abaixo de 2 m têm maior suscetibilidade; limite superior em 5 m.",
            ],
        }), hide_index=True, use_container_width=True,
            column_config={
                "Indicador":    st.column_config.TextColumn(width="medium"),
                "Como funciona": st.column_config.TextColumn(width="large"),
            })
    # Refs
        st.markdown("""
---

### Aplicação neste dashboard

As **1.590 escolas municipais do Rio de Janeiro** foram sobrepostas ao raster ISMIF
usando amostragem com buffer de 100 m, associando a cada escola o grau de suscetibilidade
física da área em que está inserida. O resultado subsidia:

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
        st.dataframe(pd.DataFrame({
            "Valor ≤":       ["0,20", "0,40", "0,60", "0,80", "1,00"],
            "Classificação": ORDEM_RISCO,
            "Descrição": [
                "Baixíssima suscetibilidade a inundações",
                "Suscetibilidade reduzida",
                "Suscetibilidade moderada",
                "Alta suscetibilidade; monitoramento recomendado",
                "Área crítica; suscetibilidade muito elevada",
            ],
        }), hide_index=True, use_container_width=True)

        st.markdown("#### Distribuição das escolas (total geral)")
        resumo_geral = (
            escolas["risco"].value_counts().reindex(ORDEM_RISCO, fill_value=0)
        )
        pct_geral = (resumo_geral.values / total_geral * 100).round(1)
        st.dataframe(
            pd.DataFrame({
                "Suscetibilidade": resumo_geral.index,
                "Qtd": resumo_geral.values,
                "%":   pct_geral,
                " ":   pct_geral,
            }),
            hide_index=True, use_container_width=True,
            column_config={
                "Qtd": st.column_config.NumberColumn(format="%d"),
                "%":   st.column_config.NumberColumn(format="%.1f%%"),
                " ":   st.column_config.ProgressColumn(format=" ", min_value=0, max_value=100),
            },
        )
