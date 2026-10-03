import math


class GeoError(ValueError):
    """Coordenada inadequada para o cálculo geográfico."""


# Posição fixa informada para o local onde a estação está instalada.
# Não veio de um módulo GPS.
PONTO_ESTACAO = {
    "nome": "Estação meteorológica",
    "latitude": -23.564978600650882,
    "longitude": -46.65086234823989,
    "sensor_pressao": "BMP280",
    "aviso": (
        "Posição fixa informada para a instalação da estação. "
        "Não foi obtida por GPS. A pressão vem do BMP280."
    ),
}

RAIO_TERRA_M = 6_371_000
METROS_POR_GRAU_LATITUDE = 111_132.92
METROS_POR_GRAU_LONGITUDE_EQUADOR = 111_412.84


def _coordenada(valor, minimo, maximo, nome):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise GeoError(f"{nome} deve ser numérica")

    valor = float(valor)
    if not math.isfinite(valor) or not minimo <= valor <= maximo:
        raise GeoError(f"{nome} fora da faixa {minimo}..{maximo}")

    return valor


def calcular_distancia(latitude, longitude):
    """Calcula o vetor local e a distância até o ponto demonstrativo."""
    latitude = _coordenada(latitude, -90, 90, "latitude")
    longitude = _coordenada(longitude, -180, 180, "longitude")
    origem_lat = PONTO_ESTACAO["latitude"]
    origem_lon = PONTO_ESTACAO["longitude"]

    norte_m = (latitude - origem_lat) * METROS_POR_GRAU_LATITUDE
    metros_por_grau_lon = (
        METROS_POR_GRAU_LONGITUDE_EQUADOR
        * math.cos(math.radians(origem_lat))
    )
    leste_m = (longitude - origem_lon) * metros_por_grau_lon
    distancia_vetorial_m = math.hypot(leste_m, norte_m)

    delta_lat = math.radians(latitude - origem_lat)
    delta_lon = math.radians(longitude - origem_lon)
    lat1 = math.radians(origem_lat)
    lat2 = math.radians(latitude)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    distancia_geografica_m = (
        2 * RAIO_TERRA_M * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    )

    return {
        "ponto_estacao": PONTO_ESTACAO,
        "ponto_referencia": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "vetor_metros": {
            "leste": leste_m,
            "norte": norte_m,
        },
        "distancia_vetorial_m": distancia_vetorial_m,
        "distancia_geografica_m": distancia_geografica_m,
        "aviso": PONTO_ESTACAO["aviso"],
    }
