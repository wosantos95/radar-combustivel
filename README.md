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
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── README.md
│
├── src/
│   ├── app/
│   ├── database/
│   ├── generator/
│   ├── pipeline/
│   └── utils/
```

---

# ⚙️ Variáveis de Ambiente

```env
MONGO_URI=mongodb://mongodb:27017

DATABASE_NAME=radar_combustivel

REDIS_HOST=redis

REDIS_PORT=6379
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
