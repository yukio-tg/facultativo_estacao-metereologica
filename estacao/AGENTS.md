# Instruções do projeto — Estação Meteorológica

## Contexto

Este é um projeto acadêmico de uma estação meteorológica de baixo custo.

Objetivo geral:

Desenvolver e validar um sistema embarcado completo, integrando hardware ESP32 e software, com backend Python e dashboard web público para coleta e disponibilização de dados ambientais.

## Arquitetura desejada

ESP32
→ Wi-Fi
→ MQTT
→ Broker HiveMQ
→ Backend Python
→ Validação dos dados
→ SQLite
→ API Flask
→ Dashboard HTML/CSS/JavaScript

## Sensores

O projeto utiliza:

- DHT22: temperatura e umidade
- BMP180: pressão atmosférica
- MQ-135: qualidade relativa do ar através de leitura ADC
- LDR: luminosidade relativa
- Pluviômetro: precipitação em mm

IMPORTANTE:
O código atual utiliza BMP180, embora a especificação acadêmica mencione BMP280. Não alterar isso silenciosamente. Manter BMP180 até que seja decidido o contrário.

O sensor de qualidade do ar é MQ-135, não MQ-2.

## MQTT

Broker atual:

broker.hivemq.com

Porta:

1883

Tópico:

universidade/sensores/estacao

## Regras de desenvolvimento

- Priorizar funcionamento e simplicidade para um protótipo acadêmico.
- Não introduzir frameworks ou tecnologias desnecessárias.
- Preferir Python + Flask + SQLite no backend.
- Preferir HTML + CSS + JavaScript no frontend.
- Fazer alterações pequenas e verificáveis.
- Antes de grandes alterações, explicar o plano.
- Não apagar funcionalidades existentes sem motivo.
- Não alterar nomes de sensores para esconder inconsistências.
- Não inventar dados de sensores físicos.
- Não tratar leitura ADC do MQ-135 como ppm sem calibração.
- Não tratar porcentagem do LDR como lux sem calibração.
- Validar dados recebidos antes de armazená-los.
- Armazenar timestamp das leituras.
- Manter código simples o suficiente para ser explicado em uma apresentação acadêmica.

## Workflow

Antes de implementar uma funcionalidade grande:

1. Inspecione os arquivos existentes.
2. Explique rapidamente o que será alterado.
3. Faça a implementação.
4. Execute os testes ou o programa quando possível.
5. Corrija erros encontrados.
6. Mostre quais arquivos foram alterados e por quê.

Não reescreva o projeto inteiro quando uma alteração localizada for suficiente.

## Prioridade atual

Precisamos primeiro concluir o fluxo:

ESP32/Wokwi
→ MQTT
→ Python
→ SQLite
→ API
→ Dashboard

Depois adicionar:

- histórico;
- gráficos;
- atualização periódica;
- mapa;
- melhorias visuais;
- documentação.

## Comunicação

Quando houver um erro, não apenas contorne o problema.

Explique:

- causa provável;
- arquivo afetado;
- alteração realizada;
- como verificar se foi corrigido.

Como este projeto será apresentado academicamente, priorize soluções que o aluno consiga explicar.