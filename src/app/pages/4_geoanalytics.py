import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk

from src.app.load_css import load_css
from src.database.redis_client import redis_client
from src.utils.formatters import numero_br, nome_combustivel


load_css()


# =========================================================
# HEADER + ATUALIZAÇÃO MANUAL
# =========================================================

col_title, col_action = st.columns([4, 1])

with col_title:
    st.markdown(
        '<h1 class="main-title">Geo & Demand Intelligence</h1>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="sub-title">Cobertura geográfica, hotzones de busca e demanda regional servidas pelo Redis</p>',
        unsafe_allow_html=True
    )

with col_action:
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("""
<div style="
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.18);
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 18px;
">
    <span style="font-size:15px;">
        ⚡ O streaming continua ativo no backend.
        Esta página usa cache para melhorar performance.
        Para refletir novas atualizações do Redis nesta visualização,
        clique em <strong>“Atualizar dados”</strong>.
    </span>
</div>
""", unsafe_allow_html=True)


# =========================================================
# HELPERS REDIS
# =========================================================

@st.cache_data
def carregar_postos_geo() -> pd.DataFrame:
    membros = redis_client.zrange("postos_geo", 0, -1)

    pipe = redis_client.pipeline()

    for posto_id in membros:
        pipe.geopos("postos_geo", posto_id)
        pipe.hgetall(f"posto:{posto_id}")

    resultados = pipe.execute()
    registros = []

    for i in range(0, len(resultados), 2):
        posicao = resultados[i]
        posto = resultados[i + 1]
        posto_id = membros[i // 2]

        if not posicao or not posicao[0] or not posto:
            continue

        longitude, latitude = posicao[0]

        registros.append({
            "posto_id": posto_id,
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


@st.cache_data
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
df_bairros = carregar_zset("buscas:bairros", 0, 200)
df_combustiveis = carregar_zset("buscas:combustiveis", 0, 10)
df_regioes = carregar_zset("buscas:regioes", 0, 200)

if df_postos.empty:
    st.warning("Aguardando dados geográficos processados no Redis...")
    st.stop()


# =========================================================
# FILTROS
# =========================================================

st.markdown("### 🎛️ Filtros da página")
st.caption(
    "Os filtros abaixo impactam o mapa, KPIs, rankings, insights e tabela desta página."
)

f1, f2, f3 = st.columns(3)

with f1:
    cidades_disponiveis = sorted(
        df_postos["Cidade"]
        .dropna()
        .unique()
        .tolist()
    )

    cidade_selecionada = st.selectbox(
        "Cidade",
        ["Todas"] + cidades_disponiveis,
        index=0,
        key="geo_cidade"
    )

df_base_bairro = df_postos.copy()

if cidade_selecionada != "Todas":
    df_base_bairro = df_base_bairro[
        df_base_bairro["Cidade"] == cidade_selecionada
    ]

with f2:
    bairros_disponiveis = sorted(
        df_base_bairro["Bairro"]
        .dropna()
        .unique()
        .tolist()
    )

    bairro_selecionado = st.selectbox(
        "Bairro",
        ["Todos"] + bairros_disponiveis,
        index=0,
        key="geo_bairro"
    )

df_base_posto = df_base_bairro.copy()

if bairro_selecionado != "Todos":
    df_base_posto = df_base_posto[
        df_base_posto["Bairro"] == bairro_selecionado
    ]

with f3:
    postos_disponiveis = sorted(
        df_base_posto["Posto"]
        .dropna()
        .unique()
        .tolist()
    )

    posto_selecionado = st.selectbox(
        "Posto de gasolina",
        ["Todos"] + postos_disponiveis,
        index=0,
        key="geo_posto"
    )


# =========================================================
# APLICAÇÃO DOS FILTROS — POSTOS
# =========================================================

df_mapa = df_postos.copy()

if cidade_selecionada != "Todas":
    df_mapa = df_mapa[df_mapa["Cidade"] == cidade_selecionada]

if bairro_selecionado != "Todos":
    df_mapa = df_mapa[df_mapa["Bairro"] == bairro_selecionado]

if posto_selecionado != "Todos":
    df_mapa = df_mapa[df_mapa["Posto"] == posto_selecionado]


# =========================================================
# APLICAÇÃO DOS FILTROS — DEMANDA
# =========================================================

df_bairros_filtrado = df_bairros.copy()

if not df_bairros_filtrado.empty:
    if cidade_selecionada != "Todas":
        df_bairros_filtrado = df_bairros_filtrado[
            df_bairros_filtrado["nome"].str.contains(
                cidade_selecionada,
                case=False,
                na=False
            )
        ]

    if bairro_selecionado != "Todos":
        df_bairros_filtrado = df_bairros_filtrado[
            df_bairros_filtrado["nome"].str.contains(
                bairro_selecionado,
                case=False,
                na=False
            )
        ]

# Posto não existe na chave buscas:bairros.
# Quando posto é selecionado, mantemos a demanda filtrada por cidade/bairro.


# =========================================================
# MÉTRICAS FILTRADAS
# =========================================================

total_buscas_filtrado = (
    int(df_bairros_filtrado["volume"].sum())
    if not df_bairros_filtrado.empty
    else 0
)

bairro_top = (
    df_bairros_filtrado.iloc[0]
    if not df_bairros_filtrado.empty
    else None
)

comb_top = (
    df_combustiveis.iloc[0]
    if not df_combustiveis.empty
    else None
)


# =========================================================
# KPI CARDS
# =========================================================

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Postos na seleção</div>
        <div class="kpi-value">{numero_br(len(df_mapa))}</div>
        <div class="kpi-detail">
            Postos filtrados via Redis GEO e HASH.
        </div>
        <div class="kpi-tag">cobertura filtrada</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    cidades_filtro = df_mapa["Cidade"].nunique() if not df_mapa.empty else 0

    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Cidades na seleção</div>
        <div class="kpi-value">{numero_br(cidades_filtro)}</div>
        <div class="kpi-detail">
            Cidades consideradas no filtro atual.
        </div>
        <div class="kpi-tag">geo</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Buscas na seleção</div>
        <div class="kpi-value">{numero_br(total_buscas_filtrado)}</div>
        <div class="kpi-detail">
            Volume de buscas compatível com cidade/bairro selecionados.
        </div>
        <div class="kpi-tag">demanda filtrada</div>
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
            Volume global consolidado: {top_volume} buscas.
        </div>
        <div class="kpi-tag">hot product</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# MAPA + TOP 5 FILTRADO
# =========================================================

col_map, col_cards = st.columns([1.4, 1])

with col_map:
    st.subheader("🗺️ Mapa executivo de cobertura filtrada")

    if df_mapa.empty:
        st.warning("Nenhum posto encontrado para os filtros selecionados.")
    else:
        if posto_selecionado != "Todos":
            titulo_mapa = f"Mapa de cobertura — {posto_selecionado}"
            latitude_mapa = df_mapa["Latitude"].mean()
            longitude_mapa = df_mapa["Longitude"].mean()
            zoom_mapa = 13.8

            df_mapa_plot = df_mapa.copy()
            df_mapa_plot["postos"] = 1
            df_mapa_plot["Local"] = (
                df_mapa_plot["Posto"].astype(str)
                + " • "
                + df_mapa_plot["Bairro"].astype(str)
                + " - "
                + df_mapa_plot["Cidade"].astype(str)
            )
            df_mapa_plot["raio"] = 220

        elif bairro_selecionado != "Todos":
            titulo_mapa = f"Mapa de cobertura — {bairro_selecionado}"
            latitude_mapa = df_mapa["Latitude"].mean()
            longitude_mapa = df_mapa["Longitude"].mean()
            zoom_mapa = 12.2

            df_mapa_plot = (
                df_mapa.groupby(["Posto", "Bairro", "Cidade", "UF"], as_index=False)
                .agg(
                    postos=("Posto", "count"),
                    Latitude=("Latitude", "mean"),
                    Longitude=("Longitude", "mean"),
                )
                .sort_values("postos", ascending=False)
                .reset_index(drop=True)
            )

            df_mapa_plot["Local"] = (
                df_mapa_plot["Posto"].astype(str)
                + " • "
                + df_mapa_plot["Bairro"].astype(str)
                + " - "
                + df_mapa_plot["Cidade"].astype(str)
            )

            df_mapa_plot["raio"] = 260

        elif cidade_selecionada != "Todas":
            titulo_mapa = f"Mapa de cobertura — {cidade_selecionada}"
            latitude_mapa = df_mapa["Latitude"].mean()
            longitude_mapa = df_mapa["Longitude"].mean()
            zoom_mapa = 10.2

            df_mapa_plot = (
                df_mapa.groupby(["Bairro", "Cidade", "UF"], as_index=False)
                .agg(
                    postos=("Posto", "count"),
                    Latitude=("Latitude", "mean"),
                    Longitude=("Longitude", "mean"),
                )
                .sort_values("postos", ascending=False)
                .reset_index(drop=True)
            )

            df_mapa_plot["Local"] = (
                df_mapa_plot["Bairro"].astype(str)
                + " • "
                + df_mapa_plot["Cidade"].astype(str)
                + " - "
                + df_mapa_plot["UF"].astype(str)
            )

            df_mapa_plot["raio"] = df_mapa_plot["postos"].apply(
                lambda x: max(280, min(x * 180, 4500))
            )

        else:
            titulo_mapa = "Mapa de cobertura — Brasil"
            latitude_mapa = -14.2350
            longitude_mapa = -51.9253
            zoom_mapa = 3.4

            df_mapa_plot = (
                df_mapa.groupby(["Cidade", "UF"], as_index=False)
                .agg(
                    postos=("Posto", "count"),
                    Latitude=("Latitude", "mean"),
                    Longitude=("Longitude", "mean"),
                )
                .sort_values("postos", ascending=False)
                .reset_index(drop=True)
            )

            df_mapa_plot["Local"] = (
                df_mapa_plot["Cidade"].astype(str)
                + " - "
                + df_mapa_plot["UF"].astype(str)
            )

            df_mapa_plot["raio"] = df_mapa_plot["postos"].apply(
                lambda x: max(600, min(x * 900, 9000))
            )

        st.markdown(f"#### {titulo_mapa}")

        view_state = pdk.ViewState(
            latitude=latitude_mapa,
            longitude=longitude_mapa,
            zoom=zoom_mapa,
            pitch=0,
        )

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_mapa_plot,
            get_position="[Longitude, Latitude]",
            get_radius="raio",
            pickable=True,
            opacity=0.68,
            stroked=True,
            filled=True,
            get_line_color=[255, 255, 255, 90],
            get_fill_color=[34, 197, 94, 150],
            line_width_min_pixels=1,
        )

        tooltip = {
            "html": """
                <div style="font-family:Arial; font-size:13px;">
                    <b>{Local}</b><br/>
                    Postos na área: <b>{postos}</b>
                </div>
            """,
            "style": {
                "backgroundColor": "#111827",
                "color": "white",
                "border": "1px solid #374151",
                "borderRadius": "8px",
                "padding": "10px",
            },
        }

        deck = pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v11",
            initial_view_state=view_state,
            layers=[layer],
            tooltip=tooltip,
        )

        st.pydeck_chart(deck, use_container_width=True)


with col_cards:
    st.subheader("🔥 Top bairros por buscas")

    if not df_bairros_filtrado.empty:
        top_5 = df_bairros_filtrado.head(5).reset_index(drop=True)

        for idx, row in top_5.iterrows():
            st.markdown(f"""
            <div class="rank-card">
                <div class="info-group">
                    <div class="rank-nome">#{idx + 1} • {row["nome"]}</div>
                    <div class="rank-meta">Demanda compatível com o filtro atual</div>
                    <div class="badge" style="background:#dcfce7;color:#166534;">alta demanda</div>
                </div>
                <div class="rank-price">{numero_br(int(row["volume"]))}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma demanda encontrada para os filtros selecionados.")


# =========================================================
# TOP 20 BAIRROS FILTRADO
# =========================================================

if not df_bairros_filtrado.empty:
    st.markdown("---")

    st.subheader("📊 Top bairros por volume de buscas — seleção atual")

    demanda_bairro = df_bairros_filtrado.head(20).copy()

    demanda_bairro["Volume formatado"] = demanda_bairro["volume"].apply(
        lambda x: numero_br(int(x))
    )

    fig_buscas = px.bar(
        demanda_bairro,
        x="nome",
        y="volume",
        color="volume",
        text="Volume formatado",
        title="Bairros com maior intenção de busca na seleção atual",
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
# INSIGHTS FILTRADOS
# =========================================================

st.markdown("---")

st.subheader("📑 Insights executivos da seleção")

i1, i2, i3 = st.columns(3)

with i1:
    hotzone = bairro_top["nome"] if bairro_top is not None else "Não disponível"
    hotzone_volume = int(bairro_top["volume"]) if bairro_top is not None else 0

    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">📍 Hotzone da seleção</div>
        <p class="insight-text">
            <strong>{hotzone}</strong> concentra o maior volume de buscas
            dentro do contexto filtrado.
            <br>
            Volume: <strong>{numero_br(hotzone_volume)}</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i2:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">🗺️ Cobertura filtrada</div>
        <p class="insight-text">
            A seleção atual possui <strong>{numero_br(len(df_mapa))}</strong> postos.
            <br>
            Essa visão é servida a partir de Redis GEO + HASH.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i3:
    st.markdown("""
    <div class="insight-card">
        <div class="insight-title">⚡ Serving Layer</div>
        <p class="insight-text">
            A página combina Redis GEO, HASH e Sorted Sets para entregar leitura analítica rápida.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# TABELA
# =========================================================

st.subheader("📋 Tabela executiva de buscas da seleção")

if not df_bairros_filtrado.empty:
    tabela_buscas = df_bairros_filtrado.copy()

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
else:
    st.info("Nenhuma busca encontrada para a seleção atual.")