import logging
import uuid

import paho.mqtt.client as mqtt

from database import inserir_leitura
from validation import ValidationError, validar_payload


MQTT_BROKER = "broker.hivemq.com"
MQTT_PORTA = 1883
MQTT_TOPICO = "universidade/sensores/estacao"

logger = logging.getLogger(__name__)


class MQTTService:
    def __init__(
        self,
        db_path=None,
        broker=MQTT_BROKER,
        porta=MQTT_PORTA,
        topico=MQTT_TOPICO
    ):
        self.db_path = db_path
        self.broker = broker
        self.porta = porta
        self.topico = topico
        client_id = f"backend-estacao-{uuid.uuid4().hex[:10]}"

        self.cliente = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv311
        )
        self.cliente.on_connect = self._ao_conectar
        self.cliente.on_disconnect = self._ao_desconectar
        self.cliente.on_message = self._ao_receber
        self.cliente.reconnect_delay_set(min_delay=1, max_delay=30)
        self._iniciado = False

    def _ao_conectar(
        self,
        cliente,
        _userdata,
        _flags,
        reason_code,
        _properties
    ):
        if reason_code == 0:
            cliente.subscribe(self.topico, qos=0)
            logger.info(
                "MQTT conectado; tópico assinado: %s",
                self.topico
            )
        else:
            logger.error(
                "Broker MQTT recusou a conexão: %s",
                reason_code
            )

    def _ao_desconectar(
        self,
        _cliente,
        _userdata,
        _disconnect_flags,
        reason_code,
        _properties
    ):
        if reason_code != 0:
            logger.warning(
                "MQTT desconectado inesperadamente: %s; reconectando",
                reason_code
            )

    def _ao_receber(self, _cliente, _userdata, mensagem):
        try:
            dados = validar_payload(mensagem.payload)
            leitura_id = inserir_leitura(dados, self.db_path)
            logger.info(
                "Leitura %s armazenada a partir de %s",
                leitura_id,
                mensagem.topic
            )
        except ValidationError as erro:
            logger.warning(
                "Mensagem MQTT rejeitada em %s: %s",
                mensagem.topic,
                erro
            )
        except Exception:
            logger.exception("Falha ao processar mensagem MQTT")

    def iniciar(self):
        if self._iniciado:
            return

        logger.info(
            "Conectando ao MQTT em %s:%s",
            self.broker,
            self.porta
        )
        self.cliente.connect_async(
            self.broker,
            self.porta,
            keepalive=30
        )
        self.cliente.loop_start()
        self._iniciado = True

    def parar(self):
        if not self._iniciado:
            return

        self.cliente.disconnect()
        self.cliente.loop_stop()
        self._iniciado = False
