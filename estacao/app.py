import logging
import os

from flask import Flask, jsonify, render_template, request

from database import (
    DB_PADRAO,
    inicializar_banco,
    obter_historico,
    obter_ultima_leitura,
)
from geo import PONTO_DEMONSTRATIVO, GeoError, calcular_distancia
from mqtt_service import MQTTService


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DATABASE"] = str(db_path or DB_PADRAO)
    inicializar_banco(app.config["DATABASE"])

    @app.route("/")
    def dashboard():
        return render_template("index.html")

    @app.route("/api/dados")
    def dados():
        leitura = obter_ultima_leitura(app.config["DATABASE"])

        if leitura is None:
            return jsonify({
                "erro": "Nenhuma leitura válida recebida ainda"
            }), 404

        return jsonify(leitura)

    @app.route("/api/historico")
    def historico():
        limite_texto = request.args.get("limite", "100")

        try:
            limite = int(limite_texto)
        except ValueError:
            return jsonify({
                "erro": "O parâmetro limite deve ser inteiro"
            }), 400

        if not 1 <= limite <= 500:
            return jsonify({
                "erro": "O parâmetro limite deve estar entre 1 e 500"
            }), 400

        leituras = obter_historico(
            limite,
            app.config["DATABASE"]
        )
        return jsonify({
            "quantidade": len(leituras),
            "leituras": leituras,
        })

    @app.route("/api/estacao")
    def estacao():
        return jsonify(PONTO_DEMONSTRATIVO)

    @app.route("/api/distancia")
    def distancia():
        try:
            latitude = float(request.args["latitude"])
            longitude = float(request.args["longitude"])
        except (KeyError, TypeError, ValueError):
            return jsonify({
                "erro": "Informe latitude e longitude numéricas"
            }), 400

        try:
            return jsonify(calcular_distancia(latitude, longitude))
        except GeoError as erro:
            return jsonify({"erro": str(erro)}), 400

    return app


app = create_app()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    servico_mqtt = MQTTService(db_path=app.config["DATABASE"])
    servico_mqtt.iniciar()

    try:
        app.run(
            host=os.environ.get("FLASK_HOST", "0.0.0.0"),
            port=int(os.environ.get("FLASK_PORT", "5000")),
            debug=os.environ.get("FLASK_DEBUG") == "1",
            use_reloader=False
        )
    finally:
        servico_mqtt.parar()