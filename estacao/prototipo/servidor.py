# Servidor da estacao - versao prototipo
# Num unico arquivo: recebe por MQTT, confere, salva no SQLite e serve o painel.

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template

BROKER = "broker.hivemq.com"
TOPICO = "universidade/sensores/estacao"
BANCO = Path(__file__).with_name("estacao.db")
ESTACAO = {"latitude": -23.564978600650882, "longitude": -46.65086234823989}

CAMPOS = (
    "dht22_temp",
    "dht22_umi",
    "pressao_hpa",
    "mq135_valor",
    "mq135_status",
    "luminosidade_estado",
)
LIMITES = {
    "dht22_temp": (-40, 80),
    "dht22_umi": (0, 100),
    "pressao_hpa": (300, 1100),
    "mq135_valor": (0, 4095),
}


# ---------- Banco de dados ----------
def executar(sql, valores=()):
    banco = sqlite3.connect(BANCO)
    banco.row_factory = sqlite3.Row
    try:
        linhas = banco.execute(sql, valores).fetchall()
        banco.commit()
        return [dict(linha) for linha in linhas]
    finally:
        banco.close()


def criar_banco():
    executar("""
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
    """)


# ---------- Conferencia dos dados ----------
def status_do_ar(valor):
    if valor < 1200:
        return "Ar Limpo"
    if valor < 2500:
        return "Ar Moderado"
    return "Ar Poluido"


def validar(dados):
    # Retorna None se estiver tudo certo, ou um texto explicando o problema.
    if not isinstance(dados, dict) or set(dados) != set(CAMPOS):
        return "campos diferentes do esperado"
    for campo, (minimo, maximo) in LIMITES.items():
        valor = dados[campo]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            return f"{campo} nao e numero"
        if not minimo <= valor <= maximo:
            return f"{campo} fora da faixa {minimo} a {maximo}"
    if not isinstance(dados["mq135_valor"], int):
        return "mq135_valor deve ser inteiro"
    if dados["mq135_status"] != status_do_ar(dados["mq135_valor"]):
        return "mq135_status nao combina com mq135_valor"
    if dados["luminosidade_estado"] not in ("Claro", "Escuro"):
        return "luminosidade_estado deve ser Claro ou Escuro"
    return None


# ---------- MQTT ----------
def ao_conectar(cliente, userdata, flags, codigo, propriedades):
    print("MQTT:", codigo, "- ouvindo", TOPICO)
    cliente.subscribe(TOPICO)


def ao_receber(cliente, userdata, mensagem):
    try:
        dados = json.loads(mensagem.payload)
    except ValueError:
        print("Rejeitado: mensagem nao e JSON")
        return

    erro = validar(dados)
    if erro:
        print("Rejeitado:", erro)
        return

    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        executar(
            "INSERT INTO leituras (timestamp, " + ", ".join(CAMPOS) + ")"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            [agora] + [dados[campo] for campo in CAMPOS],
        )
        print("Salvo:", dados)
    except sqlite3.Error as erro_banco:
        print("Erro ao salvar no banco:", erro_banco)


# ---------- Site e API ----------
app = Flask(__name__)


@app.route("/")
def painel():
    return render_template("painel.html", estacao=ESTACAO)


@app.route("/api/dados")
def ultima_leitura():
    linhas = executar("SELECT * FROM leituras ORDER BY id DESC LIMIT 1")
    if not linhas:
        return jsonify({"erro": "Nenhuma leitura recebida ainda"}), 404
    return jsonify(linhas[0])


@app.route("/api/historico")
def historico():
    linhas = executar("SELECT * FROM leituras ORDER BY id DESC LIMIT 40")
    return jsonify(linhas[::-1])


criar_banco()

if __name__ == "__main__":
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber
    cliente.connect_async(BROKER, 1883, keepalive=30)
    cliente.loop_start()  # roda o MQTT em segundo plano e reconecta sozinho
    app.run(host="0.0.0.0", port=5000)
