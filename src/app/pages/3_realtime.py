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
st_autorefresh(interval=5000, key="realtime_refresh")

st.markdown(
    '<h1 class="main-title">Real-Time Operations</h1>',
    unsafe_allow_html=True,
)

render_update_status(5)

st.markdown(
    '<p class="sub-title">Monitoramento executivo das alterações de preço servidas pelo Redis</p>',
    unsafe_allow_html=True,
)


# =========================================================
# DATA LOAD — REDIS SERVING LAYER
# =========================================================

eventos_redis = redis_client.lrange("eventos:recentes", 0, 499)

if not eventos_redis:
    st.warning("Aguardando eventos processados no Redis...")
    st.stop()

dados = []

for item in eventos_redis:
    try:
        dados.append(json.loads(item))
    except Exception:
        continue

df = pd.DataFrame(dados)

if df.empty:
    st.warning("Eventos recentes ainda não disponíveis no Redis.")
    st.stop()


# =========================================================
# DATA QUALITY / FORMAT
# =========================================================

df["preco_anterior"] = pd.to_numeric(
    df["preco_anterior"],
    errors="coerce"
).fillna(0)

df["preco_novo"] = pd.to_numeric(
    df["preco_novo"],
    errors="coerce"
).fillna(0)

df["variacao_pct"] = pd.to_numeric(
    df["variacao_pct"],
    errors="coerce"
).fillna(0)

df["ocorrido_em"] = pd.to_datetime(
    df["ocorrido_em"],
    errors="coerce"
)

df = df.dropna(subset=["ocorrido_em"])

df["Combustível"] = df["combustivel"].apply(nome_combustivel)

maior_alta = df["variacao_pct"].max()
maior_queda = df["variacao_pct"].min()
preco_medio = df["preco_novo"].mean()
eventos_count = len(df)


# =========================================================
# KPI CARDS
# =========================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Eventos recentes", numero_br(eventos_count))
c2.metric("Maior alta", percentual(maior_alta))
c3.metric("Maior queda", percentual(maior_queda))
c4.metric("Preço médio recente", moeda_brl(preco_medio))

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# TOP VARIAÇÕES + LINHA POR MINUTO
# =========================================================

col_left, col_right = st.columns([1, 1.35])

with col_left:
    st.subheader("🚨 Maiores variações recentes")

    top_var = (
        df.sort_values("variacao_pct", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )

    for idx, row in top_var.iterrows():
        st.markdown(f"""
        <div class="rank-card">
            <div class="info-group">
                <div class="rank-nome">#{idx + 1} • {row["Combustível"]}</div>
                <div class="rank-meta">
                    {moeda_brl(row["preco_anterior"])} → {moeda_brl(row["preco_novo"])}
                    • Fonte: {row["fonte"]}
                </div>
                <div class="badge" style="{badge_style(row["combustivel"])}">redis realtime</div>
            </div>
            <div class="rank-price">{percentual(row["variacao_pct"])}</div>
        </div>
        """, unsafe_allow_html=True)

with col_right:
    st.subheader("📈 Preço médio por minuto")

    df_tempo = df.copy()

    df_tempo["Minuto"] = (
        df_tempo["ocorrido_em"]
        .dt.floor("min")
    )

    tendencia_tempo = (
        df_tempo.groupby(
            ["Minuto", "Combustível"],
            as_index=False
        )["preco_novo"]
        .mean()
        .sort_values("Minuto")
    )

    fig = px.line(
        tendencia_tempo,
        x="Minuto",
        y="preco_novo",
        color="Combustível",
        template="plotly_dark",
        title="Preço médio por combustível a cada minuto",
        line_shape="spline",
        color_discrete_sequence=[
            "#3b82f6",
            "#f97316",
            "#22c55e",
            "#a855f7",
            "#eab308",
            "#06b6d4",
        ],
    )

    fig.update_traces(
        mode="lines+markers",
        line=dict(width=4),
        marker=dict(size=5),
        opacity=0.92,
    )

    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Minuto do evento",
        yaxis_title="Preço médio em R$",
        legend_title_text="Combustível",
        hovermode="x unified",
        font=dict(color="#e5e7eb"),
        title=dict(
            font=dict(
                size=18,
                color="#f8fafc"
            )
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        tickformat="%H:%M<br>%d/%m"
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.info(
        "Visualização agregada por minuto com base nos eventos servidos pelo Redis."
    )


# =========================================================
# GRÁFICOS COMPLEMENTARES
# =========================================================

st.markdown("---")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 Distribuição de eventos por combustível")

    eventos_comb = (
        df.groupby("Combustível", as_index=False)
        .agg(
            eventos=("preco_novo", "count"),
            preco_medio=("preco_novo", "mean"),
        )
        .sort_values("eventos", ascending=False)
    )

    fig_donut = px.pie(
        eventos_comb,
        names="Combustível",
        values="eventos",
        hole=0.55,
        color_discrete_sequence=px.colors.sequential.Blues_r,
        title="Participação dos eventos recentes",
    )

    fig_donut.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="Combustível",
    )

    st.plotly_chart(fig_donut, use_container_width=True)

with col_chart2:
    st.subheader("🔥 Pressão de alta por combustível")

    alta_comb = (
        df.groupby("Combustível", as_index=False)
        .agg(
            variacao_media=("variacao_pct", "mean"),
            preco_medio=("preco_novo", "mean"),
            eventos=("preco_novo", "count"),
        )
        .sort_values("variacao_media", ascending=False)
    )

    fig_scatter = px.scatter(
        alta_comb,
        x="preco_medio",
        y="variacao_media",
        size="eventos",
        color="variacao_media",
        color_continuous_scale="Turbo",
        hover_name="Combustível",
        hover_data={
            "preco_medio": ":.2f",
            "variacao_media": ":.2f",
            "eventos": True,
        },
        title="Preço médio x variação média",
    )

    fig_scatter.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Preço médio em R$",
        yaxis_title="Variação média %",
        coloraxis_colorbar_title="Variação",
    )

    fig_scatter.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.14)",
        zeroline=False,
    )

    fig_scatter.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.14)",
        zeroline=False,
    )

    st.plotly_chart(fig_scatter, use_container_width=True)


# =========================================================
# CONSULTAS TEMPO REAL
# =========================================================

st.markdown("---")

st.subheader("⚡ Consultas que precisam ser servidas em tempo real")

consultas = [
    {
        "nome": "Ranking de menor preço",
        "desc": "Consulta imediata dos postos mais baratos por combustível.",
        "estrutura": "Redis ZSET",
        "criticidade": "Alta",
    },
    {
        "nome": "Menor preço por região",
        "desc": "Busca regional para tomada de decisão rápida.",
        "estrutura": "Redis ZSET + HASH",
        "criticidade": "Alta",
    },
    {
        "nome": "Postos próximos",
        "desc": "Consulta geográfica para localizar postos próximos.",
        "estrutura": "Redis GEO",
        "criticidade": "Média",
    },
    {
        "nome": "Últimas alterações",
        "desc": "Eventos recentes de mudança de preço.",
        "estrutura": "Redis LIST + TimeSeries",
        "criticidade": "Alta",
    },
]

cols = st.columns(4)

for i, item in enumerate(consultas):
    with cols[i]:
        cor = (
            "background:#fee2e2;color:#991b1b;"
            if item["criticidade"] == "Alta"
            else "background:#dbeafe;color:#1d4ed8;"
        )

        st.markdown(f"""
        <div class="rank-card" style="display:block !important; min-height:210px;">
            <div class="info-group">
                <div class="rank-nome">{item["nome"]}</div>
                <div class="rank-meta">{item["desc"]}</div>
                <div class="badge" style="{cor}">{item["criticidade"]}</div>
                <br>
                <div class="rank-price" style="font-size:1rem !important;">{item["estrutura"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# TABELA
# =========================================================

st.subheader("📋 Tabela executiva dos últimos eventos")

tabela = df[[
    "Combustível",
    "preco_anterior",
    "preco_novo",
    "variacao_pct",
    "fonte",
    "ocorrido_em",
]].copy()

tabela["Preço anterior"] = tabela["preco_anterior"].apply(moeda_brl)
tabela["Preço novo"] = tabela["preco_novo"].apply(moeda_brl)
tabela["Variação"] = tabela["variacao_pct"].apply(percentual)

tabela = tabela.rename(columns={
    "fonte": "Fonte",
    "ocorrido_em": "Data do evento",
})

tabela = tabela[[
    "Combustível",
    "Preço anterior",
    "Preço novo",
    "Variação",
    "Fonte",
    "Data do evento",
]]

st.dataframe(
    tabela.head(100),
    use_container_width=True,
    height=560,
    hide_index=True,
)