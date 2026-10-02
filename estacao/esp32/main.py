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
        wifi.connect("Wokwi-GUEST", "")

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
# DRIVER SIMPLIFICADO DO BMP180
# O enunciado acadêmico cita BMP280. Este firmware mantém o BMP180 de propósito:
# são sensores diferentes e o nome não pode ser apenas trocado.
# ==============================================================================

class BMP180:
    def __init__(self, i2c, addr=0x77):
        self.i2c = i2c
        self.addr = addr
        self._read_calibration()

    def _read_short(self, reg):
        b = self.i2c.readfrom_mem(self.addr, reg, 2)
        val = (b[0] << 8) | b[1]
        return val - 65536 if val > 32767 else val

    def _read_ushort(self, reg):
        b = self.i2c.readfrom_mem(self.addr, reg, 2)
        return (b[0] << 8) | b[1]

    def _read_calibration(self):
        self.AC1 = self._read_short(0xAA)
        self.AC2 = self._read_short(0xAC)
        self.AC3 = self._read_short(0xAE)
        self.AC4 = self._read_ushort(0xB0)
        self.AC5 = self._read_ushort(0xB2)
        self.AC6 = self._read_ushort(0xB4)
        self.B1 = self._read_short(0xB6)
        self.B2 = self._read_short(0xB8)
        self.MB = self._read_short(0xBA)
        self.MC = self._read_short(0xBC)
        self.MD = self._read_short(0xBE)

    def read_raw_temperature(self):
        self.i2c.writeto_mem(
            self.addr,
            0xF4,
            bytearray([0x2E])
        )

        time.sleep_ms(5)

        return self._read_ushort(0xF6)

    def read_raw_pressure(self):
        self.i2c.writeto_mem(
            self.addr,
            0xF4,
            bytearray([0x34])
        )

        time.sleep_ms(5)

        b = self.i2c.readfrom_mem(
            self.addr,
            0xF6,
            3
        )

        return ((b[0] << 16) + (b[1] << 8) + b[2]) >> 8

    def read_pressure(self):
        UT = self.read_raw_temperature()
        UP = self.read_raw_pressure()

        X1 = ((UT - self.AC6) * self.AC5) >> 15
        X2 = (self.MC << 11) // (X1 + self.MD)
        B5 = X1 + X2

        B6 = B5 - 4000

        X1 = (self.B2 * (B6 * B6 >> 12)) >> 11
        X2 = (self.AC2 * B6) >> 11
        X3 = X1 + X2

        B3 = (((self.AC1 * 4 + X3) << 0) + 2) >> 2

        X1 = (self.AC3 * B6) >> 13
        X2 = (self.B1 * (B6 * B6 >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2

        B4 = (self.AC4 * (X3 + 32768)) >> 15
        B7 = (UP - B3) * 50000

        if B7 < 0x80000000:
            p = (B7 * 2) // B4
        else:
            p = (B7 // B4) * 2

        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16

        X2 = (-7357 * p) >> 16

        return (p + ((X1 + X2 + 3791) >> 4)) / 100.0


# ==============================================================================
# CONEXÕES
# ==============================================================================

cliente_mqtt = None

if conectar_wifi():
    cliente_mqtt = conectar_mqtt()


# ==============================================================================
# CONFIGURAÇÃO DOS DISPOSITIVOS
# ==============================================================================

# 1. Barramento I2C compartilhado
# OLED + BMP180
i2c = machine.I2C(
    0,
    scl=machine.Pin(22),
    sda=machine.Pin(21)
)


# Display OLED
oled = ssd1306.SSD1306_I2C(
    128,
    64,
    i2c
)


# BMP180
try:
    bmp = BMP180(i2c)
    bmp_disponivel = True
except Exception as erro:
    print("Erro ao iniciar BMP180:", erro)
    bmp_disponivel = False


# 2. Configuração do Pluviômetro
# GPIO 13 com Pull-up

pino_pluviometro = machine.Pin(
    13,
    machine.Pin.IN,
    machine.Pin.PULL_UP
)

contador_pulsos = 0
mm_por_pulso = 0.25
ultimo_tempo_pulso = 0


def tratar_pulso(pino):
    global contador_pulsos
    global ultimo_tempo_pulso

    tempo_atual = time.ticks_ms()

    if time.ticks_diff(
        tempo_atual,
        ultimo_tempo_pulso
    ) > 50:

        contador_pulsos += 1
        ultimo_tempo_pulso = tempo_atual


pino_pluviometro.irq(
    handler=tratar_pulso,
    trigger=machine.Pin.IRQ_FALLING
)


# 3. Sensor DHT22
# GPIO 14

sensor_dht = dht.DHT22(
    machine.Pin(14)
)


# 4. Sensor MQ-135
# GPIO 34

mq135_adc = machine.ADC(
    machine.Pin(34)
)

mq135_adc.atten(
    machine.ADC.ATTN_11DB
)


# 5. Sensor LDR
# GPIO 35

ldr_adc = machine.ADC(
    machine.Pin(35)
)

ldr_adc.atten(
    machine.ADC.ATTN_11DB
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

valor_ldr = 0
porcentagem_luz = 0.0


# ==============================================================================
# INFORMAÇÕES INICIAIS
# ==============================================================================

print("")
print("==========================================")
print(" ESTAÇÃO METEOROLÓGICA COMPLETA")
print("==========================================")
print("Pluviômetro: GPIO 13")
print("DHT22: GPIO 14")
print("MQ-135: GPIO 34 (ADC)")
print("LDR: GPIO 35 (ADC)")
print("OLED + BMP180: GPIOs 21 (SDA) e 22 (SCL)")
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
        # BMP180
        # ----------------------------------------------------------------------

        if bmp_disponivel:

            try:
                pressao = bmp.read_pressure()

            except Exception:
                print("Erro na leitura do BMP180")


        # ----------------------------------------------------------------------
        # MQ-135
        # ----------------------------------------------------------------------

        valor_mq135 = mq135_adc.read()


        # ----------------------------------------------------------------------
        # LDR
        # ----------------------------------------------------------------------

        valor_ldr = ldr_adc.read()

        porcentagem_luz = (
            valor_ldr / 4095.0
        ) * 100.0


        ultimo_tempo_leitura = tempo_atual


    # ==========================================================================
    # ENVIO DOS DADOS VIA MQTT A CADA 5 SEGUNDOS
    # ==========================================================================

    if time.ticks_diff(
        tempo_atual,
        ultimo_tempo_mqtt
    ) > 5000:

        total_mm = contador_pulsos * mm_por_pulso


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
            "ldr_valor": valor_ldr,
            "luminosidade": porcentagem_luz,
            "chuva_mm": total_mm
        }


        # ----------------------------------------------------------------------
        # CONVERTER DICIONÁRIO PARA JSON
        # ----------------------------------------------------------------------

        mensagem = json.dumps(dados)


        # ----------------------------------------------------------------------
        # PUBLICAR NO MQTT
        # ----------------------------------------------------------------------

        if cliente_mqtt is None:
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
        ) % 5

        tempo_alternar_tela = tempo_atual


    # ==========================================================================
    # ATUALIZAÇÃO DO DISPLAY OLED
    # ==========================================================================

    oled.fill(0)


    # --------------------------------------------------------------------------
    # TELA 0 - PLUVIÔMETRO
    # --------------------------------------------------------------------------

    if modo_tela == 0:

        oled.text(
            "   PLUVIOMETRO  ",
            0,
            0
        )

        oled.text(
            "----------------",
            0,
            10
        )

        total_mm = (
            contador_pulsos * mm_por_pulso
        )

        oled.text(
            f"Chuva:  {total_mm:.2f} mm",
            0,
            32
        )

        oled.text(
            f"Pulsos: {contador_pulsos}",
            0,
            48
        )


    # --------------------------------------------------------------------------
    # TELA 1 - DHT22
    # --------------------------------------------------------------------------

    elif modo_tela == 1:

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
    # TELA 2 - BMP180
    # --------------------------------------------------------------------------

    elif modo_tela == 2:

        oled.text(
            "BAROMETRO BMP180",
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
    # TELA 3 - MQ-135
    # --------------------------------------------------------------------------

    elif modo_tela == 3:

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
    # TELA 4 - LDR
    # --------------------------------------------------------------------------

    elif modo_tela == 4:

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
            f"ADC: {valor_ldr}",
            0,
            28
        )

        oled.text(
            f"Luz: {porcentagem_luz:.1f}%",
            0,
            46
        )


    oled.show()

    time.sleep_ms(100)