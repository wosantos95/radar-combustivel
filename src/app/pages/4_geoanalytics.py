import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from src.app.load_css import load_css
from src.database.mongo_client import get_database
from src.utils.formatters import numero_br, nome_combustivel
from src.app.components import render_update_status


load_css()
st_autorefresh(interval=5000, key="geo_demand_refresh")

db = get_database()

st.markdown(
    '<h1 class="main-title">Geo & Demand Intelligence</h1>',
    unsafe_allow_html=True
)

render_update_status(5)

st.markdown(
    '<p class="sub-title">Cobertura geográfica dos postos, hotzones de busca e consultas sensíveis à latência</p>',
    unsafe_allow_html=True
)


# =========================================================
# DATA LOAD
# =========================================================

postos = list(db.postos.find().limit(3000))
buscas = list(db.buscas_usuarios.find())

if not postos:
    st.warning("Aguardando dados de postos...")
    st.stop()


# =========================================================
# POSTOS / MAPA
# =========================================================

dados_postos = []

for posto in postos:
    geo = posto.get("location", {}).get("coordinates")

    if not geo or len(geo) != 2:
        continue

    longitude = geo[0]
    latitude = geo[1]

    dados_postos.append({
        "Latitude": latitude,
        "Longitude": longitude,
        "Posto": posto.get("nome_fantasia", "Não informado"),
        "Cidade": posto.get("endereco", {}).get("cidade", "Não informado"),
        "UF": posto.get("endereco", {}).get("estado", "Não informado"),
        "Bandeira": posto.get("bandeira", "Não informado"),
        "Bairro": posto.get("endereco", {}).get("bairro", "Não informado"),
    })

df_postos = pd.DataFrame(dados_postos)

df_postos = df_postos[
    (df_postos["Latitude"].between(-33.8, 5.3)) &
    (df_postos["Longitude"].between(-73.5, -34.8))
]

if df_postos.empty:
    st.warning("Nenhuma coordenada válida encontrada dentro do Brasil.")
    st.stop()


# =========================================================
# BUSCAS / DEMANDA
# =========================================================

if buscas:
    df_buscas = pd.DataFrame(buscas)

    if "bairro" not in df_buscas.columns:
        df_buscas["bairro"] = df_buscas["cidade"]

    df_buscas["Combustível"] = df_buscas["tipo_combustivel"].apply(nome_combustivel)

    df_buscas["Região"] = (
        df_buscas["bairro"].astype(str)
        + " • "
        + df_buscas["cidade"].astype(str)
        + " - "
        + df_buscas["estado"].astype(str)
    )

    total_buscas = df_buscas["resultado_count"].sum()

    bairro_top = (
        df_buscas.groupby("Região", as_index=False)["resultado_count"]
        .sum()
        .sort_values("resultado_count", ascending=False)
        .iloc[0]
    )

    comb_top = (
        df_buscas.groupby("Combustível", as_index=False)["resultado_count"]
        .sum()
        .sort_values("resultado_count", ascending=False)
        .iloc[0]
    )

    latencia_media = df_buscas["latencia_ms"].mean()

else:
    df_buscas = pd.DataFrame()
    total_buscas = 0
    bairro_top = None
    comb_top = None
    latencia_media = 0


# =========================================================
# KPI CARDS
# =========================================================

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Postos no mapa</div>
        <div class="kpi-value">{numero_br(len(df_postos))}</div>
        <div class="kpi-detail">
            Postos com coordenadas válidas dentro do Brasil.
        </div>
        <div class="kpi-tag">cobertura</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Estados cobertos</div>
        <div class="kpi-value">{numero_br(df_postos["UF"].nunique())}</div>
        <div class="kpi-detail">
            UFs identificadas na base geográfica.
        </div>
        <div class="kpi-tag">geo</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Volume total de buscas</div>
        <div class="kpi-value">{numero_br(total_buscas)}</div>
        <div class="kpi-detail">
            Soma dos resultados retornados nas consultas.
        </div>
        <div class="kpi-tag">demanda</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Latência média</div>
        <div class="kpi-value">{latencia_media:.0f} ms</div>
        <div class="kpi-detail">
            Indicador usado para priorizar serving em Redis.
        </div>
        <div class="kpi-tag">performance</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# MAPA + TOP 5
# =========================================================

col_map, col_cards = st.columns([1.4, 1])

with col_map:
    st.subheader("🗺️ Mapa executivo de cobertura")

    f1, f2 = st.columns(2)

    with f1:
        ufs_disponiveis = sorted(df_postos["UF"].dropna().unique().tolist())

        uf_selecionada = st.selectbox(
            "UF",
            ["Todos"] + ufs_disponiveis,
            index=0
        )

    with f2:
        bandeiras_disponiveis = sorted(df_postos["Bandeira"].dropna().unique().tolist())

        bandeira_selecionada = st.selectbox(
            "Rede de combustível",
            ["Todas"] + bandeiras_disponiveis,
            index=0
        )

    df_mapa = df_postos.copy()

    if uf_selecionada != "Todos":
        df_mapa = df_mapa[df_mapa["UF"] == uf_selecionada]

    if bandeira_selecionada != "Todas":
        df_mapa = df_mapa[df_mapa["Bandeira"] == bandeira_selecionada]

    if df_mapa.empty:
        st.warning("Nenhum posto encontrado para os filtros selecionados.")
    else:
        top_regioes_mapa = (
            df_mapa.groupby(["Cidade", "UF", "Bandeira"], as_index=False)
            .agg(
                postos=("Posto", "count"),
                Latitude=("Latitude", "mean"),
                Longitude=("Longitude", "mean"),
            )
            .sort_values("postos", ascending=False)
            .head(20)
            .reset_index(drop=True)
        )

        top_regioes_mapa["Região"] = (
            top_regioes_mapa["Cidade"].astype(str)
            + " - "
            + top_regioes_mapa["UF"].astype(str)
        )

        if uf_selecionada == "Todos":
            zoom_mapa = 3.4
            centro_mapa = {
                "lat": -14.2350,
                "lon": -51.9253
            }
        else:
            zoom_mapa = 5.8
            centro_mapa = {
                "lat": top_regioes_mapa["Latitude"].mean(),
                "lon": top_regioes_mapa["Longitude"].mean()
            }

        fig_map = px.scatter_map(
            top_regioes_mapa,
            lat="Latitude",
            lon="Longitude",
            size="postos",
            color="Bandeira",
            hover_name="Região",
            hover_data={
                "postos": True,
                "Bandeira": True,
                "Latitude": False,
                "Longitude": False,
            },
            zoom=zoom_mapa,
            center=centro_mapa,
            height=650
        )

        fig_map.update_traces(
            marker=dict(
                opacity=0.82
            )
        )

        fig_map.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend_title_text="Rede",
        )

        st.plotly_chart(fig_map, use_container_width=True)

with col_cards:
    st.subheader("🔥 Top 5 bairros por buscas")

    if not df_buscas.empty:
        top_bairros = (
            df_buscas.groupby(["bairro", "cidade", "estado"], as_index=False)["resultado_count"]
            .sum()
            .sort_values("resultado_count", ascending=False)
            .head(5)
            .reset_index(drop=True)
        )

        for idx, row in top_bairros.iterrows():
            st.markdown(f"""
            <div class="rank-card">
                <div class="info-group">
                    <div class="rank-nome">#{idx + 1} • {row["bairro"]}</div>
                    <div class="rank-meta">{row["cidade"]} - {row["estado"]}</div>
                    <div class="badge" style="background:#dcfce7;color:#166534;">alta demanda</div>
                </div>
                <div class="rank-price">{numero_br(row["resultado_count"])}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aguardando dados de buscas.")


# =========================================================
# TOP 20 REGIÕES
# =========================================================

if not df_buscas.empty:
    st.markdown("---")

    st.subheader("📊 Top 20 regiões por volume de buscas")

    demanda_regiao = (
        df_buscas.groupby(["bairro","cidade" ,"estado"], as_index=False)
        .agg(
            resultado_count=("resultado_count", "sum"),
            consultas=("session_id", "count"),
            latencia_media=("latencia_ms", "mean")
        )
        .sort_values("resultado_count", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

    demanda_regiao["Região"] = (
        demanda_regiao["bairro"].astype(str)
        + " - "
        + demanda_regiao["cidade"].astype(str)
        + " - "
        + demanda_regiao["estado"].astype(str)
    )

    demanda_regiao["Volume formatado"] = demanda_regiao["resultado_count"].apply(numero_br)

    fig_buscas = px.bar(
        demanda_regiao,
        x="Região",
        y="resultado_count",
        color="resultado_count",
        text="Volume formatado",
        title="Regiões com maior intenção de busca",
        color_continuous_scale=[
            [0.0, "#dcfce7"],
            [0.25, "#86efac"],
            [0.50, "#22c55e"],
            [0.75, "#15803d"],
            [1.0, "#052e16"],
        ],
        hover_data={
            "Região": True,
            "resultado_count": True,
            "consultas": True,
            "latencia_media": ":.0f",
            "cidade": False,
            "estado": False,
            "Volume formatado": False,
        }
    )

    fig_buscas.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
        opacity=0.96
    )

    fig_buscas.update_layout(
        template="plotly_dark",
        height=560,
        margin=dict(l=0, r=20, t=60, b=130),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Região",
        yaxis_title="Volume de buscas",
        coloraxis_showscale=False,
        xaxis_tickangle=-40,
        bargap=0.26,
        barmode="relative",
        font=dict(color="#e5e7eb"),
        title=dict(
            font=dict(size=16, color="#f8fafc")
        )
    )

    fig_buscas.update_xaxes(
        categoryorder="array",
        categoryarray=demanda_regiao["Região"].tolist(),
        showgrid=False
    )

    fig_buscas.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False
    )

    st.plotly_chart(fig_buscas, use_container_width=True)


    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown("---")

    st.subheader("📑 Insights executivos de demanda")

    i1, i2, i3 = st.columns(3)

    with i1:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">📍 Hotzone regional</div>
            <p class="insight-text">
                <strong>{bairro_top["Região"]}</strong> concentra o maior volume de buscas.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with i2:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">⛽ Produto de maior interesse</div>
            <p class="insight-text">
                <strong>{comb_top["Combustível"]}</strong> lidera a intenção de busca dos usuários.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with i3:
        st.markdown("""
        <div class="insight-card">
            <div class="insight-title">⚡ Serving Layer</div>
            <p class="insight-text">
                Buscas por bairro, combustível e proximidade são candidatas naturais para Redis GEO e Redis Sorted Sets.
            </p>
        </div>
        """, unsafe_allow_html=True)


    # =====================================================
    # TABELA
    # =====================================================

    st.subheader("📋 Tabela executiva de buscas")

    tabela_buscas = (
        df_buscas.groupby(["bairro", "cidade", "estado", "Combustível"], as_index=False)
        .agg(
            volume_buscas=("resultado_count", "sum"),
            latencia_media=("latencia_ms", "mean"),
            sessoes=("session_id", "count")
        )
        .sort_values("volume_buscas", ascending=False)
    )

    tabela_buscas["Volume de buscas"] = tabela_buscas["volume_buscas"].apply(numero_br)

    tabela_buscas["Latência média"] = (
        tabela_buscas["latencia_media"]
        .round(0)
        .astype(int)
        .astype(str)
        + " ms"
    )

    tabela_buscas["Sessões"] = tabela_buscas["sessoes"].apply(numero_br)

    tabela_buscas = tabela_buscas.rename(columns={
        "bairro": "Bairro",
        "cidade": "Cidade",
        "estado": "UF"
    })

    tabela_buscas = tabela_buscas[[
        "Bairro",
        "Cidade",
        "UF",
        "Combustível",
        "Volume de buscas",
        "Latência média",
        "Sessões"
    ]]

    st.dataframe(
        tabela_buscas.head(120),
        use_container_width=True,
        height=620,
        hide_index=True
    )