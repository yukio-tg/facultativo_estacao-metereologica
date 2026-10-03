import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


DB_PADRAO = Path(
    os.environ.get(
        "ESTACAO_DB_PATH",
        Path(__file__).with_name("estacao.db")
    )
)

CAMPOS_LEITURA = (
    "dht22_temp",
    "dht22_umi",
    "pressao_hpa",
    "mq135_valor",
    "mq135_status",
    "luminosidade_estado",
)


def _caminho(caminho=None):
    return str(Path(caminho) if caminho else DB_PADRAO)


def _conectar(caminho=None):
    conexao = sqlite3.connect(_caminho(caminho), timeout=5)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco(caminho=None):
    with closing(_conectar(caminho)) as conexao:
        with conexao:
            conexao.execute("PRAGMA journal_mode = WAL").fetchone()
            colunas = [
                linha[1]
                for linha in conexao.execute("PRAGMA table_info(leituras)")
            ]
            if colunas and "luminosidade_estado" not in colunas:
                conexao.execute(
                    "ALTER TABLE leituras RENAME TO leituras_modelo_anterior"
                )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    dht22_temp REAL NOT NULL,
                    dht22_umi REAL NOT NULL,
                    pressao_hpa REAL NOT NULL,
                    mq135_valor INTEGER NOT NULL,
                    mq135_status TEXT NOT NULL,
                    luminosidade_estado TEXT NOT NULL
                )
                """
            )
            conexao.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_leituras_timestamp
                ON leituras(timestamp)
                """
            )


def inserir_leitura(dados, caminho=None, timestamp=None):
    timestamp = timestamp or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    valores = [timestamp]
    valores.extend(dados[campo] for campo in CAMPOS_LEITURA)

    with closing(_conectar(caminho)) as conexao:
        with conexao:
            cursor = conexao.execute(
                """
                INSERT INTO leituras (
                    timestamp,
                    dht22_temp,
                    dht22_umi,
                    pressao_hpa,
                    mq135_valor,
                    mq135_status,
                    luminosidade_estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                valores
            )
            return cursor.lastrowid


def obter_ultima_leitura(caminho=None):
    with closing(_conectar(caminho)) as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM leituras
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    return dict(linha) if linha else None


def obter_historico(limite=100, caminho=None):
    limite = max(1, min(int(limite), 500))

    with closing(_conectar(caminho)) as conexao:
        linhas = conexao.execute(
            """
            SELECT *
            FROM (
                SELECT *
                FROM leituras
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (limite,)
        ).fetchall()

    return [dict(linha) for linha in linhas]
