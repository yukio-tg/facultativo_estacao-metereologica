# Estação Meteorológica com ESP32, MQTT e Flask

Protótipo acadêmico de baixo custo para coletar dados ambientais no ESP32,
publicá-los por MQTT, validá-los em Python, armazená-los no SQLite e exibi-los
em um dashboard web.

## Arquitetura

```mermaid
flowchart LR
    Sensores --> ESP32
    ESP32 -->|Wi-Fi| HiveMQ
    HiveMQ -->|MQTT| BackendPython
    BackendPython --> Validacao
    Validacao --> SQLite
    SQLite --> APIFlask
    APIFlask --> Dashboard
```

- Broker: `broker.hivemq.com`
- Porta: `1883`
- Tópico: `universidade/sensores/estacao`
- Atualização do ESP32 e do dashboard: aproximadamente 5 segundos

## Sensores e significado dos dados

- **DHT22:** temperatura em °C e umidade relativa em %.
- **BMP180:** pressão atmosférica em hPa. O enunciado acadêmico cita BMP280,
  mas este protótipo mantém o BMP180. Não há cálculo de altitude.
- **MQ-135:** valor ADC relativo de 0 a 4095 e classificação qualitativa. O
  valor não representa ppm sem calibração.
- **LDR:** ADC bruto e percentual relativo. O percentual não representa lux.
- **Pluviômetro:** precipitação acumulada desde o boot, considerando
  `0,25 mm` por pulso.

O trabalho acadêmico menciona BMP280, mas este protótipo usa BMP180. Os nomes
não são intercambiáveis: uma eventual migração exige troca do componente e do
driver.

## Backend

### Preparação no Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Execução

```powershell
python app.py
```

Abra `http://localhost:5000`. O mesmo processo executa o Flask e mantém um
subscriber MQTT em segundo plano. O arquivo `estacao.db` é criado
automaticamente e não é versionado.

Variáveis opcionais:

- `ESTACAO_DB_PATH`: caminho do banco SQLite.
- `FLASK_HOST`: interface de rede; padrão `0.0.0.0`.
- `FLASK_PORT`: porta HTTP; padrão `5000`.
- `FLASK_DEBUG=1`: ativa debug sem o reloader, evitando dois subscribers.

### API

- `GET /api/dados`: última leitura válida; retorna `404` enquanto não houver
  dados.
- `GET /api/historico?limite=40`: histórico cronológico. O limite permitido é
  de 1 a 500.
- `GET /api/estacao`: ponto demonstrativo do mapa. Não é uma medição de campo.
- `GET /api/distancia?latitude=-15.1&longitude=-47.1`: vetor local em metros
  e distância geográfica até esse ponto.

O timestamp é gerado pelo backend em UTC no momento do armazenamento.

## Contrato MQTT

Exemplo de payload:

```json
{
  "dht22_temp": 24.5,
  "dht22_umi": 61.0,
  "pressao_hpa": 1012.4,
  "mq135_valor": 843,
  "mq135_status": "Ar Limpo",
  "ldr_valor": 2048,
  "luminosidade": 50.0122,
  "chuva_mm": 1.25
}
```

Antes de gravar, o backend verifica campos, tipos, valores finitos, faixas dos
sensores, coerência entre ADC e status do MQ-135, relação entre LDR e
luminosidade e passos de `0,25 mm` do pluviômetro. Mensagens inválidas são
descartadas e registradas no terminal.

## Wokwi

O circuito está em `esp32/diagram.json`. O Wokwi não oferece um componente
nativo para MQ-135; por isso um potenciômetro simula somente sua saída ADC,
sem fingir que se trata de outro sensor de gases. Um botão simula os pulsos do
pluviômetro.

Para executar pelo Wokwi for VS Code:

1. Instale a extensão **Wokwi Simulator**.
2. Instale o utilitário do MicroPython: `python -m pip install mpremote`.
3. Abra `esp32/diagram.json` e inicie o simulador escolhendo
   `esp32/wokwi.toml`.
4. Com a simulação visível, em outro terminal execute:

```powershell
cd esp32
python -m mpremote connect port:rfc2217://localhost:4000 fs cp ssd1306.py :ssd1306.py + fs cp main.py :main.py + reset
```

O Serial Monitor deve exibir a conexão Wi-Fi/MQTT e um JSON a cada cinco
segundos. Ajuste DHT22, BMP180, LDR e o potenciômetro na interface; pressione
o botão azul para simular chuva.

## Testes

```powershell
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário e não acessam o broker. Para o teste ponta
a ponta:

1. execute o backend;
2. execute a simulação Wokwi;
3. confirme no terminal do ESP32 a publicação do JSON;
4. confirme no terminal Python a mensagem `Leitura ... armazenada`;
5. altere um sensor e verifique cards, horário e gráficos no navegador;
6. reinicie o backend e confirme que o histórico continua disponível.

## Estrutura

```text
.
├── app.py                 # Flask e endpoints
├── database.py            # persistência SQLite
├── geo.py                 # ponto demonstrativo e distâncias
├── mqtt_service.py        # subscriber HiveMQ
├── validation.py          # contrato e validação
├── requirements.txt
├── templates/
│   └── index.html         # dashboard responsivo
├── tests/
│   └── test_backend.py
└── esp32/
    ├── main.py            # firmware MicroPython
    ├── ssd1306.py         # driver do OLED
    ├── diagram.json       # circuito Wokwi
    └── wokwi.toml         # configuração do simulador
```

## Limitações do protótipo

- O HiveMQ público não autentica o publicador; a validação reduz, mas não
  elimina, o risco de mensagens de terceiros no tópico compartilhado.
- A chuva é acumulada desde o boot e não representa intensidade por hora.
- O mapa usa a coordenada ilustrativa `-15, -47`. Ela não é a posição real da
  estação.
- O sensor de pressão implementado é o BMP180. O enunciado cita BMP280, e essa
  diferença permanece explícita.
- O circuito do Wokwi ainda não foi executado nesta máquina porque a extensão
  do simulador não está disponível. A publicação MQTT foi comprovada com um
  cliente Python no computador.
- A placa física ainda não foi testada.

## Como levar o projeto para a placa física

Esta seção separa o que o código e o circuito do Wokwi definem do que ainda
precisa ser confirmado no hardware real. Não ligue um fio apenas porque ele
parece equivalente.

### 1. Arquivos que vão para o ESP32

Copie somente:

- `esp32/main.py`
- `esp32/ssd1306.py`

Não copie `diagram.json`, `wokwi.toml` nem o arquivo `.bin` do simulador para
o sistema de arquivos da placa. O `.bin` é o interpretador MicroPython e, se
necessário, é gravado na memória flash por outro processo.

### 2. Bibliotecas MicroPython

Já fazem parte do MicroPython padrão: `machine`, `network`, `time`, `json` e
`ubinascii`.

O projeto também importa:

- `dht`, para o DHT22;
- `umqtt.simple`, para o MQTT;
- `ssd1306`, fornecido pelo arquivo local `ssd1306.py`.

### 3. Como instalar as bibliotecas

Com a placa já contendo MicroPython e aparecendo como porta serial:

```powershell
python -m pip install esptool mpremote
python -m mpremote connect COM5 mip install umqtt.simple
```

Troque `COM5` pela porta real. Se `import dht` falhar no REPL, execute também
`mip install dht`. O arquivo `ssd1306.py` é enviado no passo 6, sem instalação
separada.

### 4. Como conectar o ESP32 ao computador

Use um cabo USB de dados, não apenas de carga. O Windows deve criar uma porta
COM. Confirme o número em Gerenciador de Dispositivos. O chip USB da placa
pode ser CP210x ou CH340; instale o driver correspondente se a porta não
aparecer.

**PRECISA SER CONFIRMADO:** número da porta COM e modelo exato da placa.

### 5. Como gravar o MicroPython

Faça isto apenas se a placa ainda não tiver MicroPython. Baixe o firmware
`ESP32_GENERIC` em [micropython.org](https://micropython.org/download/ESP32_GENERIC/)
correspondente ao ESP32 clássico usado no Wokwi (`board-esp32-devkit-c-v4`).

```powershell
python -m esptool --chip esp32 --port COM5 erase_flash
python -m esptool --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 firmware.bin
```

**PRECISA SER CONFIRMADO:** se a placa for ESP32-S2, S3, C3 ou outra variante,
o firmware e o endereço `0x1000` mudam. Não use este comando nesses modelos.

### 6. Como enviar os arquivos

```powershell
cd esp32
python -m mpremote connect COM5 fs cp ssd1306.py :ssd1306.py
python -m mpremote connect COM5 fs cp main.py :main.py
python -m mpremote connect COM5 reset
```

### 7. Pinos definidos pelo projeto

| Função | GPIO | Interface |
|---|---|---|
| DHT22, dados | 14 | digital |
| BMP180, SDA | 21 | I2C |
| BMP180, SCL | 22 | I2C |
| OLED SSD1306, SDA | 21 | I2C, mesmo barramento |
| OLED SSD1306, SCL | 22 | I2C, mesmo barramento |
| MQ-135, saída analógica | 34 | ADC, somente entrada |
| LDR, saída analógica | 35 | ADC, somente entrada |
| Pluviômetro | 13 | digital com pull-up interno |

### 8 e 9. Ligações e alimentação

Todas as alimentações desenhadas no Wokwi usam `3V3` e `GND` do ESP32:

- DHT22: VCC em 3V3, GND em GND e dados em GPIO 14.
- BMP180: VCC em 3V3, GND em GND, SDA em GPIO 21 e SCL em GPIO 22.
- OLED: VCC em 3V3, GND em GND e os mesmos SDA/SCL.
- LDR do diagrama: VCC, GND e AO em GPIO 35. Esse componente do Wokwi é um
  módulo com saída analógica, não um LDR solto.
- Pluviômetro do diagrama: um contato em GPIO 13 e o outro em GND.

O MQ-135 do Wokwi não é o sensor real. O diagrama liga um potenciômetro a
GPIO 34 apenas para simular um número ADC.

### 10. Cuidados elétricos

- Desligue o USB antes de montar ou alterar fios.
- Não conecte saída de 5 V a GPIO, ADC ou ao chip BMP180.
- Os GPIO 34 e 35 não possuem pull-up interno e não funcionam como saída.
- O código ativa pull-up interno somente no GPIO 13.
- O DHT22 normalmente precisa de resistor pull-up de 4,7 kΩ a 10 kΩ entre
  dados e 3V3 quando o sensor é avulso. Módulos prontos podem já trazê-lo.

**PRECISA SER CONFIRMADO:**

- Se o DHT22 disponível é avulso ou módulo com pull-up.
- A tensão de alimentação e da saída analógica do módulo MQ-135. Muitos
  módulos aquecem com 5 V e podem produzir até cerca de 5 V no pino AO.
  Meça AO com multímetro antes de ligá-lo ao GPIO 34. Se passar de 3,3 V,
  é necessário um divisor de tensão dimensionado para o módulo específico.
  O projeto atual não define os resistores desse divisor.
- Se o LDR é um módulo com pino AO, como no Wokwi, ou um componente avulso.
  Um LDR avulso precisa de divisor resistivo, que não está especificado aqui.
- A tensão aceita pelo módulo BMP180 e pelo OLED comprados. O chip BMP180
  opera em baixa tensão; não assuma que o módulo tolera 5 V.
- O valor real de milímetros por pulso do pluviômetro. O código usa `0,25`.
- O consumo total dos módulos antes de alimentá-los pelo pino 3V3 do ESP32.

### 11. O que muda entre Wokwi e placa

Em `esp32/main.py`, troque a chamada:

```python
wifi.connect("Wokwi-GUEST", "")
```

pelo nome e pela senha da rede real. Mantenha broker, porta, tópico, pinos e
o nome BMP180, salvo se o hardware for realmente substituído por BMP280.

### 12. Wi-Fi

A rede `Wokwi-GUEST` existe apenas no simulador. Na placa, use uma rede 2,4
GHz. O ESP32 clássico não usa Wi-Fi de 5 GHz.

### 13. Como testar cada sensor

Abra o REPL ou o monitor serial com `python -m mpremote connect COM5` e
observe as mensagens iniciais e as telas do OLED:

- DHT22: temperatura e umidade mudam ao aproximar a mão ou o ar.
- BMP180: pressão aparece em hPa. Se surgir “Sensor Offline”, confira I2C.
- MQ-135: o ADC muda quando a condição do ar muda. O número não é ppm.
- LDR: o ADC e o percentual mudam ao cobrir ou iluminar o sensor. Não é lux.
- Pluviômetro: cada pulso válido aumenta a contagem e a chuva em 0,25 mm.
- OLED: as cinco telas alternam sem apagar o restante do programa.

### 14. Como testar o MQTT

O Serial Monitor deve mostrar “MQTT conectado!” e um JSON a cada cinco
segundos. Outro computador pode assinar o mesmo tópico:

```powershell
python -c "import paho.mqtt.client as mqtt; c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2); c.on_message=lambda *_args: print(_args[-1].payload.decode()); c.connect('broker.hivemq.com',1883,30); c.subscribe('universidade/sensores/estacao'); c.loop_forever()"
```

### 15, 16 e 17. Backend, banco e dashboard

Execute `python app.py` no computador. O terminal deve registrar a conexão ao
broker e, para cada JSON válido, “Leitura ... armazenada”. Depois confira:

- `http://localhost:5000/api/dados`
- `http://localhost:5000/api/historico?limite=10`
- os cards, os gráficos e o horário em `http://localhost:5000`

Uma mensagem inválida deve aparecer como rejeitada e não aumentar a quantidade
de linhas do SQLite. O dashboard também mostra o mapa demonstrativo; clique
nele para calcular a distância vetorial.
