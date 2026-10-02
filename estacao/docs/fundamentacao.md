# Fundamentação do protótipo

Este texto registra o conteúdo acadêmico pedido para a estação meteorológica.
Ele descreve o que o protótipo faz hoje e também o que ainda não foi validado
na placa física.

## 3.1 Contextualização e justificativa

Uma cidade inteligente usa dados do ambiente urbano para apoiar decisões de
moradores e da gestão pública. A Internet das Coisas permite que objetos
simples, como uma estação meteorológica, meçam o ambiente e publiquem essas
medições por uma rede.

Temperatura, umidade, pressão, qualidade relativa do ar, luminosidade e chuva
ajudam a perceber calor, risco de precipitação e condições do entorno. Uma
estação de baixo custo não substitui um instituto meteorológico, mas torna
visível a condição de um ponto específico. A transparência importa porque a
comunidade consegue consultar o mesmo dado usado para uma decisão, em vez de
depender apenas de um valor anunciado sem origem.

## 3.2 Objetivo geral

Desenvolver e validar uma estação que integra ESP32, transmissão Wi-Fi/MQTT,
validação em Python, armazenamento SQLite, API Flask e dashboard web.

## 3.3 Objetivos específicos e situação atual

| Objetivo | Situação |
|---|---|
| Circuito com ESP32, DHT22, BMP280, MQ-135, LDR e pluviômetro | Parcial: o circuito do Wokwi usa BMP180, não BMP280 |
| Firmware com leitura, tratamento e MQTT | Implementado; execução no Wokwi e na placa ainda não comprovada aqui |
| API Python com recepção, validação e armazenamento | Implementado e testado no computador |
| Banco relacional | Implementado em SQLite |
| Interface pública, responsiva, com mapa e gráficos | Interface e gráficos implementados; mapa usa ponto demonstrativo; publicação na internet não foi feita |
| Scrum/Kanban | Kanban abaixo registra o trabalho real |

## 3.4 Termos-chave

- **Firmware:** programa que roda dentro do microcontrolador. Aqui é `esp32/main.py`.
- **Telemetria:** envio de medições para outro sistema. Aqui ocorre a cada cinco segundos.
- **ESP32:** microcontrolador com Wi-Fi, GPIO, ADC e I2C.
- **MQTT:** protocolo em que um dispositivo publica mensagens e outro as recebe por meio de um intermediário.
- **API RESTful:** conjunto de endereços HTTP que devolvem dados. Exemplos: `/api/dados` e `/api/historico`.
- **Payload:** conteúdo da mensagem MQTT, neste projeto um objeto JSON.
- **Geolocalização vetorial:** representação de um deslocamento por componentes leste e norte, em metros, a partir de um ponto de origem.

## Arquitetura em camadas

- **Percepção:** DHT22, BMP180, MQ-135, LDR e pluviômetro ligados ao ESP32.
- **Rede:** Wi-Fi até o broker HiveMQ, no tópico `universidade/sensores/estacao`.
- **Aplicação:** Python valida e grava; Flask entrega; o navegador apresenta cards, gráficos e mapa.

## Sensores e eletrônica

O DHT22 entrega sinais digitais de temperatura e umidade no GPIO 14. O BMP180
mede pressão por I2C nos GPIO 21 e 22. O enunciado pede BMP280, que também
mede pressão e permite estimar altitude, mas é outro componente e usa outro
driver. Por decisão do projeto, o BMP180 foi mantido e a divergência ficou
visível no código, no dashboard e neste texto. Não há altitude calculada.

O MQ-135 é lido como ADC no GPIO 34. O resultado é um número relativo e uma
classificação qualitativa, não concentração em ppm. O LDR entra pelo ADC do
GPIO 35 e vira percentual relativo, não lux. O pluviômetro é um contato no
GPIO 13: cada pulso válido soma 0,25 mm ao acumulado desde a inicialização.

Sinais analógicos variam continuamente e passam pelo ADC. Sinais digitais
representam estados, como o pulso do pluviômetro. O debounce de 50 ms é uma
condição lógica: um novo pulso só conta se o intervalo desde o anterior for
maior que 50 ms. A validação do backend também é lógica: o valor precisa ser
numérico, finito e estar dentro da faixa antes de existir uma gravação.

## Backend

O subscriber recebe o payload, `validar_payload` aplica as regras e
`inserir_leitura` grava uma linha com data e hora UTC. A API consulta essa
tabela. Coleções Python, principalmente dicionários e listas, representam a
mensagem e o histórico.

## Geometria

O mapa usa o ponto ilustrativo de latitude -15 e longitude -47. Ele não é a
posição medida da estação. Ao clicar em outro ponto, a API calcula:

- componente norte, pela diferença de latitude;
- componente leste, pela diferença de longitude corrigida pelo cosseno da
  latitude de origem;
- distância vetorial, pela hipotenusa desses componentes;
- distância geográfica, pela fórmula de haversine.

## Kanban do trabalho realizado

| A fazer | Em andamento | Concluído no computador |
|---|---|---|
| Executar o circuito no Wokwi | — | Firmware, MQTT, validação, SQLite, API, gráficos e mapa demonstrativo |
| Testar a placa física | — | Testes automatizados e publicação MQTT de teste |
| Trocar para BMP280, se for exigido | — | Divergência BMP180 documentada |

Não houve uma equipe Scrum separada nem sprints formais. O quadro registra a
sequência real do protótipo.

## Referências

ESPRESSIF SYSTEMS. ESP32 Series Datasheet. Xangai: Espressif Systems.
Disponível em: https://www.espressif.com/en/support/documents/technical-documents.
Acesso em: 2 out. 2026.

OASIS. MQTT Version 3.1.1. 29 out. 2014. Disponível em:
http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html.
Acesso em: 2 out. 2026.

SQLITE CONSORTIUM. SQLite Documentation. Disponível em: https://www.sqlite.org/docs.html.
Acesso em: 2 out. 2026.

ZANELLA, Andrea et al. Internet of Things for Smart Cities. IEEE Internet of
Things Journal, v. 1, n. 1, p. 22-32, fev. 2014.

As folhas de dados específicas do DHT22, BMP180, BMP280, MQ-135 e do modelo
físico do pluviômetro devem ser anexadas a partir dos componentes comprados.
Os códigos exatos desses documentos **PRECISAM SER CONFIRMADOS** no PDF do
fabricante de cada peça; por isso não foram inventados aqui.
