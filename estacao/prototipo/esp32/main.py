# Estacao meteorologica - versao prototipo
# Le os sensores e envia um JSON por MQTT a cada 5 segundos.

import json
import time

import dht
import machine
import network
import ubinascii
from umqtt.simple import MQTTClient

# ---------- Configuracao (troque pelos dados da sua rede) ----------
WIFI_NOME = ""
WIFI_SENHA = ""
BROKER = "broker.hivemq.com"
TOPICO = "universidade/sensores/estacao"
CLIENTE_ID = b"esp32-estacao-" + ubinascii.hexlify(machine.unique_id())
LUZ_INVERTIDA = False  # mude para True se o painel mostrar claro/escuro trocado

# ---------- Sensores ----------
dht22 = dht.DHT22(machine.Pin(14))
mq135 = machine.ADC(machine.Pin(34))
mq135.atten(machine.ADC.ATTN_11DB)  # permite ler de 0 a ~3,3 V
luz = machine.Pin(35, machine.Pin.IN)
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=100000)


def iniciar_bmp280():
    # Procura o BMP280 nos dois enderecos possiveis e le a calibracao de fabrica.
    for endereco in (0x76, 0x77):
        try:
            if i2c.readfrom_mem(endereco, 0xD0, 1)[0] != 0x58:
                continue
            i2c.writeto_mem(endereco, 0xF4, b"\x27")  # modo normal
            i2c.writeto_mem(endereco, 0xF5, b"\xA0")  # intervalo de 1 s
            c = i2c.readfrom_mem(endereco, 0x88, 24)
            cal = [c[i] | (c[i + 1] << 8) for i in range(0, 24, 2)]
            for i in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11):  # valores com sinal
                if cal[i] > 32767:
                    cal[i] -= 65536
            return endereco, cal
        except OSError:
            pass
    return None, None


def ler_pressao(endereco, cal):
    # Formula do fabricante (Bosch). Retorna a pressao em hPa.
    d = i2c.readfrom_mem(endereco, 0xF7, 6)
    adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
    adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
    t1, t2, t3, p1, p2, p3, p4, p5, p6, p7, p8, p9 = cal

    v1 = (adc_t / 16384 - t1 / 1024) * t2
    v2 = (adc_t / 131072 - t1 / 8192) ** 2 * t3
    t_fine = v1 + v2

    v1 = t_fine / 2 - 64000
    v2 = v1 * v1 * p6 / 32768 + v1 * p5 * 2
    v2 = v2 / 4 + p4 * 65536
    v1 = (p3 * v1 * v1 / 524288 + p2 * v1) / 524288
    v1 = (1 + v1 / 32768) * p1
    if v1 == 0:
        return 0
    p = (1048576 - adc_p - v2 / 4096) * 6250 / v1
    p = p + (p9 * p * p / 2147483648 + p * p8 / 32768 + p7) / 16
    return p / 100


def status_do_ar(valor):
    if valor < 1200:
        return "Ar Limpo"
    if valor < 2500:
        return "Ar Moderado"
    return "Ar Poluido"


def conectar():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    if not wifi.isconnected():
        print("Conectando ao Wi-Fi...")
        wifi.connect(WIFI_NOME, WIFI_SENHA)
        for _ in range(20):
            if wifi.isconnected():
                break
            time.sleep(1)
    if not wifi.isconnected():
        print("Sem Wi-Fi")
        return None
    try:
        cliente = MQTTClient(CLIENTE_ID, BROKER, port=1883, keepalive=30)
        cliente.connect()
        print("MQTT conectado")
        return cliente
    except Exception as erro:
        print("Sem MQTT:", erro)
        return None


# ---------- Programa principal ----------
endereco_bmp, cal_bmp = iniciar_bmp280()
print("BMP280:", hex(endereco_bmp) if endereco_bmp else "nao encontrado")
cliente = conectar()

while True:
    time.sleep(5)

    if endereco_bmp is None:
        endereco_bmp, cal_bmp = iniciar_bmp280()
        if endereco_bmp is None:
            print("BMP280 nao encontrado. Confira os fios SDA/SCL.")
            continue

    try:
        dht22.measure()
        temperatura = dht22.temperature()
        umidade = dht22.humidity()
        pressao = ler_pressao(endereco_bmp, cal_bmp)
    except OSError as erro:
        print("Falha ao ler sensor:", erro)
        continue

    ar = mq135.read()
    claro = luz.value() == 1
    if LUZ_INVERTIDA:
        claro = not claro

    mensagem = json.dumps({
        "dht22_temp": temperatura,
        "dht22_umi": umidade,
        "pressao_hpa": round(pressao, 2),
        "mq135_valor": ar,
        "mq135_status": status_do_ar(ar),
        "luminosidade_estado": "Claro" if claro else "Escuro",
    })
    print(mensagem)

    if cliente is None:
        cliente = conectar()
    if cliente is None:
        continue
    try:
        cliente.publish(TOPICO, mensagem)
    except Exception as erro:
        print("Falha no envio, reconectando:", erro)
        cliente = None
