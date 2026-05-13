import time

from src.database.mongo_client import get_database
from src.database.redis_client import redis_client
from src.utils.logger import logger

db = get_database()

eventos = db["eventos_preco"]
postos = db["postos"]

logger.info("Pipeline contínuo Mongo → Redis iniciado")

ultimo_id = None


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


while True:

    query = {}

    if ultimo_id:
        query["_id"] = {
            "$gt": ultimo_id
        }

    novos_eventos = list(
        eventos.find(query)
        .sort("_id", 1)
        .limit(500)
    )

    if not novos_eventos:
        logger.info("Nenhum evento novo encontrado")
        time.sleep(5)
        continue

    processados = 0

    for evento in novos_eventos:

        posto = postos.find_one({
            "_id": evento["posto_id"]
        })

        if not posto:
            ultimo_id = evento["_id"]
            continue

        posto_id = str(posto["_id"])

        redis_client.hset(
            f"posto:{posto_id}",
            mapping={
                "nome_fantasia": posto.get("nome_fantasia", ""),
                "bandeira": posto.get("bandeira", ""),
                "bairro": posto.get("endereco", {}).get("bairro", ""),
                "cidade": posto.get("endereco", {}).get("cidade", ""),
                "estado": posto.get("endereco", {}).get("estado", ""),
                "combustivel": evento.get("combustivel", ""),
                "preco": float(evento.get("preco_novo", 0)),
            }
        )

        redis_client.zadd(
            f"ranking:{evento['combustivel']}",
            {
                posto_id: float(evento["preco_novo"])
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
            f"historico:{posto_id}:{evento['combustivel']}",
            float(evento["preco_novo"])
        )

        ultimo_id = evento["_id"]
        processados += 1

    logger.info(
        f"{processados} eventos processados no Redis"
    )

    time.sleep(5)