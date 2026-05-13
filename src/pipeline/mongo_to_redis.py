import json
import os
import time
from datetime import datetime

from src.database.mongo_client import get_database
from src.database.redis_client import redis_client
from src.utils.logger import logger


db = get_database()

eventos = db["eventos_preco"]
postos = db["postos"]
buscas = db["buscas_usuarios"]

PIPELINE_BATCH_SIZE = int(os.getenv("PIPELINE_BATCH_SIZE", 500))
PIPELINE_SLEEP_SECONDS = int(os.getenv("PIPELINE_SLEEP_SECONDS", 2))

ultimo_id = None

logger.info("Pipeline contínuo MongoDB → Redis iniciado")


def upsert_timeseries(key: str, valor: float):
    try:
        redis_client.execute_command(
            "TS.CREATE",
            key,
            "DUPLICATE_POLICY",
            "last"
        )
    except Exception:
        pass

    try:
        redis_client.execute_command(
            "TS.ADD",
            key,
            "*",
            valor,
            "ON_DUPLICATE",
            "last"
        )
    except Exception as e:
        logger.warning(f"Erro ao inserir TimeSeries {key}: {e}")


def atualizar_metricas_overview():
    total_postos = postos.count_documents({})
    total_eventos = eventos.count_documents({})
    total_buscas = buscas.count_documents({})

    resultado = list(eventos.aggregate([
        {
            "$group": {
                "_id": None,
                "preco_medio": {"$avg": "$preco_novo"},
                "menor_preco": {"$min": "$preco_novo"},
                "maior_preco": {"$max": "$preco_novo"},
                "maior_alta": {"$max": "$variacao_pct"},
                "maior_queda": {"$min": "$variacao_pct"},
            }
        }
    ]))

    dados = resultado[0] if resultado else {}

    redis_client.hset(
        "metricas:overview",
        mapping={
            "total_postos": total_postos,
            "total_eventos": total_eventos,
            "total_buscas": total_buscas,
            "preco_medio": float(dados.get("preco_medio") or 0),
            "menor_preco": float(dados.get("menor_preco") or 0),
            "maior_preco": float(dados.get("maior_preco") or 0),
            "maior_alta": float(dados.get("maior_alta") or 0),
            "maior_queda": float(dados.get("maior_queda") or 0),
            "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
    )


def atualizar_buscas_redis():
    redis_client.delete(
        "buscas:bairros",
        "buscas:combustiveis",
        "buscas:regioes"
    )

    for busca in buscas.find():
        bairro = busca.get("bairro") or busca.get("cidade", "Não informado")
        cidade = busca.get("cidade", "Não informado")
        estado = busca.get("estado", "NI")
        combustivel = busca.get("tipo_combustivel", "Não informado")
        volume = int(busca.get("resultado_count", 0) or 0)

        chave_bairro = f"{bairro} • {cidade} - {estado}"
        chave_regiao = f"{cidade} - {estado}"

        redis_client.zincrby("buscas:bairros", volume, chave_bairro)
        redis_client.zincrby("buscas:combustiveis", volume, combustivel)
        redis_client.zincrby("buscas:regioes", volume, chave_regiao)


def publicar_evento_recente(evento, posto, posto_id: str):
    payload = {
        "posto_id": posto_id,
        "nome_fantasia": posto.get("nome_fantasia", ""),
        "bandeira": posto.get("bandeira", ""),
        "cidade": posto.get("endereco", {}).get("cidade", ""),
        "estado": posto.get("endereco", {}).get("estado", ""),
        "bairro": posto.get("endereco", {}).get("bairro", ""),
        "combustivel": evento.get("combustivel", ""),
        "preco_anterior": float(evento.get("preco_anterior", 0) or 0),
        "preco_novo": float(evento.get("preco_novo", 0) or 0),
        "variacao_pct": float(evento.get("variacao_pct", 0) or 0),
        "fonte": evento.get("fonte", ""),
        "ocorrido_em": str(evento.get("ocorrido_em", "")),
    }

    redis_client.lpush(
        "eventos:recentes",
        json.dumps(payload, ensure_ascii=False)
    )

    redis_client.ltrim("eventos:recentes", 0, 499)


def processar_evento(evento):
    posto = postos.find_one({
        "_id": evento["posto_id"]
    })

    if not posto:
        return False

    posto_id = str(posto["_id"])
    combustivel = evento.get("combustivel", "")
    preco_novo = float(evento.get("preco_novo", 0) or 0)

    redis_client.hset(
        f"posto:{posto_id}",
        mapping={
            "nome_fantasia": posto.get("nome_fantasia", ""),
            "bandeira": posto.get("bandeira", ""),
            "bairro": posto.get("endereco", {}).get("bairro", ""),
            "cidade": posto.get("endereco", {}).get("cidade", ""),
            "estado": posto.get("endereco", {}).get("estado", ""),
            "combustivel": combustivel,
            "preco": preco_novo,
        }
    )

    redis_client.zadd(
        f"ranking:{combustivel}",
        {
            posto_id: preco_novo
        }
    )

    geo = posto.get("location", {}).get("coordinates")

    if geo and len(geo) == 2:
        redis_client.geoadd(
            "postos_geo",
            (
                float(geo[0]),
                float(geo[1]),
                posto_id
            )
        )

    upsert_timeseries(
        f"historico:{posto_id}:{combustivel}",
        preco_novo
    )

    publicar_evento_recente(evento, posto, posto_id)

    return True


while True:
    try:
        query = {}

        if ultimo_id:
            query["_id"] = {
                "$gt": ultimo_id
            }

        novos_eventos = list(
            eventos.find(query)
            .sort("_id", 1)
            .limit(PIPELINE_BATCH_SIZE)
        )

        processados = 0

        if novos_eventos:
            for evento in novos_eventos:
                if processar_evento(evento):
                    processados += 1

                ultimo_id = evento["_id"]

            logger.info(f"{processados} eventos processados no Redis")

        else:
            logger.info("Nenhum evento novo encontrado")

        atualizar_metricas_overview()
        atualizar_buscas_redis()

        redis_client.hset(
            "pipeline:status",
            mapping={
                "status": "online",
                "ultimo_processamento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "eventos_processados_ultimo_ciclo": processados,
                "batch_size": PIPELINE_BATCH_SIZE,
                "sleep_seconds": PIPELINE_SLEEP_SECONDS,
            }
        )

        time.sleep(PIPELINE_SLEEP_SECONDS)

    except Exception as e:
        logger.error(f"Erro no pipeline MongoDB → Redis: {e}")
        time.sleep(PIPELINE_SLEEP_SECONDS)