import streamlit as st

from src.app.load_css import load_css
from src.database.mongo_client import get_database
from src.database.redis_client import redis_client

st.set_page_config(
    page_title="Radar Combustível",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

db = get_database()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("""
<div class="sidebar-brand">
    ⚡ Radar Combustível
</div>

<div class="sidebar-sub">
Data-Driven Fuel Intelligence Platform
</div>
""", unsafe_allow_html=True)

# =========================================================
# DADOS EXECUTIVOS
# =========================================================

total_postos = db.postos.count_documents({})
total_eventos = db.eventos_preco.count_documents({})
total_buscas = db.buscas_usuarios.count_documents({})
total_avaliacoes = db.avaliacoes_interacoes.count_documents({})

# =========================================================
# HERO
# =========================================================

st.markdown("""
<div class="hero-container">

<div class="hero-badge">
REAL-TIME DATA PLATFORM
</div>

<h1 class="hero-title">
⛽ Radar Combustível
</h1>

<p class="hero-subtitle">
Plataforma executiva para monitoramento de preços,
demanda regional, inteligência geográfica
e consultas servidas em tempo quase real via Redis.
</p>

</div>
""", unsafe_allow_html=True)

# =========================================================
# KPI GRID
# =========================================================

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="home-kpi-card">
        <div class="home-kpi-label">Postos monitorados</div>
        <div class="home-kpi-value">{total_postos:,}</div>
        <div class="home-kpi-footer">Base operacional</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="home-kpi-card">
        <div class="home-kpi-label">Eventos de preço</div>
        <div class="home-kpi-value">{total_eventos:,}</div>
        <div class="home-kpi-footer">Pipeline ativo</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="home-kpi-card">
        <div class="home-kpi-label">Buscas processadas</div>
        <div class="home-kpi-value">{total_buscas:,}</div>
        <div class="home-kpi-footer">Demand intelligence</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="home-kpi-card">
        <div class="home-kpi-label">Interações</div>
        <div class="home-kpi-value">{total_avaliacoes:,}</div>
        <div class="home-kpi-footer">Engajamento</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# STORYTELLING
# =========================================================

col1, col2 = st.columns([1.2, 1])

with col1:

    st.markdown("""
    <div class="story-card">

    <h3>📌 Objetivo do projeto</h3>

    <p>
    O Radar Combustível transforma eventos operacionais
    em uma Serving Layer de baixa latência utilizando Redis.
    </p>

    <p>
    A plataforma responde perguntas críticas de negócio:
    </p>

    <ul>
        <li>Quais postos possuem menor preço por região</li>
        <li>Quais combustíveis estão em alta</li>
        <li>Quais regiões concentram maior demanda</li>
        <li>Quais consultas precisam de resposta em tempo real</li>
        <li>Quais postos apresentam maior volatilidade</li>
    </ul>

    </div>
    """, unsafe_allow_html=True)

with col2:

    st.markdown("""
    <div class="story-card">

    <h3>⚡ Arquitetura Data Platform</h3>

    <div class="architecture-flow">
    Fake Generator
    <span>→</span>
    MongoDB
    <span>→</span>
    Pipeline Python
    <span>→</span>
    Redis
    <span>→</span>
    Streamlit Analytics
    </div>

    <br>

    <h3>🚀 Tecnologias utilizadas</h3>

    <ul>
        <li>MongoDB</li>
        <li>Redis Stack</li>
        <li>Python</li>
        <li>Docker</li>
        <li>Plotly</li>
        <li>Streamlit</li>
    </ul>

    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# EXECUTIVE STATUS
# =========================================================

st.markdown("""
<div class="status-card">

<div class="status-dot"></div>

<div>
<strong>Pipeline operacional</strong><br>
Dados sendo gerados continuamente e servidos em tempo quase real.
</div>

</div>
""", unsafe_allow_html=True)