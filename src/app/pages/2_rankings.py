import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from src.app.load_css import load_css
from src.database.redis_client import redis_client
from src.utils.formatters import (
    moeda_brl,
    nome_combustivel,
    badge_style,
    percentual,
    numero_br,
)
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
    "GNV",
]


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

            bairro = posto.get("bairro", "Não informado")
            cidade = posto.get("cidade", "Não informado")
            uf = posto.get("estado", "Não informado")

            registros.append({
                "Posto": posto.get("nome_fantasia", "Não informado"),
                "Bandeira": posto.get("bandeira", "Não informado"),
                "Bairro": bairro,
                "Cidade": cidade,
                "UF": uf,
                "Região": f"{bairro} • {cidade} - {uf}",
                "Combustível": nome_combustivel(item),
                "Combustível técnico": item,
                "Preço": float(preco),
            })

    return pd.DataFrame(registros)


df_base = carregar_ranking("TODOS")

if df_base.empty:
    st.warning("Ranking ainda não carregado no Redis.")
    st.stop()


cidades_disponiveis = sorted(df_base["Cidade"].dropna().unique().tolist())

cidade_selecionada = st.sidebar.selectbox(
    "Cidade",
    ["Todas"] + cidades_disponiveis,
    index=0
)

combustivel = st.sidebar.selectbox(
    "Produto",
    combustiveis,
    format_func=nome_combustivel
)


df = df_base.copy()

if cidade_selecionada != "Todas":
    df = df[df["Cidade"] == cidade_selecionada]

if combustivel != "TODOS":
    df = df[df["Combustível técnico"] == combustivel]

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()


df = df.sort_values("Preço", ascending=True).reset_index(drop=True)
df["Preço BRL"] = df["Preço"].apply(moeda_brl)

menor = df["Preço"].min()
media = df["Preço"].mean()
maior = df["Preço"].max()
economia = ((media - menor) / media) * 100 if media > 0 else 0

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

    if cidade_selecionada == "Todas":
        comparativo = (
            df.groupby("Combustível", as_index=False)
            .agg(
                menor_preco=("Preço", "min"),
                preco_medio=("Preço", "mean"),
                maior_preco=("Preço", "max"),
                postos=("Posto", "count")
            )
            .sort_values("preco_medio", ascending=False)
            .reset_index(drop=True)
        )

        comparativo["economia_potencial"] = (
            ((comparativo["preco_medio"] - comparativo["menor_preco"])
             / comparativo["preco_medio"]) * 100
        )

        comparativo["Preço médio"] = comparativo["preco_medio"].apply(moeda_brl)
        comparativo["Menor preço"] = comparativo["menor_preco"].apply(moeda_brl)
        comparativo["Maior preço"] = comparativo["maior_preco"].apply(moeda_brl)
        comparativo["Economia potencial"] = comparativo["economia_potencial"].apply(percentual)

        fig = px.scatter(
            comparativo,
            x="preco_medio",
            y="Combustível",
            size="postos",
            color="economia_potencial",
            text="Preço médio",
            color_continuous_scale=[
                [0.0, "#dbeafe"],
                [0.35, "#93c5fd"],
                [0.70, "#f97316"],
                [1.0, "#dc2626"],
            ],
            hover_data={
                "Menor preço": True,
                "Preço médio": True,
                "Maior preço": True,
                "Economia potencial": True,
                "postos": True,
                "preco_medio": False,
                "menor_preco": False,
                "maior_preco": False,
                "economia_potencial": False,
            },
            title="Preço médio, volume e oportunidade por combustível"
        )

        fig.update_traces(
            textposition="middle right",
            marker=dict(
                opacity=0.88,
                line=dict(width=0)
            )
        )

        fig.update_layout(
            xaxis_title="Preço médio em R$",
            yaxis_title="Combustível",
            coloraxis_colorbar_title="Economia potencial",
        )

        fig.update_yaxes(
            categoryorder="array",
            categoryarray=comparativo["Combustível"].tolist()
        )

        legenda_html = """
        <div class="insight-card" style="margin-top:10px;">
            <div class="insight-title">Como ler este gráfico</div>
            <p class="insight-text">
                <strong>Mais à direita:</strong> combustível com maior preço médio.
                <br>
                <strong>Bolha maior:</strong> maior quantidade de postos analisados.
                <br>
                <strong>Cor mais quente:</strong> maior economia potencial entre o menor preço e a média.
            </p>
        </div>
        """

    else:
        comparativo = (
            df.groupby(["Região", "Combustível"], as_index=False)
            .agg(
                preco_medio=("Preço", "mean"),
                menor_preco=("Preço", "min"),
                maior_preco=("Preço", "max"),
                postos=("Posto", "count")
            )
            .sort_values("preco_medio", ascending=False)
            .head(30)
            .reset_index(drop=True)
        )

        comparativo["Preço médio"] = comparativo["preco_medio"].apply(moeda_brl)
        comparativo["Menor preço"] = comparativo["menor_preco"].apply(moeda_brl)
        comparativo["Maior preço"] = comparativo["maior_preco"].apply(moeda_brl)

        fig = px.scatter(
            comparativo,
            x="Região",
            y="Combustível",
            size="postos",
            color="preco_medio",
            text="Preço médio",
            color_continuous_scale=[
                [0.0, "#dbeafe"],
                [0.35, "#93c5fd"],
                [0.70, "#f97316"],
                [1.0, "#dc2626"],
            ],
            hover_data={
                "Região": True,
                "Combustível": True,
                "Menor preço": True,
                "Preço médio": True,
                "Maior preço": True,
                "postos": True,
                "preco_medio": False,
                "menor_preco": False,
                "maior_preco": False,
            },
            title=f"Preço médio por região — {cidade_selecionada}"
        )

        fig.update_traces(
            textposition="top center",
            marker=dict(
                opacity=0.88,
                line=dict(width=0)
            )
        )

        fig.update_layout(
            xaxis_title="Regiões",
            yaxis_title="Combustível",
            coloraxis_colorbar_title="Preço médio",
        )

        legenda_html = """
        <div class="insight-card" style="margin-top:10px;">
            <div class="insight-title">Como ler este gráfico</div>
            <p class="insight-text">
                <strong>Eixo X:</strong> regiões da cidade selecionada.
                <br>
                <strong>Eixo Y:</strong> tipo de combustível.
                <br>
                <strong>Bolha maior:</strong> mais postos analisados naquela região.
                <br>
                <strong>Cor mais quente:</strong> preço médio mais alto.
            </p>
        </div>
        """

    fig.update_layout(
        template="plotly_dark",
        height=470,
        margin=dict(l=0, r=40, t=55, b=115),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        coloraxis_showscale=True
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.12)",
        zeroline=False,
        tickangle=-35
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.12)",
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(legenda_html, unsafe_allow_html=True)


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
            Ranking por combustível, cidade e região é servido pelo Redis para resposta imediata.
        </p>
    </div>
    """, unsafe_allow_html=True)


st.subheader("📋 Tabela executiva de preços")

tabela = df[[
    "Posto",
    "Bandeira",
    "Bairro",
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