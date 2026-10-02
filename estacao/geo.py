import math


class GeoError(ValueError):
    """Coordenada inadequada para o cálculo geográfico."""


# Coordenada usada somente para demonstrar o mapa e a Geometria Analítica.
# Ela não foi medida em campo e não representa a posição real da estação.
PONTO_DEMONSTRATIVO = {
    "nome": "Ponto demonstrativo",
    "latitude": -15.0,
    "longitude": -47.0,
    "sensor_pressao": "BMP180",
    "aviso": (
        "Coordenada ilustrativa. Não é a localização medida da estação. "
        "A pressão vem do BMP180; o enunciado acadêmico cita BMP280."
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
    origem_lat = PONTO_DEMONSTRATIVO["latitude"]
    origem_lon = PONTO_DEMONSTRATIVO["longitude"]

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
        "ponto_estacao": PONTO_DEMONSTRATIVO,
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
        "aviso": PONTO_DEMONSTRATIVO["aviso"],
    }
