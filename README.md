# ⛽ Radar Combustível — Real-Time Data Platform

Plataforma analítica em tempo quase real desenvolvida para demonstrar arquitetura moderna de dados utilizando:

- MongoDB
- Redis Stack
- Streamlit
- Docker
- Pipeline Mongo → Redis
- GEO Analytics
- Redis TimeSeries
- Real-Time Serving Layer

O projeto simula o ecossistema da plataforma Radar Combustível, processando eventos contínuos de preços, buscas, localização e demanda regional.

---

# 🎯 Objetivo do Projeto

Construir um pipeline de dados orientado a eventos capaz de:

- capturar eventos operacionais no MongoDB;
- processar continuamente alterações de preço e buscas;
- atualizar estruturas otimizadas no Redis;
- servir dashboards analíticos em tempo real;
- demonstrar Redis como camada principal de serving.

---

# 🏗️ Arquitetura da Solução

Fake Generator
       ↓
MongoDB
       ↓
Pipeline Mongo → Redis
       ↓
Redis Serving Layer
       ↓
Dashboard Streamlit

---

# ⚡ Conceito Arquitetural

O MongoDB atua como:

- camada transacional;
- armazenamento documental;
- origem dos eventos.

O Redis atua como:

- camada de serving;
- consultas em baixa latência;
- rankings;
- realtime analytics;
- GEO queries;
- cache operacional.

O Streamlit consome os dados diretamente do Redis.

---

# 📂 Estrutura do Projeto

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
├── src/
│   │
│   ├── app/
│   │   │
│   │   ├── app.py
│   │   ├── load_css.py
│   │   ├── components.py
│   │   │
│   │   ├── pages/
│   │   │   │
│   │   │   ├── 1_overview.py
│   │   │   ├── 2_rankings.py
│   │   │   ├── 3_realtime.py
│   │   │   └── 4_geoanalytics.py
│   │   │
│   │   └── styles/
│   │       │
│   │       └── theme.css
│   │
│   ├── database/
│   │   │
│   │   ├── mongo_client.py
│   │   └── redis_client.py
│   │
│   ├── generator/
│   │   │
│   │   └── fake_generator.py
│   │
│   ├── pipeline/
│   │   │
│   │   └── mongo_to_redis.py
│   │
│   └── utils/
│       │
│       ├── logger.py
│       └── formatters.py

---

# 🧠 Modelagem Orientada a Acesso

O projeto foi modelado considerando os padrões de leitura do negócio.

Cada estrutura Redis foi escolhida conforme o tipo de consulta:

| Necessidade | Estrutura Redis |
|---|---|
| Cadastro rápido de postos | HASH |
| Ranking de preços | SORTED SET |
| GEO localização | GEO |
| Eventos recentes | LIST |
| Histórico temporal | Redis TimeSeries |
| KPIs executivos | HASH |
| Hotzones de busca | SORTED SET |

---

# ⚙️ Variáveis de Ambiente

## .env

MONGO_URI=mongodb://mongodb:27017

DATABASE_NAME=radar_combustivel

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

STREAMLIT_SERVER_PORT=8501

PIPELINE_BATCH_SIZE=500
PIPELINE_SLEEP_SECONDS=2

FAKE_STREAM_INTERVAL=2
FAKE_INITIAL_LOAD=10000

---

# 📦 Dependências

## requirements.txt

streamlit==1.45.1
plotly==6.0.1
pandas==2.2.3
numpy==2.2.5
redis==6.0.0
pymongo==4.12.0
faker==37.1.0
streamlit-autorefresh==1.0.1
python-dotenv==1.1.0
tqdm==4.67.1

---

# 🐳 Docker Compose

## Serviços da Plataforma

- MongoDB
- Redis Stack
- Fake Generator
- Pipeline Mongo → Redis
- Dashboard Streamlit

---

# ▶️ Executar Projeto

## Build completo

docker compose up --build

---

# 🌐 Acessos

## Dashboard Streamlit

http://localhost:8502

## Redis Insight

http://localhost:8001

---

# 🔄 Pipeline Mongo → Redis

O pipeline executa continuamente:

1. leitura de eventos do MongoDB;
2. transformação dos dados;
3. atualização das estruturas Redis;
4. serving em tempo real para o dashboard.

---

# ⚡ Estruturas Redis Utilizadas

## HASH

### Cadastro resumido de postos

posto:<posto_id>

### Métricas executivas

metricas:overview

### Status do pipeline

pipeline:status

---

## SORTED SET

### Ranking por combustível

ranking:<combustivel>

### Volume de buscas por bairro

buscas:bairros

### Volume de buscas por combustível

buscas:combustiveis

### Volume de buscas por região

buscas:regioes

---

## GEO

### Coordenadas dos postos

postos_geo

---

## LIST

### Eventos recentes

eventos:recentes

---

## REDIS TIMESERIES

### Histórico temporal de preços

historico:<posto_id>:<combustivel>

---

# 📊 Dashboards

## 1. Executive Overview

Visão executiva da plataforma:

- KPIs;
- volatilidade;
- combustível em alta;
- insights;
- comparativos.

Todos os dados servidos pelo Redis.

---

## 2. Market Intelligence

Dashboard analítico de preços:

- menor preço;
- maior preço;
- oportunidades;
- ranking por combustível;
- comparação regional;
- análise de mercado.

Servido por Redis Sorted Sets.

---

## 3. Real-Time Operations

Monitoramento operacional em tempo real:

- eventos recentes;
- alterações de preço;
- séries temporais;
- pressão inflacionária;
- realtime analytics.

Servido por Redis LIST + TimeSeries.

---

## 4. Geo & Demand Intelligence

Dashboard geográfico:

- cobertura nacional;
- hotzones;
- volume de buscas;
- distribuição regional;
- GEO analytics.

Servido por Redis GEO + ZSET.

---

# 📈 Fluxo de Dados

MongoDB
   ↓
Pipeline contínuo
   ↓
Redis Serving Layer
   ↓
Streamlit

---

# 🔥 Diferenciais Técnicos

✅ Pipeline orientado a eventos

✅ Redis como serving layer principal

✅ Dashboard realtime

✅ GEO analytics

✅ Redis TimeSeries

✅ Rankings de preço

✅ Hotzones de demanda

✅ Arquitetura distribuída

✅ Projeto totalmente dockerizado

✅ Atualização contínua

✅ Estrutura corporativa

---

# 🧪 Validação do Redis

## Verificar rankings

ZRANGE ranking:GASOLINA_COMUM 0 5 WITHSCORES

## Verificar eventos realtime

LRANGE eventos:recentes 0 5

## Verificar métricas executivas

HGETALL metricas:overview

## Verificar buscas por bairro

ZREVRANGE buscas:bairros 0 5 WITHSCORES

## Verificar GEO

ZRANGE postos_geo 0 5

## Verificar pipeline

HGETALL pipeline:status

---

# 📚 Tecnologias Utilizadas

- Python
- MongoDB
- Redis Stack
- Redis GEO
- Redis TimeSeries
- Streamlit
- Plotly
- Docker
- Pandas
- Faker

---

# 👨‍💻 Objetivos Acadêmicos

Projeto desenvolvido com foco em:

- Engenharia de Dados
- Sistemas Distribuídos
- Serving Layer
- Real-Time Analytics
- Modelagem orientada a acesso
- Redis aplicado a analytics
- Pipeline de dados
- Data Visualization

---

# 🚀 Resultado Final

A solução entrega uma arquitetura completa de:

- ingestão;
- transformação;
- serving;
- visualização;
- analytics em tempo quase real.

Com Redis atuando como principal camada de consulta e baixa latência.