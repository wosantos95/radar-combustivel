# ⛽ Radar Combustível — Plataforma Analítica em Tempo Real

## Plataforma completa de engenharia de dados e analytics em tempo real

MongoDB • Redis Stack • Streamlit • Docker • Plotly • GEO Analytics • TimeSeries • Serving Layer

---

# 📌 Visão Geral

O Radar Combustível é uma plataforma analítica desenvolvida para simular um ecossistema real de monitoramento de preços de combustíveis em tempo real.

O projeto demonstra conceitos modernos de:

- Engenharia de Dados
- Processamento Streaming
- Serving Layer
- GEO Analytics
- Dashboards Executivos
- Redis como camada de baixa latência
- Pipeline MongoDB → Redis
- Visualização analítica em tempo real

---

# 🏗️ Arquitetura da Solução

```text
Fake Data Generator
        ↓
MongoDB (Raw Layer)
        ↓
Pipeline Streaming Mongo → Redis
        ↓
Redis Stack (Serving Layer)
        ↓
Dashboard Streamlit
```

---

# 📂 Estrutura Final do Projeto

```text
radar-combustivel/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .dockerignore
├── .env
├── README.md
│
├── logs/
│
└── src/
    │
    ├── app/
    │   │
    │   ├── app.py
    │   ├── load_css.py
    │   ├── components.py
    │   │
    │   ├── pages/
    │   │   │
    │   │   ├── 1_overview.py
    │   │   ├── 2_rankings.py
    │   │   ├── 3_realtime.py
    │   │   └── 4_geoanalytics.py
    │   │
    │   └── styles/
    │       │
    │       └── theme.css
    │
    ├── database/
    │   │
    │   ├── mongo_client.py
    │   └── redis_client.py
    │
    ├── generator/
    │   │
    │   └── fake_generator.py
    │
    ├── pipeline/
    │   │
    │   └── mongo_to_redis.py
    │
    └── utils/
        │
        ├── logger.py
        └── formatters.py
```

# ⚙️ Variáveis de Ambiente

```env
# =========================================================
# MONGODB
# =========================================================

MONGO_URI=mongodb://radar-mongodb:27017

DATABASE_NAME=radar_combustivel


# =========================================================
# REDIS
# =========================================================

REDIS_HOST=radar-redis

REDIS_PORT=6379

REDIS_DB=0


# =========================================================
# STREAMLIT
# =========================================================

STREAMLIT_SERVER_PORT=8501

STREAMLIT_SERVER_ADDRESS=0.0.0.0


# =========================================================
# PIPELINE
# =========================================================

PIPELINE_BATCH_SIZE=500

PIPELINE_SLEEP_SECONDS=2


# =========================================================
# FAKE DATA GENERATOR
# =========================================================

FAKE_STREAM_INTERVAL=2

FAKE_INITIAL_LOAD=10000


# =========================================================
# PYTHON
# =========================================================

PYTHONPATH=/app

```

---

# 🚀 Executar Projeto

```bash
docker compose up --build
```

---

# 🌐 Acessos

Dashboard:

```text
http://localhost:8501
```

Redis Insight:

```text
http://localhost:8001
```

---

# 📌 Diferenciais Técnicos

✅ Arquitetura distribuída

✅ Streaming contínuo

✅ Pipeline Mongo → Redis

✅ Serving Layer

✅ Redis GEO

✅ Redis TimeSeries

✅ Dashboard executivo

✅ Real-Time Analytics

✅ Dockerização completa

---

# 👨‍💻 Objetivo Acadêmico

Projeto desenvolvido com foco em:

- Engenharia de Dados
- Sistemas Distribuídos
- Real-Time Processing
- NoSQL
- Serving Layer
- Data Analytics
- Visualização Executiva
