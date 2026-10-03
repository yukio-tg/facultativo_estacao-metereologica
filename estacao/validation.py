import json
import math
from collections.abc import Mapping


class ValidationError(ValueError):
    """Payload MQTT inválido para a estação."""


CAMPOS_ESPERADOS = {
    "dht22_temp",
    "dht22_umi",
    "pressao_hpa",
    "mq135_valor",
    "mq135_status",
    "luminosidade_estado",
}

ESTADOS_LUZ = {
    "Claro",
    "Escuro",
}

STATUS_AR = {
    "Ar Limpo",
    "Ar Moderado",
    "Ar Poluido",
}


def _numero(dados, campo, minimo, maximo):
    valor = dados[campo]

    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(f"{campo} deve ser numérico")

    valor = float(valor)
    if not math.isfinite(valor):
        raise ValidationError(f"{campo} deve ser finito")

    if not minimo <= valor <= maximo:
        raise ValidationError(
            f"{campo} fora da faixa {minimo}..{maximo}"
        )

    return valor


def _adc(dados, campo):
    valor = dados[campo]

    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValidationError(f"{campo} deve ser inteiro")

    if not 0 <= valor <= 4095:
        raise ValidationError(f"{campo} fora da faixa 0..4095")

    return valor


def _status_esperado(valor_mq135):
    if valor_mq135 < 1200:
        return "Ar Limpo"
    if valor_mq135 < 2500:
        return "Ar Moderado"
    return "Ar Poluido"


def validar_payload(payload):
    """Converte JSON e devolve uma leitura normalizada ou lança ValidationError."""
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError as erro:
            raise ValidationError("payload não está em UTF-8") from erro

    if isinstance(payload, str):
        try:
            dados = json.loads(payload)
        except (json.JSONDecodeError, ValueError) as erro:
            raise ValidationError("payload não contém JSON válido") from erro
    elif isinstance(payload, Mapping):
        dados = dict(payload)
    else:
        raise ValidationError("payload deve ser JSON ou objeto")

    if not isinstance(dados, dict):
        raise ValidationError("JSON deve representar um objeto")

    campos_recebidos = set(dados)
    ausentes = CAMPOS_ESPERADOS - campos_recebidos
    extras = campos_recebidos - CAMPOS_ESPERADOS

    if ausentes:
        raise ValidationError(
            "campos ausentes: " + ", ".join(sorted(ausentes))
        )
    if extras:
        raise ValidationError(
            "campos desconhecidos: " + ", ".join(sorted(extras))
        )

    temperatura = _numero(dados, "dht22_temp", -40, 80)
    umidade = _numero(dados, "dht22_umi", 0, 100)
    pressao = _numero(dados, "pressao_hpa", 300, 1100)
    mq135 = _adc(dados, "mq135_valor")
    estado_luz = dados["luminosidade_estado"]
    status = dados["mq135_status"]

    if status not in STATUS_AR:
        raise ValidationError("mq135_status não reconhecido")

    if status != _status_esperado(mq135):
        raise ValidationError("mq135_status não corresponde ao valor ADC")

    if estado_luz not in ESTADOS_LUZ:
        raise ValidationError("luminosidade_estado deve ser Claro ou Escuro")

    return {
        "dht22_temp": temperatura,
        "dht22_umi": umidade,
        "pressao_hpa": pressao,
        "mq135_valor": mq135,
        "mq135_status": status,
        "luminosidade_estado": estado_luz,
    }
