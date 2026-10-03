import machine
import time
import network
import ssd1306
import dht
import json
import ubinascii
from umqtt.simple import MQTTClient


# ==============================================================================
# FUNÇÃO DE WI-FI
# ==============================================================================

def conectar_wifi(tentativas=20):
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if not wifi.isconnected():
        print("Conectando ao Wi-Fi...")
        # No Wokwi estes valores funcionam. Na placa física, troque pelo
        # nome e pela senha da rede real. Não grave a senha em um repositório.
        wifi.connect("PENSAO1", "21211413")

        for _ in range(tentativas):
            if wifi.isconnected():
                break
            time.sleep(1)
            print(".", end="")

    if not wifi.isconnected():
        print("\nWi-Fi indisponível. Nova tentativa será feita depois.")
        return False

    print("Wi-Fi conectado!")
    print("IP:", wifi.ifconfig()[0])
    return True


# ==============================================================================
# CONFIGURAÇÕES MQTT
# ==============================================================================

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORTA = 1883
MQTT_CLIENT_ID = b"esp32-estacao-" + ubinascii.hexlify(machine.unique_id())
MQTT_TOPICO = "universidade/sensores/estacao"


def conectar_mqtt():
    print("Conectando ao broker MQTT...")

    try:
        cliente = MQTTClient(
            MQTT_CLIENT_ID,
            MQTT_BROKER,
            port=MQTT_PORTA,
            keepalive=30
        )
        cliente.connect()
        print("MQTT conectado!")
        return cliente
    except Exception as erro:
        print("MQTT indisponível:", erro)
        return None


# ==============================================================================
# DRIVER DO BMP280
# O cálculo segue a compensação de temperatura e pressão da Bosch.
# Endereços comuns: 0x76 e 0x77. O identificador do chip é 0x58.
# ==============================================================================

def _inteiro_com_sinal(valor):
    return valor - 65536 if valor > 32767 else valor


class BMP280:
    def __init__(self, i2c, addr):
        self.i2c = i2c
        self.addr = addr
        identificador = i2c.readfrom_mem(addr, 0xD0, 1)[0]

        if identificador != 0x58:
            raise OSError("chip I2C não é BMP280")

        self._ler_calibracao()
        i2c.writeto_mem(addr, 0xF4, b"\x27")
        i2c.writeto_mem(addr, 0xF5, b"\xA0")
        self.t_fine = 0

    def _ler_calibracao(self):
        cal = self.i2c.readfrom_mem(self.addr, 0x88, 24)

        def u16(indice):
            return cal[indice] | (cal[indice + 1] << 8)

        def s16(indice):
            return _inteiro_com_sinal(u16(indice))

        self.dig_T1 = u16(0)
        self.dig_T2 = s16(2)
        self.dig_T3 = s16(4)
        self.dig_P1 = u16(6)
        self.dig_P2 = s16(8)
        self.dig_P3 = s16(10)
        self.dig_P4 = s16(12)
        self.dig_P5 = s16(14)
        self.dig_P6 = s16(16)
        self.dig_P7 = s16(18)
        self.dig_P8 = s16(20)
        self.dig_P9 = s16(22)

    def _compensar_temperatura(self, adc_t):
        var1 = (adc_t / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = adc_t / 131072.0 - self.dig_T1 / 8192.0
        var2 = var2 * var2 * self.dig_T3
        self.t_fine = var1 + var2

    def _compensar_pressao(self, adc_p):
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = (var2 / 4.0) + (self.dig_P4 * 65536.0)
        var1 = (
            self.dig_P3 * var1 * var1 / 524288.0
            + self.dig_P2 * var1
        ) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1

        if var1 == 0:
            return 0

        pressao = 1048576.0 - adc_p
        pressao = (pressao - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self.dig_P9 * pressao * pressao / 2147483648.0
        var2 = pressao * self.dig_P8 / 32768.0
        return pressao + (var1 + var2 + self.dig_P7) / 16.0

    def read_pressure(self):
        dados = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        adc_p = (dados[0] << 12) | (dados[1] << 4) | (dados[2] >> 4)
        adc_t = (dados[3] << 12) | (dados[4] << 4) | (dados[5] >> 4)
        self._compensar_temperatura(adc_t)
        return self._compensar_pressao(adc_p) / 100.0


# ==============================================================================
# CONEXÕES
# ==============================================================================

cliente_mqtt = None

if conectar_wifi():
    cliente_mqtt = conectar_mqtt()


# ==============================================================================
# CONFIGURAÇÃO DOS DISPOSITIVOS
# ==============================================================================

# 1. Barramento I2C
# O OLED é opcional. A falha dele não pode apagar o barramento do BMP280.
i2c = None
oled = None

try:
    i2c = machine.I2C(
        0,
        scl=machine.Pin(22),
        sda=machine.Pin(21),
        freq=100000
    )
    print(
        "Dispositivos I2C:",
        [hex(endereco) for endereco in i2c.scan()]
    )
except Exception as erro:
    print("Erro ao iniciar I2C:", erro)

if i2c is not None:
    try:
        oled = ssd1306.SSD1306_I2C(
            128,
            64,
            i2c
        )
    except Exception as erro:
        print("OLED ausente; a estação continua sem display:", erro)
        oled = None


# BMP280
bmp = None
bmp_disponivel = False

if i2c is not None:
    for endereco in (0x76, 0x77):
        try:
            bmp = BMP280(i2c, endereco)
            bmp_disponivel = True
            print("BMP280 encontrado em", hex(endereco))
            break
        except Exception as erro:
            print("BMP280 não respondeu em", hex(endereco), ":", erro)


# 2. Sensor DHT22
# GPIO 14

sensor_dht = dht.DHT22(
    machine.Pin(14)
)


# 3. Sensor MQ-135
# GPIO 34

mq135_adc = machine.ADC(
    machine.Pin(34)
)

mq135_adc.atten(
    machine.ADC.ATTN_11DB
)


# 4. Sensor digital de luminosidade
# GPIO 35, somente entrada. O módulo informa claro ou escuro, não percentual.
# Se o texto ficar invertido em relação ao ambiente, troque False por True.
LUZ_INVERTIDA = False

sensor_luz = machine.Pin(
    35,
    machine.Pin.IN
)


# ==============================================================================
# VARIÁVEIS
# ==============================================================================

ultimo_tempo_leitura = 0
tempo_alternar_tela = 0

# Envio MQTT a cada 5 segundos
ultimo_tempo_mqtt = 0
ultimo_tempo_reconexao_mqtt = 0

modo_tela = 0

temp = 0.0
umi = 0.0
pressao = 0.0

valor_mq135 = 0
estado_luz = "Escuro"


# ==============================================================================
# INFORMAÇÕES INICIAIS
# ==============================================================================

print("")
print("==========================================")
print(" ESTAÇÃO METEOROLÓGICA COMPLETA")
print("==========================================")
print("DHT22: GPIO 14")
print("MQ-135: GPIO 34 (ADC)")
print("Luz digital: GPIO 35 (claro ou escuro)")
print("BMP280: GPIOs 21 (SDA) e 22 (SCL)")
print("OLED: opcional, no mesmo I2C")
print("MQTT:", MQTT_BROKER)
print("Tópico:", MQTT_TOPICO)
print("==========================================")
print("")


# ==============================================================================
# LOOP PRINCIPAL
# ==============================================================================

while True:

    tempo_atual = time.ticks_ms()

    # Tenta recuperar Wi-Fi/MQTT sem impedir a leitura local dos sensores.
    if (
        cliente_mqtt is None
        and time.ticks_diff(
            tempo_atual,
            ultimo_tempo_reconexao_mqtt
        ) > 10000
    ):
        ultimo_tempo_reconexao_mqtt = tempo_atual

        if conectar_wifi(tentativas=5):
            cliente_mqtt = conectar_mqtt()

    # ==========================================================================
    # LEITURA DOS SENSORES A CADA 2 SEGUNDOS
    # ==========================================================================

    if time.ticks_diff(
        tempo_atual,
        ultimo_tempo_leitura
    ) > 2000:

        # ----------------------------------------------------------------------
        # DHT22
        # ----------------------------------------------------------------------

        try:
            sensor_dht.measure()

            temp = sensor_dht.temperature()
            umi = sensor_dht.humidity()

        except OSError:
            print("Erro na leitura do DHT22")


        # ----------------------------------------------------------------------
        # BMP280
        # ----------------------------------------------------------------------

        if bmp_disponivel:

            try:
                pressao = bmp.read_pressure()

            except Exception as erro:
                print("Erro na leitura do BMP280:", erro)


        # ----------------------------------------------------------------------
        # MQ-135
        # ----------------------------------------------------------------------

        valor_mq135 = mq135_adc.read()


        # ----------------------------------------------------------------------
        # Luminosidade digital
        # ----------------------------------------------------------------------

        nivel_luz = sensor_luz.value()

        if LUZ_INVERTIDA:
            nivel_luz = 0 if nivel_luz else 1

        estado_luz = "Claro" if nivel_luz else "Escuro"


        ultimo_tempo_leitura = tempo_atual


    # ==========================================================================
    # ENVIO DOS DADOS VIA MQTT A CADA 5 SEGUNDOS
    # ==========================================================================

    if time.ticks_diff(
        tempo_atual,
        ultimo_tempo_mqtt
    ) > 5000:

        # ----------------------------------------------------------------------
        # CLASSIFICAÇÃO DO AR
        # ----------------------------------------------------------------------

        if valor_mq135 < 1200:
            status_ar = "Ar Limpo"

        elif valor_mq135 < 2500:
            status_ar = "Ar Moderado"

        else:
            status_ar = "Ar Poluido"


        # ----------------------------------------------------------------------
        # DADOS QUE SERÃO ENVIADOS
        # ----------------------------------------------------------------------

        dados = {
            "dht22_temp": temp,
            "dht22_umi": umi,
            "pressao_hpa": pressao,
            "mq135_valor": valor_mq135,
            "mq135_status": status_ar,
            "luminosidade_estado": estado_luz
        }


        # ----------------------------------------------------------------------
        # CONVERTER DICIONÁRIO PARA JSON
        # ----------------------------------------------------------------------

        mensagem = json.dumps(dados)


        # ----------------------------------------------------------------------
        # PUBLICAR NO MQTT
        # ----------------------------------------------------------------------

        if not bmp_disponivel or pressao <= 0:
            print("BMP280 sem leitura válida: MQTT não enviado.")
            ultimo_tempo_mqtt = tempo_atual
        elif cliente_mqtt is None:
            print("MQTT offline: leitura não enviada.")
        else:
            try:
                cliente_mqtt.publish(
                    MQTT_TOPICO,
                    mensagem
                )

                print("")
                print("========== MQTT ==========")
                print("Dados enviados:")
                print(mensagem)
                print("==========================")
                print("")

            except Exception as erro:
                print("Erro ao enviar MQTT:", erro)

                try:
                    cliente_mqtt.disconnect()
                except Exception:
                    pass

                cliente_mqtt = None


        ultimo_tempo_mqtt = tempo_atual


    # ==========================================================================
    # ALTERNA AS TELAS DO OLED A CADA 3 SEGUNDOS
    # ==========================================================================

    if time.ticks_diff(
        tempo_atual,
        tempo_alternar_tela
    ) > 3000:

        modo_tela = (
            modo_tela + 1
        ) % 4

        tempo_alternar_tela = tempo_atual


    # ==========================================================================
    # ATUALIZAÇÃO DO DISPLAY OLED
    # ==========================================================================

    if oled is None:
        time.sleep_ms(100)
        continue

    oled.fill(0)


    # --------------------------------------------------------------------------
    # TELA 0 - DHT22
    # --------------------------------------------------------------------------

    if modo_tela == 0:

        oled.text(
            " ESTACAO CLIMA  ",
            0,
            0
        )

        oled.text(
            "----------------",
            0,
            10
        )

        oled.text(
            f"Temp:  {temp:.1f} C",
            0,
            32
        )

        oled.text(
            f"Umid:  {umi:.1f} %",
            0,
            48
        )


    # --------------------------------------------------------------------------
    # TELA 1 - BMP280
    # --------------------------------------------------------------------------

    elif modo_tela == 1:

        oled.text(
            "BAROMETRO BMP280",
            0,
            0
        )

        oled.text(
            "----------------",
            0,
            10
        )

        if bmp_disponivel:

            oled.text(
                "Pressao:",
                0,
                28
            )

            oled.text(
                f"{pressao:.1f} hPa",
                0,
                46
            )

        else:

            oled.text(
                "Sensor Offline",
                0,
                32
            )


    # --------------------------------------------------------------------------
    # TELA 2 - MQ-135
    # --------------------------------------------------------------------------

    elif modo_tela == 2:

        oled.text(
            " QUALIDADE DO AR",
            0,
            0
        )

        oled.text(
            "----------------",
            0,
            10
        )

        oled.text(
            f"ADC: {valor_mq135}",
            0,
            28
        )

        if valor_mq135 < 1200:
            status_ar = "Ar: Limpo"

        elif valor_mq135 < 2500:
            status_ar = "Ar: Moderado"

        else:
            status_ar = "Ar: Poluido"

        oled.text(
            status_ar,
            0,
            46
        )


    # --------------------------------------------------------------------------
    # TELA 3 - LUZ DIGITAL
    # --------------------------------------------------------------------------

    elif modo_tela == 3:

        oled.text(
            "  LUMINOSIDADE  ",
            0,
            0
        )

        oled.text(
            "----------------",
            0,
            10
        )

        oled.text(
            estado_luz,
            0,
            32
        )


    oled.show()

    time.sleep_ms(100)