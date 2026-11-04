1. Sumário (Índice) -WORD GERA AUTOMATICAMENTE
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha hoje às 23:59
Instruções
Deve listar com precisão todas as seções, subseções e elementos do relatório com a indicação
das respectivas páginas.
• Sumário Geral: Estrutura hierárquica numerada de tópicos do trabalho.
• Lista de Figuras: Relação sequencial de diagramas de arquitetura, esquemas elétricos
no Fritzing/Tinkercad/Wokwi, protótipos em protoboard, diagramas DER e capturas de
tela do Dashboard.
• Lista de Tabelas: Relação de tabelas de requisitos, especificações de sensores,
dicionário de dados e casos de teste.
• Lista de Abreviaturas e Siglas: Siglas técnicas utilizadas (ex.: ESP32, MQTT, API, REST,
DER, GPIO, LDR, DHT).



2. Resumo
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha hoje às 23:59
Instruções
Texto contínuo de parágrafo único (aproximadamente 500 palavras) elaborado após a conclusão do projeto.
•
Contexto: Necessidade de monitoramento ambiental em cidades inteligentes e acesso público a dados climáticos.
• Objetivo: Construção de uma estação meteorológica embarcada com disponibilização de dados em tempo real via dashboard público.
•
Metodologia: Prototipagem com ESP32 e sensores (DHT22, BMP280, MQ-135, LDR, pluviômetro), comunicação Wi-Fi/MQTT, backend desenvolvido em Python, modelagem de banco de dados e visualização web baseada em geolocalização.
•
Resultados e Conclusão: Confirmação da operacionalidade do hardware, precisão da coleta, estabilidade da API e usabilidade da interface web para conscientização cidadã.
•
Palavras-chave: Cidades Inteligentes, ESP32, Internet das Coisas (IoT), Python, Estação Meteorológica, Dashboard Web.




3. Introdução
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha hoje às 23:59
Instruções
3.1. Contextualização e Justificativa
•
Apresentar o conceito de Cidades Inteligentes (Smart Cities) e a importância da Internet das Coisas (IoT) no ambiente urbano.
Justificar a relevância da criação de uma estação meteorológica de baixo custo para o monitoramento de parâmetros como qualidade do ar, índice pluviométrico, temperatura, umidade, pressão e luminosidade.
• Destacar o impacto social da transparência dos dados para a tomada de decisões da comunidade e gestão pública.
3.2. Objetivo Geral
Desenvolver e validar um sistema embarcado completo (estação meteorológica) integrando hardware (ESP32) e software (backend Python + dashboard web interativo) para coleta e disponibilização pública de dados ambientais em tempo real.
3.3. Objetivos Específicos
•
Projetar e montar o circuito eletrônico utilizando ESP32 e os sensores DHT22, BMP280, MQ-135, LDR e pluviômetro.
• Desenvolver o firmware do ESP32 para leitura, tratamento lógico e transmissão dos dados via Wi-Fi/MQTT.
•
Implementar uma API em Python para recepção, validação matemática e armazenamento dos dados.
•
Modelar e estruturar o banco de dados relacional para persistência das leituras meteorológicas.
•
Criar uma interface web pública responsiva com mapas interativos (Geometria Analítica) e gráficos em tempo real.
•
Aplicar metodologias ágeis (Scrum/Kanban) na gestão do projeto integrador.
3.4. Definição de Termos-Chave
Definir conceitos essenciais para padronização do entendimento: Firmware, Telemetria, Microcontrolador ESP32, Protocolo MQTT, API RESTful, Payload, Geolocalização Vetorial.
4. Revisão Bibliográfica (Fundamentação Teórica)
Apresentar a sustentação teórica com citações no padrão ABNT, correlacionando os conteúdos das disciplinas do semestre:
•
Cidades Inteligentes e Internet das Coisas (IoT): Fundamentos, arquitetura em camadas de IoT (Percepção, Rede, Aplicação) e aplicações urbanas.
•
Plataforma Hardware e Sensores:
o Arquitetura do microcontrolador ESP32 e pinagem (GPIOs, ADCs, interfaces I2C/SPI).
o
Funcionamento físico e elétrico dos sensores: DHT22 (temperatura e umidade), BMP280 (pressão atmosférica e altitude), MQ-135 (qualidade do ar e gases), LDR (luminosidade) e Pluviômetro (precipitação).
•
Circuitos Lógicos Digitais e Eletrônica: Álgebra de Boole aplicada, portas lógicas de controle, sinal analógico vs. digital e leitura de entradas/saídas.
Lógica Matemática Aplicada: Aplicação de proposições lógicas para filtragem de ruídos, tratamento de dados inconsistentes e validação de intervalos válidos de leitura.
•
Programação e Backend em Python: Programação estruturada, arquitetura de APIs, manipulação de coleções de dados (listas, dicionários) e bibliotecas de integração.
• Geometria Analítica no Espaço Geográfico: Coordenadas cartesianas e geográficas, cálculo de distâncias vetoriais e posicionamento espacial para mapeamento de estações.




Instruções
4.1. Gestão do Projeto e Metodologia Ágil
• Descrever a adaptação do Scrum/Kanban para o desenvolvimento do projeto.
•
Apresentar a divisão da equipe, papéis e o planejamento das sprints quinzenais com suas respectivas entregas incrementais.
4.2. Engenharia de Software e Levantamento de Requisitos
•
Stakeholders: Cidadãos, gestores públicos, pesquisadores e equipe de manutenção.
• Delimitação do Escopo: O que o sistema cobre (coleta, envio, armazenamento e exibição) e o que está fora do escopo.
•
Requisitos Funcionais (RF):
o RF01: O ESP32 deve efetuar a leitura dos sensores a cada intervalo programado.
o RF02: O sistema deve enviar os dados para o backend via protocolo MQTT/HTTP.
o RF03: O dashboard deve plotar a localização da estação no mapa utilizando coordenadas geográficas.
o RF04: O dashboard deve emitir alertas visuais caso a qualidade do ar ou precipitação atinja níveis críticos.
•
Requisitos Não-Funcionais (RNF):
o RNF01: A interface web deve ser responsiva (adaptável a mobile e desktop). o RNF02: O tempo de atualização do dashboard não deve exceder 5 segundos após o envio do dado.
o RNF03: O backend deve validar e rejeitar leituras fora do intervalo físico aceitável dos sensores.
4.3. Arquitetura Geral do Sistema
Apresentar a arquitetura ponta a ponta detalhada do fluxo de dados: [Sensores (DHT22, BMP280, MQ-135, LDR)]
│
▼
[ESP32 / Firmware (MQTT/Wi-Fi)]
│
▼
[API Python (Flask/FastAPI) + Lógica Matemática] │
┌──────────┴──────────┐
▼                     ▼
[Banco de Dados]    [Dashboard Web (Frontend)] 5.4. Projeto de Hardware e Circuitos Digitais
•
Esquema Elétrico: Apresentar o diagrama do circuito (Fritzing/Tinkercad) detalhando todas as conexões entre o ESP32, sensores, resistores pull-up/pull-down e linhas de alimentação.
•
Tabela de Conexões e Pinagem: Mapeamento explícito das portas GPIO utilizadas.
•
Condicionamento e Lógica Digital: Explicação dos sinais lógicos digitais (ex.: pulsos do pluviômetro) e condicionamento das entradas analógicas (MQ-135 e LDR).
4.5. Desenvolvimento do Firmware (ESP32)
• Descrição do algoritmo principal em C++ (Arduino IDE) ou MicroPython.
•
Rotina de inicialização, conexão Wi-Fi e reconexão automática.
•
Algoritmos de temporização e interpolação de leitura para evitar bloqueio da CPU.
•
Formatação do payload de envio (ex.: JSON via MQTT/HTTP).
4.6. Backend em Python e Regras de Negócio
•
Estrutura da API desenvolvida em Python para recepção das requisições.
• Aplicação da Lógica Matemática: Algoritmos de filtragem para eliminar outliers ou erros de leitura dos sensores (ex.: condicional rigorosa para ignorar variações abruptas e impossíveis de temperatura).
•
Estruturas de dados empregadas (dicionários, filas, listas) para pré-processamento estatístico (média, mínima e máxima).
4.7. Modelagem do Banco de Dados
•
Modelo Conceitual: Diagrama Entidade-Relacionamento (DER).
•
Modelo Lógico e Físico: Especificação formal das tabelas, atributos, tipos de dados, chaves primárias (PK), chaves estrangeiras (FK) e restrições (NOT NULL, CHECK).
Tabela Atributo
Tipo de Dado Restrição / Descrição
estacao id_estacao
INT
PK, Auto Increment
estacao latitude
FLOAT
Coordenada Y (Geometria Analítica)
estacao longitude
FLOAT
Coordenada X (Geometria Analítica)
leitura id_leitura
BIGINT
PK, Auto Increment
leitura id_estacao
INT
FK estacao(id_estacao)
leitura temperatura FLOAT
Graus Celsius
leitura umidade
FLOAT
Porcentagem (%)
leitura pressao
FLOAT
hPa
leitura qualidade_ar INT
Valor PPM (MQ-135)
leitura luminosidade INT
Valor ADC/Lux
leitura pluviometria FLOAT
mm de chuva
leitura data_hora
TIMESTAMP Data e hora da coleta
4.8. Frontend e Dashboard Público Interativo
•
Layout e UX/UI: Mockups ou telas planejadas para acesso do cidadão.
• Aplicação de Geometria Analítica: Mapeamento das coordenadas da estação em um plano 2D/mapa interativo, calculando vetor de posição e distâncias para exibição no frontend.
•
Componentes de interface: Indicadores de tempo real (gauges), gráficos históricos e alertas climáticos.
4.9. Plano de Testes e Cronograma
•
Casos de Teste Especificados:
ID Teste
Componente
Descrição do Teste
Resultado Esperado
CT01 Hardware/Firmware
Leitura do sensor DHT22 com variação de temperatura
Leitura atualizada e sem erros no monitor serial
CT02 Comunicação
Desconexão forçada da rede Wi-Fi
Firmware tenta reconectar sem travar a execução
CT03 Backend/Lógica
Envio de leitura inconsistente (ex.: T = 150°C)
API rejeita o dado com base nas regras de validação
D Teste
Componente
Descrição do Teste
Resultado Esperado
CT04 Dashboard
Visualização da localização da estação
Marcador plotado corretamente nas coordenadas
•
Cronograma do Projeto: Apresentação do cronograma de execução das sprints (planejado vs. executado).



Instruções
Apresentação estritamente objetiva e descritiva dos artefatos construídos e funcionais (sem análises interpretativas nesta seção).
•
Protótipo Físico Final: Fotos do circuito montado em protoboard com a integração completa do ESP32 e dos 5 sensores operando.
•
Massa de Dados Coletada: Captura dos registros armazenados nas tabelas do Banco de Dados demonstrando a rotina de persistência.
•
Logs da API e Comunicação: Registros de recebimento com sucesso de payloads no servidor Python.
• Dashboard Web Ativo: Capturas de tela da interface pública final exibindo os dados em tempo real, o mapa de geolocalização e os gráficos gerados.
•
Relatório dos Casos de Teste: Tabela com os resultados reais obtidos na execução dos testes (Aprovado / Reprovado).




6. Análise dos Resultados e Discussão
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha hoje às 23:59
Instruções
Sessão de interpretação crítica do projeto, confrontando os resultados obtidos com a teoria e com os objetivos estipulados.
•
Confiabilidade e Precisão do Hardware: Análise da estabilidade da leitura dos sensores (DHT22, BMP280, MQ-135, LDR, Pluviômetro) e comportamento das portas do ESP32 sob operação contínua.
•
Eficácia dos Filtros Matemáticos: Avaliação do impacto da validação por Lógica Matemática no backend para a eliminação de ruídos e dados discrepantes.
• Desempenho da Transmissão e Arquitetura: Discussão sobre a latência na rede Wi-Fi/MQTT, tempo de resposta da API em Python e eficiência das consultas ao banco de dados.
• Usabilidade e Geolocalização no Dashboard: Análise da precisão da plotagem vetorial/geográfica no mapa (Geometria Analítica) e grau de acessibilidade da interface para o cidadão comum.
• Aderência ao Conceito de Smart Cities: Avaliação do impacto da solução criada como ferramenta real de engajamento comunitário e apoio à decisão urbana.
• Anomalias e Limitações Identificadas: Justificativa técnica para eventuais falhas observadas durante os testes de campo (ex.: interferência de luz solar no LDR, calibração do MQ-135, oscilação de sinal Wi-Fi).



7. Conclusões e Recomendações
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha hoje às 23:59
Instruções
7.1. Conclusão
•
Síntese direta do projeto condensada em 5 a 6 sentenças principais.
•
Confirmação do grau de atendimento aos objetivos geral e específicos estipulados na Introdução.
•
Validação do sucesso na integração interdisciplinar (Programação Python, Circuitos Digitais, Lógica Matemática, Geometria Analítica e Banco de Dados).
7.2. Recomendações e Trabalhos Futuros
Proposta de melhorias técnicas e continuidade da pesquisa:
•
Encapsulamento da estação em caixa hermética (IP65) impressa em 3D para exposição ao tempo.
•
Implementação de alimentação autônoma por painel solar e bateria Li-Ion.
•
Aplicação de algoritmos de Machine Learning para previsão do tempo e alertas preditivos de alagamento.
•
Expansão da rede para um modelo mesh com múltiplas estações distribuídas pela cidade.



8. Bibliografia
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha hoje às 23:59
Instruções
Relação completa de todos os materiais consultados para o desenvolvimento do projeto e da documentação, formatada estritamente segundo as normas da ABNT. Deve incluir a bibliografia indicada no Plano de Ensino:
•
ALENCAR FILHO, Edgard de. Iniciação à Lógica Matemática. São Paulo: Nobel, 2008.
•
IDOETA, I.V.; CAPUANO, F.G. Elementos de Eletrônica Digital. 42ª Ed. São Paulo: Érica, 2019.
•
KOLBAN, Neil. Kolban's Book on ESP32. Leanpub, 2018. Disponível em: https://leanpub.com/kolban-ESP32
•
LOURENÇO, A.C.; CRUZ, E.C.A.; FERREIRA, S. Circuitos Digitais. 9ª Ed. São Paulo: Érica.
•
MENEZES, N.N.C. Introdução à Programação com Python: algoritmos e lógica de programação para iniciantes. São Paulo: Novatec, 2019.
• OLIVEIRA, Sérgio de. Internet das Coisas com ESP8266, ESP32 e Raspberry Pi. São Paulo: Novatec, 2017.
•
WINTERLE, P. Vetores e Geometria Analítica. 2ª Ed. São Paulo: Pearson, 2014.



9. Apêndices
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha hoje às 23:59
Instruções
Materiais suplementares elaborados pela própria equipe durante o projeto: • Apêndice A: Código-fonte completo do Firmware do ESP32.
• Apêndice B: Código-fonte completo da API Backend em Python.
.  Apêndice C: Código-fonte das telas do Dashboard Web (HTML/CSS/JavaScript).
• Apêndice D: Script SQL de criação do Banco de Dados (DDL/DML).
• Apêndice E: Tabela detalhada de custos de hardware e componentes (BOM - Bill of Materials).



ATENÇÃO - REVISÃO BIBLIOGRAFICA -
Vence hoje às 23:59
•
Vários envios permitidos
•
Fecha amanhã às 23:59
Instruções
ESSE CAPITULO DEVE SER COLOCADO ENTRE O CAPITULO INTRODUÇÃO E METODOLOGIA. 
AJUSTAR A NUMERAÇÃO DOS CAPITULOS!
DESCRIÇÃO DO CAPÍTULO:
Revisão Bibliografia: aqui se deve descrever a evolução histórica e atual
situação do conhecimento acadêmico sobre o tópico, sumarizando o que outros
escreveram sobre o tema. Como estarão reportando trabalhos de terceiros, muito
provável que apareçam citações e referências (livros, artigos, internet), que devem
estar propriamente registrados como previsto em norma. Ao final desta sessão é
que se deve enumerar as hipóteses da pesquisa agora em curso




Roteiro de Produção e Entrega de Material Multimidiático
Data de conclusão 13 de novembro de 2026 às 23:59
•
Vários envios permitidos
•
Fecha 13 de novembro de 2026 às 23:59
Instruções
Roteiro de Produção e Entrega de Material Multimidiático - Estação Meteorológica IoT, objetivando manter um registro academico, segue material anexo para a entrega. Esta atividade não dispensa a apresentação presencial.