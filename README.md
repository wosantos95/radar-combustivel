# ⛽ Radar Combustível — Real-Time Data Platform

Plataforma analítica em tempo quase real desenvolvida para demonstrar uma arquitetura moderna de dados utilizando MongoDB como fonte operacional de eventos e Redis Stack como camada principal de serving.

O projeto simula o ecossistema da plataforma Radar Combustível, processando eventos contínuos de preços, buscas, localização de postos e demanda regional.

---

## 📌 Visão Geral

O Radar Combustível foi desenvolvido para responder, em tempo quase real, perguntas de negócio como:

- Quais postos possuem os menores preços por combustível?
- Quais combustíveis apresentam maior variação recente?
- Quais bairros concentram maior volume de buscas?
- Quais regiões possuem maior demanda?
- Quais consultas precisam ser servidas com baixa latência?
- Como transformar eventos operacionais em uma camada rápida de consulta?

A solução foi construída com foco em:

- Engenharia de Dados;
- Redis como serving layer;
- MongoDB como origem documental;
- pipeline contínuo MongoDB → Redis;
- dashboards executivos;
- visualização em tempo real;
- modelagem orientada a acesso.

---

## 🎯 Objetivo do Projeto

Construir um pipeline de dados capaz de:

- capturar dados operacionais no MongoDB;
- processar continuamente eventos de preço, busca e localização;
- transformar dados documentais em estruturas otimizadas no Redis;
- disponibilizar consultas rápidas para dashboards;
- demonstrar o uso correto de Redis como camada principal de leitura;
- apresentar visualizações executivas no Streamlit.

---

## 🏗️ Arquitetura da Solução

```text
Fake Data Generator
        ↓
MongoDB
        ↓
Pipeline MongoDB → Redis
        ↓
Redis Stack Serving Layer
        ↓
Dashboard Streamlit
```

---

## ⚡ Conceito Arquitetural

A arquitetura foi desenhada separando responsabilidades entre as camadas.

### MongoDB

O MongoDB atua como camada operacional e documental.

Responsabilidades:

- armazenar documentos brutos;
- registrar eventos de atualização de preço;
- armazenar buscas de usuários;
- armazenar avaliações e interações;
- armazenar dados de localização dos postos;
- funcionar como origem principal do pipeline.

### Pipeline MongoDB → Redis

O pipeline é executado continuamente.

Responsabilidades:

- ler novos eventos do MongoDB;
- transformar os dados conforme os padrões de consulta;
- atualizar rankings, métricas, listas e estruturas geográficas;
- popular o Redis com dados prontos para consumo;
- manter o status operacional do processamento.

### Redis Stack

O Redis atua como camada principal de serving.

Responsabilidades:

- servir dados para o dashboard;
- disponibilizar consultas de baixa latência;
- armazenar rankings;
- armazenar métricas executivas;
- manter eventos recentes;
- armazenar histórico temporal;
- permitir consultas geográficas.

### Streamlit

O Streamlit atua como camada de visualização.

Responsabilidades:

- consumir dados servidos pelo Redis;
- exibir KPIs;
- exibir rankings;
- exibir dados em tempo real;
- exibir mapas;
- demonstrar valor analítico do pipeline.

---

## 📂 Estrutura do Projeto

```text
radar-combustivel/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .dockerignore
├── .env.example
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

---

## 🧠 Modelagem Orientada a Acesso

O projeto foi modelado considerando os principais padrões de leitura da aplicação.

Cada estrutura Redis foi escolhida conforme a necessidade de consulta.

| Necessidade de negócio | Estrutura Redis | Chave |
|---|---|---|
| Cadastro resumido de postos | HASH | posto:<posto_id> |
| Métricas executivas | HASH | metricas:overview |
| Status do pipeline | HASH | pipeline:status |
| Ranking de menor preço | SORTED SET | ranking:<combustivel> |
| Volume de buscas por bairro | SORTED SET | buscas:bairros |
| Volume de buscas por combustível | SORTED SET | buscas:combustiveis |
| Volume de buscas por região | SORTED SET | buscas:regioes |
| Localização geográfica dos postos | GEO | postos_geo |
| Eventos recentes | LIST | eventos:recentes |
| Histórico temporal de preço | TimeSeries | historico:<posto_id>:<combustivel> |

---

## 🗄️ Base de Dados MongoDB

O MongoDB armazena a base operacional do projeto.

Coleções principais:

| Coleção | Descrição |
|---|---|
| postos | Cadastro dos postos de combustível |
| eventos_preco | Eventos de alteração de preço |
| buscas_usuarios | Buscas realizadas pelos usuários |
| avaliacoes_interacoes | Avaliações, favoritos, denúncias e interações |
| localizacoes_postos | Localizações geográficas dos postos |

O MongoDB representa a camada documental e transacional da aplicação.

---

## 🔄 Pipeline MongoDB → Redis

O arquivo responsável pelo pipeline é:

```text
src/pipeline/mongo_to_redis.py
```

O pipeline executa continuamente:

1. leitura incremental de eventos no MongoDB;
2. enriquecimento com dados do posto;
3. atualização do cadastro resumido no Redis;
4. atualização dos rankings por combustível;
5. atualização do Redis GEO;
6. atualização do histórico TimeSeries;
7. atualização da lista de eventos recentes;
8. atualização das métricas executivas;
9. atualização dos rankings de busca;
10. atualização do status do pipeline.

Fluxo simplificado:

```text
eventos_preco + postos + buscas_usuarios
        ↓
mongo_to_redis.py
        ↓
Redis Stack
        ↓
Streamlit
```

---

## ⚡ Estruturas Redis Utilizadas

### HASH

Cadastro resumido de posto:

```text
posto:<posto_id>
```

Exemplo de campos:

```text
nome_fantasia
bandeira
bairro
cidade
estado
combustivel
preco
```

Métricas executivas:

```text
metricas:overview
```

Exemplo de campos:

```text
total_postos
total_eventos
total_buscas
preco_medio
menor_preco
maior_preco
maior_alta
maior_queda
atualizado_em
```

Status do pipeline:

```text
pipeline:status
```

Exemplo de campos:

```text
status
ultimo_processamento
eventos_processados_ultimo_ciclo
batch_size
sleep_seconds
```

---

### SORTED SET

Ranking por combustível:

```text
ranking:GASOLINA_COMUM
ranking:GASOLINA_ADITIVADA
ranking:ETANOL
ranking:DIESEL_S10
ranking:DIESEL_COMUM
ranking:GNV
```

Buscas por bairro:

```text
buscas:bairros
```

Buscas por combustível:

```text
buscas:combustiveis
```

Buscas por região:

```text
buscas:regioes
```

---

### GEO

Coordenadas dos postos:

```text
postos_geo
```

Essa estrutura permite representar a localização geográfica dos postos e preparar consultas por proximidade.

---

### LIST

Eventos recentes:

```text
eventos:recentes
```

Essa lista alimenta a página de operações em tempo real.

---

### REDIS TIMESERIES

Histórico temporal de preços:

```text
historico:<posto_id>:<combustivel>
```

Exemplo:

```text
historico:6a04fc8925fe9ef109804b32:GNV
```

---

## 📊 Dashboards

O dashboard Streamlit é dividido em páginas executivas.

---

### 1. Executive Overview

Arquivo:

```text
src/app/pages/1_overview.py
```

Objetivo:

- apresentar visão consolidada;
- exibir KPIs executivos;
- mostrar variação média;
- destacar combustível em alta;
- apresentar insights gerenciais.

Fonte principal:

```text
Redis
```

Chaves utilizadas:

```text
metricas:overview
eventos:recentes
```

---

### 2. Market Intelligence

Arquivo:

```text
src/app/pages/2_rankings.py
```

Objetivo:

- apresentar menores preços;
- comparar preços por combustível;
- comparar preços por UF;
- mostrar top oportunidades;
- apoiar decisão de consumo e análise de mercado.

Fonte principal:

```text
Redis
```

Chaves utilizadas:

```text
ranking:<combustivel>
posto:<posto_id>
```

---

### 3. Real-Time Operations

Arquivo:

```text
src/app/pages/3_realtime.py
```

Objetivo:

- monitorar alterações recentes;
- visualizar preço médio por minuto;
- acompanhar maiores variações;
- mostrar distribuição dos eventos;
- demonstrar consultas críticas em tempo real.

Fonte principal:

```text
Redis
```

Chaves utilizadas:

```text
eventos:recentes
historico:<posto_id>:<combustivel>
```

---

### 4. Geo & Demand Intelligence

Arquivo:

```text
src/app/pages/4_geoanalytics.py
```

Objetivo:

- visualizar cobertura geográfica;
- analisar hotzones de busca;
- exibir bairros com maior demanda;
- demonstrar Redis GEO;
- demonstrar Redis Sorted Sets aplicados à demanda.

Fonte principal:

```text
Redis
```

Chaves utilizadas:

```text
postos_geo
posto:<posto_id>
buscas:bairros
buscas:combustiveis
buscas:regioes
metricas:overview
```

---

## ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` a partir do `.env.example`.

Arquivo recomendado:

```env
MONGO_URI=mongodb://mongodb:27017

DATABASE_NAME=radar_combustivel

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

PIPELINE_BATCH_SIZE=500
PIPELINE_SLEEP_SECONDS=2

FAKE_STREAM_INTERVAL=2
FAKE_INITIAL_LOAD=10000

PYTHONPATH=/app
```

Observação:

No Docker Compose, o dashboard roda internamente na porta 8501 e é exposto localmente na porta 8502.

Portanto, o acesso no navegador é:

```text
http://localhost:8502
```

---

## 📦 Dependências

Arquivo:

```text
requirements.txt
```

Dependências principais:

```text
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
```

---

## 🐳 Execução com Docker

A aplicação é totalmente containerizada com Docker Compose.

Serviços:

| Serviço | Função |
|---|---|
| mongodb | Banco documental |
| redis | Redis Stack e Redis Insight |
| fake-generator | Geração de massa e streaming |
| pipeline | Pipeline MongoDB → Redis |
| dashboard | Aplicação Streamlit |

---

## ▶️ Como Executar

Clone o repositório:

```bash
git clone https://github.com/wosantos95/radar-combustivel.git
```

Entre na pasta:

```bash
cd radar-combustivel
```

Crie o arquivo `.env`:

```bash
cp .env.example .env
```

Suba a aplicação:

```bash
docker compose up --build
```

---

## 🌐 Acessos

Dashboard Streamlit:

```text
http://localhost:8502
```

Redis Insight:

```text
http://localhost:8001
```

MongoDB:

```text
localhost:27017
```

Redis:

```text
localhost:6379
```

---

## 🧪 Validação do Redis

Entre no Redis CLI:

```bash
docker exec -it radar-redis redis-cli
```

Validar rankings:

```redis
KEYS ranking:*
```

Validar métricas executivas:

```redis
HGETALL metricas:overview
```

Validar eventos recentes:

```redis
LRANGE eventos:recentes 0 3
```

Validar buscas por combustível:

```redis
ZREVRANGE buscas:combustiveis 0 5 WITHSCORES
```

Validar buscas por bairro:

```redis
ZREVRANGE buscas:bairros 0 5 WITHSCORES
```

Validar dados geográficos:

```redis
ZRANGE postos_geo 0 5
```

Validar status do pipeline:

```redis
HGETALL pipeline:status
```

Validar histórico TimeSeries:

```redis
KEYS historico:*
```

---

## 🔎 Exemplo de Validação Esperada

### Rankings

```text
ranking:GASOLINA_COMUM
ranking:DIESEL_S10
ranking:GNV
ranking:DIESEL_COMUM
ranking:ETANOL
ranking:GASOLINA_ADITIVADA
```

### Métricas

```text
total_postos
total_eventos
total_buscas
preco_medio
menor_preco
maior_preco
atualizado_em
```

### Pipeline

```text
status: online
eventos_processados_ultimo_ciclo: 10
batch_size: 500
sleep_seconds: 2
```

---

## 📈 Fluxo de Dados Final

```text
Fake Generator
      ↓
MongoDB
      ↓
Pipeline contínuo
      ↓
Redis Serving Layer
      ↓
Streamlit Dashboard
```

---

## 🔥 Diferenciais Técnicos

- Pipeline contínuo MongoDB → Redis;
- Redis como camada principal de leitura;
- modelagem orientada a acesso;
- Redis Hash para dados resumidos;
- Redis Sorted Set para rankings;
- Redis GEO para localização;
- Redis TimeSeries para histórico;
- Redis List para eventos recentes;
- dashboard multipágina;
- atualização automática;
- arquitetura totalmente dockerizada;
- separação clara entre ingestão, processamento, serving e visualização.

---

## 📚 Conceitos Aplicados

- Engenharia de Dados;
- NoSQL;
- MongoDB;
- Redis Stack;
- Serving Layer;
- Real-Time Analytics;
- Event Streaming;
- GEO Analytics;
- TimeSeries;
- Cache de baixa latência;
- Data Visualization;
- Arquitetura distribuída;
- Docker Compose.

---

## ✅ Atendimento ao Escopo do Trabalho

| Requisito | Implementação |
|---|---|
| Base MongoDB | Coleções de postos, eventos, buscas, interações e localização |
| Pipeline MongoDB → Redis | Pipeline contínuo em Python |
| Redis como camada de serving | Dashboard consome Redis |
| Estruturas Redis adequadas | HASH, ZSET, GEO, LIST e TimeSeries |
| Visualização | Dashboard Streamlit |
| Documentação | README com arquitetura e execução |
| Carga de dados | Fake Generator com carga inicial e streaming |
| Execução | Docker Compose |

---

## 👨‍💻 Autor

Projeto acadêmico desenvolvido para estudos de Engenharia de Dados, Redis Stack, MongoDB, pipeline em tempo quase real e visualização analítica.

---

## 🚀 Resultado Final

A solução entrega uma arquitetura completa de dados em tempo quase real, contemplando:

- geração de eventos;
- armazenamento documental;
- pipeline de transformação;
- Redis como serving layer principal;
- dashboards executivos;
- análise geográfica;
- rankings;
- métricas em tempo real.

Com isso, o projeto demonstra de forma prática o uso do Redis como camada de consulta rápida sobre eventos originados no MongoDB.