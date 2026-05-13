import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from src.app.load_css import load_css
from src.database.redis_client import redis_client
from src.utils.formatters import moeda_brl, nome_combustivel, badge_style, percentual, numero_br
from src.app.components import render_update_status


load_css()
st_autorefresh(interval=10000, key="ranking_refresh")


st.markdown(
    '<h1 class="main-title">Market Intelligence</h1>',
    unsafe_allow_html=True
)

render_update_status(10)


st.markdown(
    '<p class="sub-title">Menores preços por produto e região servidos pelo Redis Sorted Set</p>',
    unsafe_allow_html=True
)


combustiveis = [
    "TODOS",
    "GASOLINA_COMUM",
    "GASOLINA_ADITIVADA",
    "ETANOL",
    "DIESEL_S10",
    "DIESEL_COMUM",
    "GNV"
]

combustivel = st.sidebar.selectbox(
    "Produto",
    combustiveis,
    format_func=nome_combustivel
)


def carregar_ranking(produto: str) -> pd.DataFrame:
    registros = []

    produtos_consulta = (
        [p for p in combustiveis if p != "TODOS"]
        if produto == "TODOS"
        else [produto]
    )

    for item in produtos_consulta:
        ranking = redis_client.zrange(
            f"ranking:{item}",
            0,
            300,
            withscores=True
        )

        for posto_id, preco in ranking:
            posto = redis_client.hgetall(f"posto:{posto_id}")

            if not posto:
                continue

            registros.append({
                "Posto": posto.get("nome_fantasia", "Não informado"),
                "Bandeira": posto.get("bandeira", "Não informado"),
                "Cidade": posto.get("cidade", "Não informado"),
                "UF": posto.get("estado", "Não informado"),
                "Região": f"{posto.get('cidade', 'N/I')} - {posto.get('estado', 'N/I')}",
                "Combustível": nome_combustivel(item),
                "Combustível técnico": item,
                "Preço": float(preco),
            })

    return pd.DataFrame(registros)


df = carregar_ranking(combustivel)

if df.empty:
    st.warning("Ranking ainda não carregado no Redis.")
    st.stop()


df = df.sort_values("Preço", ascending=True).reset_index(drop=True)
df["Preço BRL"] = df["Preço"].apply(moeda_brl)

menor = df["Preço"].min()
media = df["Preço"].mean()
maior = df["Preço"].max()
economia = ((media - menor) / media) * 100

menor_row = df.loc[df["Preço"].idxmin()]
maior_row = df.loc[df["Preço"].idxmax()]

df["diff_media"] = (df["Preço"] - media).abs()
media_row = df.loc[df["diff_media"].idxmin()]

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Menor preço</div>
        <div class="kpi-value">{moeda_brl(menor_row["Preço"])}</div>
        <div class="kpi-detail">
            {menor_row["Posto"]}<br>
            {menor_row["Região"]}<br>
            {menor_row["Combustível"]}
        </div>
        <div class="kpi-tag">melhor oportunidade</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Preço médio aproximado</div>
        <div class="kpi-value">{moeda_brl(media)}</div>
        <div class="kpi-detail">
            Posto mais próximo da média:<br>
            {media_row["Posto"]}<br>
            {media_row["Região"]}<br>
            {media_row["Combustível"]}
        </div>
        <div class="kpi-tag">referência de mercado</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Maior preço</div>
        <div class="kpi-value">{moeda_brl(maior_row["Preço"])}</div>
        <div class="kpi-detail">
            {maior_row["Posto"]}<br>
            {maior_row["Região"]}<br>
            {maior_row["Combustível"]}
        </div>
        <div class="kpi-tag">ponto de atenção</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-grid-card">
        <div class="kpi-label">Economia vs média</div>
        <div class="kpi-value">{percentual(economia)}</div>
        <div class="kpi-detail">
            Diferença entre o menor preço e a média da seleção atual.<br>
            Base: {numero_br(len(df))} registros analisados.
        </div>
        <div class="kpi-tag">ganho potencial</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("<br>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.35])

with col_left:
    st.subheader("📍 Top oportunidades")

    top = (
        df.drop_duplicates(subset=["Região", "Combustível"])
        .head(5)
        .reset_index(drop=True)
    )

    for idx, row in top.iterrows():
        posicao = idx + 1

        st.markdown(f"""
        <div class="rank-card">
            <div class="info-group">
                <div class="rank-nome">#{posicao} • {row["Posto"]}</div>
                <div class="rank-meta">{row["Região"]} • {row["Bandeira"]}</div>
                <div class="badge" style="{badge_style(row["Combustível técnico"])}">{row["Combustível"]}</div>
            </div>
            <div class="rank-price">{row["Preço BRL"]}</div>
        </div>
        """, unsafe_allow_html=True)


with col_right:
    st.subheader("📊 Comparativo executivo")

    if combustivel == "TODOS":
        comparativo = (
            df.groupby("Combustível")
            .agg(
                menor_preco=("Preço", "min"),
                preco_medio=("Preço", "mean"),
                maior_preco=("Preço", "max"),
                postos=("Posto", "count")
            )
            .reset_index()
            .sort_values("preco_medio", ascending=False)
        )

        fig = px.scatter(
            comparativo,
            x="Combustível",
            y="preco_medio",
            size="postos",
            color="preco_medio",
            color_continuous_scale="reds",
            hover_data={
                "menor_preco": ":.2f",
                "preco_medio": ":.2f",
                "maior_preco": ":.2f",
                "postos": True,
            },
            title="Preço médio por combustível"
        )

        fig.update_layout(
            xaxis_title="Combustível",
            yaxis_title="Preço médio em R$",
            coloraxis_colorbar_title="Preço médio"
        )

    else:
        comparativo = (
            df.groupby("UF")
            .agg(
                menor_preco=("Preço", "min"),
                preco_medio=("Preço", "mean"),
                maior_preco=("Preço", "max"),
                postos=("Posto", "count")
            )
            .reset_index()
            .sort_values("preco_medio", ascending=False)
        )

        fig = px.scatter(
            comparativo,
            x="UF",
            y="preco_medio",
            size="postos",
            color="preco_medio",
            color_continuous_scale="reds",
            hover_data={
                "menor_preco": ":.2f",
                "preco_medio": ":.2f",
                "maior_preco": ":.2f",
                "postos": True,
            },
            title="Preço médio por combustível"
        )

        fig.update_layout(
            xaxis_title="UF",
            yaxis_title="Preço médio em R$",
            coloraxis_colorbar_title="Preço médio"
        )

    fig.update_layout(
        template="plotly_dark",
        height=430,
        margin=dict(l=0, r=30, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.12)",
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)


st.markdown("---")

st.subheader("📑 Insights executivos")

melhor = df.iloc[0]

i1, i2, i3 = st.columns(3)

with i1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">🎯 Melhor oportunidade</div>
        <p class="insight-text">
            O posto <strong>{melhor["Posto"]}</strong> apresenta o menor preço analisado:
            <strong>{melhor["Preço BRL"]}</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i2:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">💰 Economia potencial</div>
        <p class="insight-text">
            O menor preço está <strong>{percentual(economia)}</strong> abaixo da média da seleção atual.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i3:
    st.markdown("""
    <div class="insight-card">
        <div class="insight-title">⚡ Consulta crítica</div>
        <p class="insight-text">
            Ranking por combustível e região deve ser servido pelo Redis para resposta imediata.
        </p>
    </div>
    """, unsafe_allow_html=True)


st.subheader("📋 Tabela executiva de preços")

tabela = df[[
    "Posto",
    "Bandeira",
    "Cidade",
    "UF",
    "Região",
    "Combustível",
    "Preço BRL"
]].copy()

tabela = tabela.rename(columns={
    "Preço BRL": "Preço"
})

st.dataframe(
    tabela.head(150),
    use_container_width=True,
    height=620,
    hide_index=True
)