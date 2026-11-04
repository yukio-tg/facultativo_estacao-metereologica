# Fundamentação do protótipo

Resumo da base teórica da estação meteorológica e de como cada conceito
aparece no projeto.

## 3.1 Contextualização e justificativa

Uma cidade inteligente usa dados do ambiente urbano para apoiar decisões de
moradores e da gestão pública. A Internet das Coisas permite que objetos
simples, como uma estação meteorológica, meçam o ambiente e publiquem essas
medições por uma rede.

Temperatura, umidade, pressão, qualidade relativa do ar e luminosidade ajudam
a perceber calor, mudanças de tempo e condições do entorno. Uma estação de
baixo custo não substitui um instituto meteorológico, mas torna visível a
condição de um ponto específico e pode ser replicada em vários locais. Quando
os dados ficam abertos, a comunidade consulta a mesma informação usada para uma
decisão.

## 3.2 Objetivo geral

Desenvolver e validar uma estação que integra ESP32, transmissão Wi-Fi/MQTT,
conferência dos dados em Python, armazenamento SQLite, API Flask e painel web.

## 3.3 Objetivos específicos e situação atual

| Objetivo | Situação |
|---|---|
| Circuito com ESP32 e sensores ambientais | Montado com DHT22, BMP280, MQ-135 e sensor de luz digital. O pluviômetro foi retirado do escopo do protótipo |
| Firmware com leitura, tratamento e MQTT | Funcionando na placa física, com início automático ao ligar |
| Servidor Python com recepção, conferência e armazenamento | Funcionando; leituras reais da placa foram recebidas e gravadas |
| Banco relacional | SQLite, tabela `leituras` |
| Interface com mapa e gráficos | Painel com cards, gráficos, mapa da posição fixa e cálculo de vetor e distância. Roda no computador do grupo, ainda sem hospedagem pública |
| Organização do trabalho | Kanban abaixo |

## 3.4 Termos-chave

- **Firmware:** programa que roda dentro do microcontrolador (`main.py`).
- **Telemetria:** envio automático de medições para outro sistema, aqui a cada
  cinco segundos.
- **ESP32:** microcontrolador com Wi-Fi, pinos digitais (GPIO), conversor
  analógico-digital (ADC) e barramento I2C.
- **MQTT:** protocolo em que um dispositivo publica mensagens em um tópico e
  outro as recebe por meio de um intermediário (broker).
- **API RESTful:** endereços HTTP que devolvem dados, como `/api/dados` e
  `/api/historico`.
- **Payload:** conteúdo da mensagem MQTT, neste projeto um objeto JSON.
- **Geolocalização vetorial:** deslocamento representado por componentes
  leste e norte, em metros, a partir da posição da estação.

## Arquitetura em camadas

- **Percepção:** DHT22, BMP280, MQ-135 e sensor de luz ligados ao ESP32.
- **Rede:** Wi-Fi até o broker HiveMQ, no tópico `universidade/sensores/estacao`.
- **Aplicação:** Python confere e grava; Flask entrega; o navegador apresenta
  cards, gráficos e mapa.

## Sensores e eletrônica

O DHT22 entrega temperatura e umidade por um sinal digital no GPIO 14. O
BMP280 mede pressão e conversa com o ESP32 pelo barramento I2C (SDA no GPIO 21
e SCL no GPIO 22). Cada BMP280 traz números de calibração gravados de fábrica,
que o firmware lê e usa na fórmula do fabricante para obter a pressão em hPa.
Em São Paulo a leitura fica perto de 930 hPa, porque a cidade está a cerca de
760 m de altitude e o valor não é convertido para o nível do mar.

O MQ-135 é lido pelo ADC no GPIO 34. O ADC transforma a tensão contínua do
sensor em um número de 0 a 4095. Esse número é relativo, não é concentração em
ppm, e recebe uma classificação: Ar Limpo, Ar Moderado ou Ar Poluido.

O sensor de luz é digital: o módulo entrega apenas dois estados, alto ou
baixo, conforme a luz esteja acima ou abaixo do limite do próprio módulo. O firmware lê o GPIO 35 e traduz
para Claro ou Escuro.

Essa diferença ilustra os dois tipos de sinal. Um sinal analógico, como o do
MQ-135, varia continuamente e precisa do ADC. Um sinal digital, como o do
sensor de luz, tem apenas dois níveis lógicos e é lido diretamente.

## Lógica aplicada aos dados

Antes de gravar, o servidor avalia proposições lógicas sobre cada mensagem. A
leitura só é aceita se todas forem verdadeiras (operação E):

- a mensagem tem exatamente os seis campos esperados;
- os valores numéricos são números;
- −40 ≤ temperatura ≤ 80 °C;
- 0 ≤ umidade ≤ 100 %;
- 300 ≤ pressão ≤ 1100 hPa;
- 0 ≤ valor do MQ-135 ≤ 4095;
- o status do ar corresponde ao valor do MQ-135;
- a luminosidade é Claro ou Escuro.

Se qualquer condição for falsa, a mensagem é descartada e o motivo aparece no
terminal.

## Backend

O servidor recebe o JSON, transforma em dicionário Python, confere e grava uma
linha no SQLite com data e hora UTC. A API consulta essa tabela. Dicionários
representam cada leitura e listas representam o histórico.

## Geometria analítica

A estação está em um ponto fixo informado pelo grupo: latitude
-23,564978600650882 e longitude -46,65086234823989. Ao clicar em outro ponto do
mapa, o painel calcula:

- componente norte = Δlatitude × 111.320 m;
- componente leste = Δlongitude × 111.320 m × cos(latitude da estação);
- distância = √(leste² + norte²), o módulo do vetor.

O cosseno corrige o fato de os meridianos se aproximarem longe do Equador. A
versão completa do servidor também calcula a distância geográfica pela fórmula
de haversine, que considera a curvatura da Terra.

## Kanban do trabalho realizado

| A fazer | Em andamento | Concluído |
|---|---|---|
| Hospedar o painel na internet | Documentação final | Firmware na placa física com início automático |
| Calibrar MQ-135 e conferir pressão com uma referência | — | Troca do BMP180 pelo BMP280 |
| — | — | Servidor, banco, API, painel e mapa |
| — | — | Versão simplificada do código para estudo e apresentação |

## Referências

BOSCH SENSORTEC. BMP280: Digital Pressure Sensor – Data Sheet. Bosch
Sensortec, 2021.

ESPRESSIF SYSTEMS. ESP32 Series Datasheet. Xangai: Espressif Systems.
Disponível em: https://www.espressif.com/en/support/documents/technical-documents.
Acesso em: 3 out. 2026.

OASIS. MQTT Version 3.1.1. 29 out. 2014. Disponível em:
http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html.
Acesso em: 3 out. 2026.

SQLITE CONSORTIUM. SQLite Documentation. Disponível em:
https://www.sqlite.org/docs.html. Acesso em: 3 out. 2026.

ZANELLA, Andrea et al. Internet of Things for Smart Cities. IEEE Internet of
Things Journal, v. 1, n. 1, p. 22-32, fev. 2014.
