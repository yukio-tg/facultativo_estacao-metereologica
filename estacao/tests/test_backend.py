import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from database import (
    inicializar_banco,
    inserir_leitura,
    obter_historico,
    obter_ultima_leitura,
)
from geo import PONTO_ESTACAO, calcular_distancia
from validation import ValidationError, validar_payload


def payload_valido(**alteracoes):
    dados = {
        "dht22_temp": 24.5,
        "dht22_umi": 61.0,
        "pressao_hpa": 1012.4,
        "mq135_valor": 843,
        "mq135_status": "Ar Limpo",
        "luminosidade_estado": "Claro",
    }
    dados.update(alteracoes)
    return dados


class TestValidacao(unittest.TestCase):
    def test_aceita_payload_valido_em_json(self):
        dados = validar_payload(json.dumps(payload_valido()))
        self.assertEqual(dados["mq135_valor"], 843)
        self.assertAlmostEqual(dados["dht22_temp"], 24.5)

    def test_rejeita_json_malformado(self):
        with self.assertRaisesRegex(ValidationError, "JSON válido"):
            validar_payload("{incompleto")

    def test_rejeita_campo_ausente(self):
        dados = payload_valido()
        del dados["pressao_hpa"]

        with self.assertRaisesRegex(ValidationError, "campos ausentes"):
            validar_payload(dados)

    def test_rejeita_valor_fora_da_faixa(self):
        with self.assertRaisesRegex(ValidationError, "dht22_umi"):
            validar_payload(payload_valido(dht22_umi=120))

    def test_rejeita_booleano_como_numero(self):
        with self.assertRaisesRegex(ValidationError, "dht22_temp"):
            validar_payload(payload_valido(dht22_temp=True))

    def test_rejeita_status_incompativel_com_adc(self):
        with self.assertRaisesRegex(ValidationError, "não corresponde"):
            validar_payload(
                payload_valido(mq135_status="Ar Poluido")
            )

    def test_rejeita_estado_de_luz_desconhecido(self):
        with self.assertRaisesRegex(ValidationError, "luminosidade_estado"):
            validar_payload(payload_valido(luminosidade_estado="lux"))

    def test_rejeita_precipitacao_no_payload(self):
        with self.assertRaisesRegex(ValidationError, "desconhecidos"):
            validar_payload(payload_valido(chuva_mm=1.25))


class TestBancoEApi(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.db_path = Path(self.diretorio.name) / "teste.db"
        inicializar_banco(self.db_path)

    def tearDown(self):
        self.diretorio.cleanup()

    def test_insere_e_consulta_leituras(self):
        primeira = validar_payload(payload_valido(dht22_temp=20))
        segunda = validar_payload(payload_valido(dht22_temp=25))

        inserir_leitura(
            primeira,
            self.db_path,
            "2026-10-02T18:00:00Z"
        )
        inserir_leitura(
            segunda,
            self.db_path,
            "2026-10-02T18:00:05Z"
        )

        ultima = obter_ultima_leitura(self.db_path)
        historico = obter_historico(10, self.db_path)

        self.assertEqual(ultima["dht22_temp"], 25)
        self.assertEqual(len(historico), 2)
        self.assertEqual(
            historico[0]["timestamp"],
            "2026-10-02T18:00:00Z"
        )

    def test_api_sem_dados_retorna_404(self):
        app = create_app(self.db_path)
        resposta = app.test_client().get("/api/dados")

        self.assertEqual(resposta.status_code, 404)
        self.assertIn("erro", resposta.get_json())

    def test_api_expoe_ultima_leitura_e_historico(self):
        leitura = validar_payload(payload_valido())
        inserir_leitura(
            leitura,
            self.db_path,
            "2026-10-02T18:00:00Z"
        )
        app = create_app(self.db_path)
        cliente = app.test_client()

        ultima = cliente.get("/api/dados")
        historico = cliente.get("/api/historico?limite=10")

        self.assertEqual(ultima.status_code, 200)
        self.assertEqual(ultima.get_json()["mq135_valor"], 843)
        self.assertEqual(historico.status_code, 200)
        self.assertEqual(historico.get_json()["quantidade"], 1)

    def test_api_valida_limite_do_historico(self):
        app = create_app(self.db_path)
        cliente = app.test_client()

        self.assertEqual(
            cliente.get("/api/historico?limite=texto").status_code,
            400
        )
        self.assertEqual(
            cliente.get("/api/historico?limite=501").status_code,
            400
        )


class TestGeometria(unittest.TestCase):
    def test_distancia_no_proprio_ponto_e_zero(self):
        resultado = calcular_distancia(
            PONTO_ESTACAO["latitude"],
            PONTO_ESTACAO["longitude"]
        )

        self.assertEqual(resultado["distancia_vetorial_m"], 0)
        self.assertAlmostEqual(resultado["distancia_geografica_m"], 0)

    def test_deslocamento_para_norte(self):
        resultado = calcular_distancia(
            PONTO_ESTACAO["latitude"] + 1,
            PONTO_ESTACAO["longitude"]
        )

        self.assertGreater(resultado["vetor_metros"]["norte"], 100_000)
        self.assertAlmostEqual(resultado["vetor_metros"]["leste"], 0)
        self.assertAlmostEqual(
            resultado["distancia_vetorial_m"],
            resultado["distancia_geografica_m"],
            delta=3_000
        )

    def test_api_rejeita_coordenada_invalida(self):
        with tempfile.TemporaryDirectory() as diretorio:
            app = create_app(Path(diretorio) / "teste.db")
            cliente = app.test_client()

            self.assertEqual(cliente.get("/api/estacao").status_code, 200)
            self.assertIn(
                "Posição fixa",
                cliente.get("/api/estacao").get_json()["aviso"]
            )
            self.assertEqual(
                cliente.get(
                    "/api/distancia?latitude=95&longitude=0"
                ).status_code,
                400
            )
            self.assertEqual(cliente.get("/api/distancia").status_code, 400)


if __name__ == "__main__":
    unittest.main()
