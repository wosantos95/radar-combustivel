"""
Fake Data Generator — Radar Combustível
=======================================

Objetivo:
Gerar dados fake no MongoDB para alimentar o pipeline MongoDB → Redis.

Modo:
- Carga inicial com dados base
- Streaming contínuo a cada 2 segundos
"""

from __future__ import annotations

import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, List, Sequence

from bson import ObjectId
from faker import Faker
from pymongo import ASCENDING, GEOSPHERE
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from tqdm import tqdm

from src.database.mongo_client import get_database
from src.utils.logger import logger


db = get_database()


CIDADES_BASE = [
    {"cidade": "São Paulo", "estado": "SP", "lat": -23.5505, "lng": -46.6333},
    {"cidade": "Rio de Janeiro", "estado": "RJ", "lat": -22.9068, "lng": -43.1729},
    {"cidade": "Belo Horizonte", "estado": "MG", "lat": -19.9167, "lng": -43.9345},
    {"cidade": "Curitiba", "estado": "PR", "lat": -25.4284, "lng": -49.2733},
    {"cidade": "Porto Alegre", "estado": "RS", "lat": -30.0346, "lng": -51.2177},
    {"cidade": "Salvador", "estado": "BA", "lat": -12.9777, "lng": -38.5016},
    {"cidade": "Recife", "estado": "PE", "lat": -8.0476, "lng": -34.8770},
    {"cidade": "Fortaleza", "estado": "CE", "lat": -3.7319, "lng": -38.5267},
    {"cidade": "Brasília", "estado": "DF", "lat": -15.7939, "lng": -47.8828},
    {"cidade": "Goiânia", "estado": "GO", "lat": -16.6869, "lng": -49.2648},
]

COMBUSTIVEIS = (
    "GASOLINA_COMUM",
    "GASOLINA_ADITIVADA",
    "ETANOL",
    "DIESEL_S10",
    "DIESEL_COMUM",
    "GNV",
)

BANDEIRAS = (
    "Ipiranga",
    "Shell",
    "BR",
    "Raízen",
    "Ale",
    "Petrobras",
    "Rede Independente",
)

TIPOS_INTERACAO = (
    "avaliacao",
    "favorito",
    "compartilhamento",
    "denuncia",
    "check_in",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def chunked(seq: Sequence[Any], size: int) -> Iterable[List[Any]]:
    for i in range(0, len(seq), size):
        yield list(seq[i:i + size])


def make_fake_geo(base: dict[str, Any]) -> dict[str, Any]:
    lat = base["lat"] + random.uniform(-0.06, 0.06)
    lng = base["lng"] + random.uniform(-0.06, 0.06)

    return {
        "type": "Point",
        "coordinates": [
            round(lng, 6),
            round(lat, 6),
        ],
    }


def cnpj_like() -> str:
    digits = "".join(str(random.randint(0, 9)) for _ in range(14))

    return (
        f"{digits[:2]}."
        f"{digits[2:5]}."
        f"{digits[5:8]}/"
        f"{digits[8:12]}-"
        f"{digits[12:14]}"
    )


def doc_posto(fake: Faker, oid: ObjectId) -> dict[str, Any]:
    base = random.choice(CIDADES_BASE)

    bairro = (
        fake.bairro()
        if hasattr(fake, "bairro")
        else f"Bairro {random.randint(1, 50)}"
    )

    return {
        "_id": oid,
        "cnpj": cnpj_like(),
        "nome_fantasia": f"Posto {fake.company()}",
        "bandeira": random.choice(BANDEIRAS),
        "endereco": {
            "logradouro": fake.street_name(),
            "numero": str(random.randint(1, 9999)),
            "bairro": bairro,
            "cep": fake.postcode(),
            "cidade": base["cidade"],
            "estado": base["estado"],
        },
        "telefone": fake.phone_number()[:20],
        "ativo": random.random() > 0.03,
        "location": make_fake_geo(base),
        "created_at": fake.date_time_between(
            start_date="-5y",
            end_date="now",
            tzinfo=timezone.utc,
        ),
        "updated_at": utc_now(),
    }


def doc_evento_preco(fake: Faker, posto_ids: Sequence[ObjectId]) -> dict[str, Any]:
    preco_novo = round(random.uniform(4.5, 8.9), 3)
    preco_ant = round(max(3.0, preco_novo + random.uniform(-0.8, 0.8)), 3)

    return {
        "_id": ObjectId(),
        "posto_id": random.choice(posto_ids),
        "combustivel": random.choice(COMBUSTIVEIS),
        "preco_anterior": preco_ant,
        "preco_novo": preco_novo,
        "variacao_pct": round(((preco_novo - preco_ant) / preco_ant) * 100, 4),
        "unidade": "BRL_L",
        "fonte": random.choice(("app_usuario", "api_anp", "operador_posto", "crawler")),
        "ocorrido_em": utc_now(),
        "revisado": random.random() > 0.15,
    }


def doc_busca(fake: Faker) -> dict[str, Any]:
    base = random.choice(CIDADES_BASE)

    bairro = (
        fake.bairro()
        if hasattr(fake, "bairro")
        else f"Bairro {random.randint(1, 50)}"
    )

    return {
        "_id": ObjectId(),
        "usuario_id": fake.uuid4(),
        "session_id": fake.uuid4(),
        "tipo_combustivel": random.choice(COMBUSTIVEIS),
        "cidade": base["cidade"],
        "estado": base["estado"],
        "bairro": bairro,
        "raio_km": random.choice((1, 2, 3, 5, 10, 15)),
        "filtros": {
            "apenas_abertos": random.random() > 0.5,
            "ordenacao": random.choice(("preco", "distancia", "avaliacao")),
        },
        "geo_centro": make_fake_geo(base),
        "consultado_em": utc_now(),
        "resultado_count": random.randint(0, 120),
        "latencia_ms": random.randint(8, 450),
    }


def doc_avaliacao_interacao(
    fake: Faker,
    posto_ids: Sequence[ObjectId],
) -> dict[str, Any]:
    tipo = random.choice(TIPOS_INTERACAO)

    return {
        "_id": ObjectId(),
        "posto_id": random.choice(posto_ids),
        "usuario_id": fake.uuid4(),
        "tipo": tipo,
        "nota": random.randint(1, 5) if tipo == "avaliacao" else None,
        "comentario": (
            fake.text(max_nb_chars=180)
            if tipo == "avaliacao" and random.random() > 0.4
            else None
        ),
        "created_at": utc_now(),
        "util_count": random.randint(0, 42),
    }


def doc_localizacao_posto(
    fake: Faker,
    posto_id: ObjectId,
) -> dict[str, Any]:
    base = random.choice(CIDADES_BASE)

    bairro = (
        fake.bairro()
        if hasattr(fake, "bairro")
        else f"Bairro {random.randint(1, 50)}"
    )

    return {
        "_id": ObjectId(),
        "posto_id": posto_id,
        "municipio": base["cidade"],
        "bairro": bairro,
        "uf": base["estado"],
        "codigo_ibge": str(random.randint(1100000, 5300000)),
        "geo": make_fake_geo(base),
        "atualizado_em": utc_now() - timedelta(days=random.randint(0, 30)),
    }


def ensure_indexes() -> None:
    logger.info("Criando índices MongoDB")

    db.postos.create_index([("location", GEOSPHERE)])
    db.postos.create_index([
        ("endereco.estado", ASCENDING),
        ("endereco.cidade", ASCENDING),
    ])

    db.eventos_preco.create_index([
        ("posto_id", ASCENDING),
        ("ocorrido_em", ASCENDING),
    ])

    db.eventos_preco.create_index([
        ("combustivel", ASCENDING),
        ("ocorrido_em", ASCENDING),
    ])

    db.buscas_usuarios.create_index([("consultado_em", ASCENDING)])
    db.buscas_usuarios.create_index([
        ("estado", ASCENDING),
        ("cidade", ASCENDING),
        ("bairro", ASCENDING),
    ])

    db.localizacoes_postos.create_index([("geo", GEOSPHERE)])


def insert_batches(
    collection: Collection,
    docs: List[dict[str, Any]],
    batch_size: int,
) -> int:
    total = 0
    start = time.time()

    batches = list(chunked(docs, batch_size))

    print(f"\n🚀 Inserindo em {collection.name}")

    for batch in tqdm(batches, desc=f"{collection.name}", unit="batch"):
        collection.insert_many(batch, ordered=False)
        total += len(batch)

    end = time.time()

    logger.info(f"{collection.name}: {total} documentos inseridos")

    print(
        f"✅ {collection.name}: "
        f"{total} documentos inseridos "
        f"({round(end - start, 2)}s)"
    )

    return total


def main() -> None:
    logger.info("Iniciando geração de dados fake")

    try:
        print("\n" + "=" * 70)
        print("⛽ RADAR COMBUSTÍVEL — FAKE DATA GENERATOR")
        print("=" * 70)
        print("Modo: carga inicial + streaming a cada 2 segundos\n")

        seed = 42
        batch_size = 5000
        n_target = 10000

        random.seed(seed)
        Faker.seed(seed)

        fake = Faker("pt_BR")

        logger.info("Limpando coleções")

        for name in (
            "postos",
            "eventos_preco",
            "buscas_usuarios",
            "avaliacoes_interacoes",
            "localizacoes_postos",
        ):
            db[name].drop()

        posto_ids = [ObjectId() for _ in range(n_target)]

        insert_batches(
            db.postos,
            [doc_posto(fake, oid) for oid in posto_ids],
            batch_size,
        )

        insert_batches(
            db.localizacoes_postos,
            [doc_localizacao_posto(fake, pid) for pid in posto_ids],
            batch_size,
        )

        insert_batches(
            db.eventos_preco,
            [doc_evento_preco(fake, posto_ids) for _ in range(n_target)],
            batch_size,
        )

        insert_batches(
            db.buscas_usuarios,
            [doc_busca(fake) for _ in range(n_target)],
            batch_size,
        )

        insert_batches(
            db.avaliacoes_interacoes,
            [doc_avaliacao_interacao(fake, posto_ids) for _ in range(n_target)],
            batch_size,
        )

        ensure_indexes()

        print("\n🔥 CARGA INICIAL CONCLUÍDA")
        print("🚀 Streaming iniciado")
        print("⏱️ Novos dados serão gerados a cada 2 segundos.\n")

        while True:
            try:
                novos_eventos = [
                    doc_evento_preco(fake, posto_ids)
                    for _ in range(random.randint(2, 6))
                ]

                novas_buscas = [
                    doc_busca(fake)
                    for _ in range(random.randint(1, 4))
                ]

                novas_interacoes = [
                    doc_avaliacao_interacao(fake, posto_ids)
                    for _ in range(random.randint(1, 3))
                ]

                db.eventos_preco.insert_many(novos_eventos, ordered=False)
                db.buscas_usuarios.insert_many(novas_buscas, ordered=False)
                db.avaliacoes_interacoes.insert_many(novas_interacoes, ordered=False)

                logger.info(
                    "Streaming: "
                    f"{len(novos_eventos)} eventos_preco | "
                    f"{len(novas_buscas)} buscas_usuarios | "
                    f"{len(novas_interacoes)} avaliacoes_interacoes"
                )

                print(
                    "✅ Stream ativo → "
                    f"{len(novos_eventos)} preços | "
                    f"{len(novas_buscas)} buscas | "
                    f"{len(novas_interacoes)} interações"
                )

                time.sleep(2)

            except Exception as stream_error:
                logger.error(f"Erro no streaming: {stream_error}")
                print(f"❌ Erro stream: {stream_error}")
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 Stream interrompido pelo usuário.")
        sys.exit(0)

    except PyMongoError as e:
        logger.error(f"Erro MongoDB: {e}")
        print(f"❌ Erro MongoDB: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()