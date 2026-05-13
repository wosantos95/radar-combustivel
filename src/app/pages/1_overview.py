import json

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from src.app.load_css import load_css
from src.database.redis_client import redis_client
from src.utils.formatters import (
    moeda_brl,
    percentual,
    numero_br,
    nome_combustivel,
    badge_style,
)
from src.app.components import render_update_status


load_css()
st_autorefresh(interval=10000, key="overview_refresh")

st.markdown(
    '<h1 class="main-title">Executive Overview</h1>',
    unsafe_allow_html=True
)

render_update_status(10)

st.markdown(
    '<p class="sub-title">Resumo executivo de preços, volatilidade e demanda servidos pelo Redis</p>',
    unsafe_allow_html=True
)


# =========================================================
# REDIS SERVING LAYER
# =========================================================

metricas = redis_client.hgetall("metricas:overview")
eventos_redis = redis_client.lrange("eventos:recentes", 0, 499)

if not metricas or not eventos_redis:
    st.warning("Aguardando dados processados no Redis...")
    st.stop()


# =========================================================
# MÉTRICAS GERAIS
# =========================================================

total_postos = int(float(metricas.get("total_postos", 0)))
total_eventos = int(float(metricas.get("total_eventos", 0)))
total_buscas = int(float(metricas.get("total_buscas", 0)))

preco_medio = float(metricas.get("preco_medio", 0))
menor_preco = float(metricas.get("menor_preco", 0))
maior_preco = float(metricas.get("maior_preco", 0))

gap = (
    ((maior_preco - menor_preco) / menor_preco) * 100
    if menor_preco > 0
    else 0
)


# =========================================================
# EVENTOS RECENTES DO REDIS
# =========================================================

dados_eventos = []

for item in eventos_redis:
    try:
        dados_eventos.append(json.loads(item))
    except Exception:
        continue

df = pd.DataFrame(dados_eventos)

if df.empty:
    st.warning("Eventos recentes ainda não disponíveis no Redis.")
    st.stop()

df["preco_novo"] = pd.to_numeric(df["preco_novo"], errors="coerce").fillna(0)
df["variacao_pct"] = pd.to_numeric(df["variacao_pct"], errors="coerce").fillna(0)
df["Combustível"] = df["combustivel"].apply(nome_combustivel)


# =========================================================
# COMBUSTÍVEIS EM ALTA
# =========================================================

alta = (
    df.groupby(["combustivel", "Combustível"], as_index=False)
    .agg(
        variacao_media=("variacao_pct", "mean"),
        preco_medio=("preco_novo", "mean"),
        eventos=("preco_novo", "count"),
    )
    .sort_values("variacao_media", ascending=False)
    .reset_index(drop=True)
)


# =========================================================
# KPI CARDS
# =========================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Postos monitorados", numero_br(total_postos))
c2.metric("Eventos processados", numero_br(total_eventos))
c3.metric("Buscas registradas", numero_br(total_buscas))
c4.metric("Preço médio", moeda_brl(preco_medio))

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# COMBUSTÍVEIS EM ALTA + COMPARATIVO
# =========================================================

col_left, col_right = st.columns([1, 1.35])

with col_left:
    st.subheader("🔥 Combustíveis em alta")

    for idx, row in alta.head(5).iterrows():
        st.markdown(f"""
        <div class="rank-card">
            <div class="info-group">
                <div class="rank-nome">#{idx + 1} • {row["Combustível"]}</div>
                <div class="rank-meta">
                    Preço médio {moeda_brl(row["preco_medio"])}
                    • {numero_br(row["eventos"])} eventos recentes
                </div>
                <div class="badge" style="{badge_style(row["combustivel"])}">redis serving</div>
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
            "eventos": True,
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
        coloraxis_colorbar_title="Preço",
        font=dict(color="#e5e7eb"),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# EXECUTIVE INSIGHTS
# =========================================================

st.markdown("---")
st.subheader("📑 Executive Insights")

i1, i2, i3 = st.columns(3)

economia = (
    ((preco_medio - menor_preco) / preco_medio) * 100
    if preco_medio > 0
    else 0
)

combustivel_top = alta.iloc[0]["Combustível"] if not alta.empty else "Não disponível"
variacao_top = alta.iloc[0]["variacao_media"] if not alta.empty else 0

with i1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">🎯 Oportunidade de economia</div>
        <p class="insight-text">
            O menor preço está <strong>{percentual(economia)}</strong>
            abaixo da média geral processada no Redis.
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
            <strong>{combustivel_top}</strong> lidera a alta recente com 
            <strong>{percentual(variacao_top)}</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# TABELA EXECUTIVA
# =========================================================

st.subheader("📋 Tabela executiva por combustível")

tabela = alta.copy()

tabela["Preço médio"] = tabela["preco_medio"].apply(moeda_brl)
tabela["Variação média"] = tabela["variacao_media"].apply(percentual)
tabela["Eventos analisados"] = tabela["eventos"].apply(numero_br)

tabela = tabela[[
    "Combustível",
    "Preço médio",
    "Variação média",
    "Eventos analisados",
]]

st.dataframe(
    tabela,
    use_container_width=True,
    height=360,
    hide_index=True
)