import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from src.app.load_css import load_css
from src.database.mongo_client import get_database
from src.utils.formatters import moeda_brl, percentual, numero_br, nome_combustivel, badge_style
from src.app.components import render_update_status

load_css()
st_autorefresh(interval=10000, key="overview_refresh")

db = get_database()

st.markdown('<h1 class="main-title">Executive Overview</h1>', unsafe_allow_html=True)

render_update_status(10)

st.markdown(
    '<p class="sub-title">Resumo executivo de preços, volatilidade e demanda</p>',
    unsafe_allow_html=True
)

eventos = list(db.eventos_preco.find())
postos = list(db.postos.find())
buscas = list(db.buscas_usuarios.find())

if not eventos or not postos:
    st.warning("Aguardando dados...")
    st.stop()

df = pd.DataFrame(eventos)
df["Combustível"] = df["combustivel"].apply(nome_combustivel)

preco_medio = df["preco_novo"].mean()
menor_preco = df["preco_novo"].min()
maior_preco = df["preco_novo"].max()
gap = ((maior_preco - menor_preco) / menor_preco) * 100

alta = (
    df.groupby(["combustivel", "Combustível"])
    .agg(
        variacao_media=("variacao_pct", "mean"),
        preco_medio=("preco_novo", "mean"),
        eventos=("preco_novo", "count")
    )
    .sort_values("variacao_media", ascending=False)
    .reset_index()
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Postos monitorados", numero_br(len(postos)))
c2.metric("Eventos processados", numero_br(len(eventos)))
c3.metric("Menor preço", moeda_brl(menor_preco))
c4.metric("Preço médio", moeda_brl(preco_medio))

st.markdown("<br>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.35])

with col_left:
    st.subheader("🔥 Combustíveis em alta")

    for idx, row in alta.head(5).iterrows():
        st.markdown(f"""
        <div class="rank-card">
            <div class="info-group">
                <div class="rank-nome">#{idx + 1} • {row["Combustível"]}</div>
                <div class="rank-meta">Preço médio {moeda_brl(row["preco_medio"])} • {numero_br(row["eventos"])} eventos</div>
                <div class="badge" style="{badge_style(row["combustivel"])}">mercado</div>
            </div>
            <div class="rank-price">{percentual(row["variacao_media"])}</div>
        </div>
        """, unsafe_allow_html=True)

with col_right:
    st.subheader("📊 Comparativo de mercado")

    fig = px.scatter(
        alta,
        x="preco_medio",
        y="variacao_media",
        size="eventos",
        color="preco_medio",
        color_continuous_scale="Turbo",
        hover_name="Combustível",
        hover_data={
            "preco_medio": ":.2f",
            "variacao_media": ":.2f",
            "eventos": True
        },
        title="Preço médio x variação média por combustível"
    )

    fig.update_layout(
        template="plotly_dark",
        height=430,
        margin=dict(l=0, r=0, t=45, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Preço médio em R$",
        yaxis_title="Variação média %",
        coloraxis_colorbar_title="Preço"
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("📑 Executive Insights")

i1, i2, i3 = st.columns(3)

with i1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">🎯 Oportunidade de economia</div>
        <p class="insight-text">
            O menor preço está <strong>{percentual((preco_medio - menor_preco) / preco_medio * 100)}</strong>
            abaixo da média geral.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i2:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">⚠️ Volatilidade</div>
        <p class="insight-text">
            O gap entre menor e maior preço é de <strong>{percentual(gap)}</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

with i3:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">🔥 Combustível em alta</div>
        <p class="insight-text">
            <strong>{alta.iloc[0]["Combustível"]}</strong> lidera a alta com 
            <strong>{percentual(alta.iloc[0]["variacao_media"])}</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.subheader("📋 Tabela executiva por combustível")

tabela = alta.copy()
tabela["Preço médio"] = tabela["preco_medio"].apply(moeda_brl)
tabela["Variação média"] = tabela["variacao_media"].apply(percentual)
tabela["Eventos analisados"] = tabela["eventos"].apply(numero_br)

tabela = tabela[[
    "Combustível",
    "Preço médio",
    "Variação média",
    "Eventos analisados"
]]

st.dataframe(
    tabela,
    use_container_width=True,
    height=360,
    hide_index=True
)