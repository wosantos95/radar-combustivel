import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from src.app.load_css import load_css
from src.database.redis_client import redis_client
from src.utils.formatters import numero_br, nome_combustivel
from src.app.components import render_update_status


load_css()
st_autorefresh(interval=5000, key="geo_demand_refresh")

st.markdown(
    '<h1 class="main-title">Geo & Demand Intelligence</h1>',
    unsafe_allow_html=True
)

render_update_status(5)

st.markdown(
    '<p class="sub-title">Cobertura geográfica, hotzones de busca e demanda regional servidas pelo Redis</p>',
    unsafe_allow_html=True
)


# =========================================================
# HELPERS REDIS
# =========================================================

def carregar_postos_geo() -> pd.DataFrame:
    membros = redis_client.zrange("postos_geo", 0, -1)

    registros = []

    for posto_id in membros:
        posicao = redis_client.geopos("postos_geo", posto_id)
        posto = redis_client.hgetall(f"posto:{posto_id}")

        if not posicao or not posicao[0] or not posto:
            continue

        longitude, latitude = posicao[0]

        registros.append({
            "Posto": posto.get("nome_fantasia", "Não informado"),
            "Bandeira": posto.get("bandeira", "Não informado"),
            "Bairro": posto.get("bairro", "Não informado"),
            "Cidade": posto.get("cidade", "Não informado"),
            "UF": posto.get("estado", "Não informado"),
            "Latitude": float(latitude),
            "Longitude": float(longitude),
        })

    df = pd.DataFrame(registros)

    if not df.empty:
        df = df[
            (df["Latitude"].between(-33.8, 5.3)) &
            (df["Longitude"].between(-73.5, -34.8))
        ]

    return df


def carregar_zset(chave: str, inicio: int = 0, fim: int = 19) -> pd.DataFrame:
    dados = redis_client.zrevrange(
        chave,
        inicio,
        fim,
        withscores=True
    )

    return pd.DataFrame(
        dados,
        columns=["nome", "volume"]
    )


# =========================================================
# DATA LOAD — REDIS SERVING LAYER
# =========================================================

metricas = redis_client.hgetall("metricas:overview")

df_postos = carregar_postos_geo()

df_bairros = carregar_zset("buscas:bairros", 0, 19)
df_combustiveis = carregar_zset("buscas:combustiveis", 0, 10)
df_regioes = carregar_zset("buscas:regioes", 0, 10)

if df_postos.empty:
    st.warning("Aguardando dados geográficos processados no Redis...")
    st.stop()

total_buscas = int(float(metricas.get("total_buscas", 0))) if metricas else 0

if not df_bairros.empty:
    bairro_top = df_bairros.iloc[0]
else:
    bairro_top = None

if not df_combustiveis.empty:
    comb_top = df_combustiveis.iloc[0]
else:
    comb_top = None


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
            Postos recuperados via Redis GEO e HASH.
        </div>
        <div class="kpi-tag">redis geo</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Estados cobertos</div>
        <div class="kpi-value">{numero_br(df_postos["UF"].nunique())}</div>
        <div class="kpi-detail">
            UFs identificadas na camada de serving.
        </div>
        <div class="kpi-tag">cobertura</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Volume total de buscas</div>
        <div class="kpi-value">{numero_br(total_buscas)}</div>
        <div class="kpi-detail">
            Total consolidado no Redis a partir do MongoDB.
        </div>
        <div class="kpi-tag">demanda</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    top_texto = nome_combustivel(comb_top["nome"]) if comb_top is not None else "N/I"
    top_volume = numero_br(int(comb_top["volume"])) if comb_top is not None else "0"

    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Produto mais buscado</div>
        <div class="kpi-value">{top_texto}</div>
        <div class="kpi-detail">
            Volume consolidado: {top_volume} buscas.
        </div>
        <div class="kpi-tag">hot product</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# MAPA + TOP 5 BAIRROS
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

    if not df_bairros.empty:
        top_5 = df_bairros.head(5).reset_index(drop=True)

        for idx, row in top_5.iterrows():
            st.markdown(f"""
            <div class="rank-card">
                <div class="info-group">
                    <div class="rank-nome">#{idx + 1} • {row["nome"]}</div>
                    <div class="rank-meta">Volume consolidado via Redis Sorted Set</div>
                    <div class="badge" style="background:#dcfce7;color:#166534;">alta demanda</div>
                </div>
                <div class="rank-price">{numero_br(int(row["volume"]))}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aguardando dados de buscas no Redis.")


# =========================================================
# TOP 20 BAIRROS
# =========================================================

if not df_bairros.empty:
    st.markdown("---")

    st.subheader("📊 Top 20 bairros por volume de buscas")

    demanda_bairro = df_bairros.copy()
    demanda_bairro["Volume formatado"] = demanda_bairro["volume"].apply(
        lambda x: numero_br(int(x))
    )

    fig_buscas = px.bar(
        demanda_bairro,
        x="nome",
        y="volume",
        color="volume",
        text="Volume formatado",
        title="Bairros com maior intenção de busca",
        color_continuous_scale=[
            [0.0, "#dcfce7"],
            [0.25, "#86efac"],
            [0.50, "#22c55e"],
            [0.75, "#15803d"],
            [1.0, "#052e16"],
        ],
        hover_data={
            "nome": True,
            "volume": True,
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
        height=580,
        margin=dict(l=0, r=20, t=60, b=160),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Bairro / Cidade - UF",
        yaxis_title="Volume de buscas",
        coloraxis_showscale=False,
        xaxis_tickangle=-40,
        bargap=0.26,
        font=dict(color="#e5e7eb"),
        title=dict(
            font=dict(size=16, color="#f8fafc")
        )
    )

    fig_buscas.update_xaxes(
        categoryorder="array",
        categoryarray=demanda_bairro["nome"].tolist(),
        showgrid=False
    )

    fig_buscas.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False
    )

    st.plotly_chart(fig_buscas, use_container_width=True)


# =========================================================
# INSIGHTS
# =========================================================

st.markdown("---")

st.subheader("📑 Insights executivos de demanda")

i1, i2, i3 = st.columns(3)

with i1:
    hotzone = bairro_top["nome"] if bairro_top is not None else "Não disponível"
    hotzone_volume = int(bairro_top["volume"]) if bairro_top is not None else 0

    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">📍 Hotzone regional</div>
        <p class="insight-text">
            <strong>{hotzone}</strong> concentra o maior volume de buscas,
            com <strong>{numero_br(hotzone_volume)}</strong> ocorrências.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i2:
    produto = nome_combustivel(comb_top["nome"]) if comb_top is not None else "Não disponível"
    produto_volume = int(comb_top["volume"]) if comb_top is not None else 0

    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">⛽ Produto de maior interesse</div>
        <p class="insight-text">
            <strong>{produto}</strong> lidera a intenção de busca,
            com <strong>{numero_br(produto_volume)}</strong> registros.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i3:
    st.markdown("""
    <div class="insight-card">
        <div class="insight-title">⚡ Serving Layer</div>
        <p class="insight-text">
            Buscas por bairro, produto e região são consolidadas em Redis Sorted Sets para leitura rápida.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# TABELA
# =========================================================

st.subheader("📋 Tabela executiva de buscas por bairro")

tabela_buscas = df_bairros.copy()

tabela_buscas["Volume de buscas"] = tabela_buscas["volume"].apply(
    lambda x: numero_br(int(x))
)

tabela_buscas = tabela_buscas.rename(columns={
    "nome": "Bairro / Região"
})

tabela_buscas = tabela_buscas[[
    "Bairro / Região",
    "Volume de buscas"
]]

st.dataframe(
    tabela_buscas.head(120),
    use_container_width=True,
    height=620,
    hide_index=True
)