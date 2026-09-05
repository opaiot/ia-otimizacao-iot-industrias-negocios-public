# Módulo 2 - Fundamentos de IoT e IIoT

Este módulo reúne as práticas do OpAIoT voltadas aos fundamentos de IoT com ESP32: saídas e entradas digitais, leitura de sensores, conversão analógico-digital (ADC), publicação MQTT e um pipeline de dados fim a fim.

As atividades usam o ESP32 (placa física ou simulador [Wokwi](https://wokwi.com)) programado pela Arduino IDE. A partir da Aula 8, e nos materiais de Extras, a prática soma uma stack de apoio em Docker Compose (broker MQTT, banco de dados de série temporal e Grafana) para fechar o pipeline de ponta a ponta.

Este repositório publica código para as Aulas 1, 2, 4, 7 e 8. As Aulas 3, 5 e 6 do módulo são aulas teóricas, sem prática de código associada, por isso não aparecem aqui.

<img width="1672" height="941" alt="IoT-Mod2" src="https://github.com/user-attachments/assets/ce77dd9c-09bf-4cd6-8fc4-4988094c9c0d" />

## Ordem sugerida

1. Comece pela [Aula 1 - Stacks e Ferramentas](Aula_1_stacks_ferramentas/pratica_01_ESP32_blink.ino) para validar o ambiente (Arduino IDE/Wokwi) piscando um LED.
2. Avance para a [Aula 2 - Sensores](Aula_2_sensores/) e pratique entradas digitais (botão, encoder rotativo) e a primeira leitura analógica.
3. Aprofunde a conversão analógico-digital na [Aula 4 - ADC](Aula_4_adc/) com potenciômetro e termistor NTC.
4. Publique dados de um sensor via [Aula 7 - MQTT](Aula_7_mqtt/pratica_mqtt.ino), com DHT22 e broker público.
5. Feche o módulo com a [Aula 8 - Pipeline IoT Fim a Fim](Aula_8_pipeline_iot/README.md), que integra ESP32, MQTT, banco de série temporal e Grafana.
6. Quando quiser aprofundar, veja os [Extras](#extras): amostragem/FFT e conectividade em redes IoT.

## Aulas

| Aula | Entrada principal | Conteúdo |
| --- | --- | --- |
| Aula 1 - Stacks e Ferramentas | [pratica_01_ESP32_blink.ino](Aula_1_stacks_ferramentas/pratica_01_ESP32_blink.ino) | Primeiro sketch no ESP32: pisca um LED no GPIO18 para validar o ambiente (Arduino IDE/Wokwi). |
| Aula 2 - Sensores | [Aula_2_sensores/](Aula_2_sensores/) | Três sketches: botão com pull-up alternando um LED, leitura de encoder rotativo (posição e sentido) e primeira leitura analógica de um potenciômetro. |
| Aula 4 - ADC | [Aula_4_adc/](Aula_4_adc/) | Conversão analógico-digital do ESP32: potenciômetro (leitura e conversão para tensão) e termistor NTC com cálculo de temperatura via Steinhart-Hart. |
| Aula 7 - MQTT | [pratica_mqtt.ino](Aula_7_mqtt/pratica_mqtt.ino) | ESP32 + DHT22 publicam temperatura e umidade em JSON via MQTT (`broker.emqx.io`, tópico `opaiot-dht-1`), visualizados no MQTTX Web Client. |
| Aula 8 - Pipeline IoT Fim a Fim | [Aula_8_pipeline_iot/README.md](Aula_8_pipeline_iot/README.md) | Pipeline completo em Docker Compose: ESP32 (Wokwi) + DHT22 → Mosquitto → backend Node.js → PostgreSQL/TimescaleDB → Grafana. |

## Extras

Materiais complementares, fora da sequência numerada de aulas.

| Extra | Entrada principal | Conteúdo |
| --- | --- | --- |
| Amostragem e Conversão A/D | [Extras/Aula_sobre_Amostragem/README.md](Extras/Aula_sobre_Amostragem/README.md) | Teoria de amostragem, Nyquist e FFT, mais um laboratório completo: ESP32 + MPU6050 → MQTT → backend Python (FFT) → InfluxDB → Grafana. |
| Redes Mesh e Conectividade IoT | [Extras/Aula_sobre_Redes_Mesh/iot_mesh_zigbee_rpl_lorawan_concepts.ipynb](Extras/Aula_sobre_Redes_Mesh/iot_mesh_zigbee_rpl_lorawan_concepts.ipynb) | Notebook sobre Wi-Fi, Mesh, Zigbee/RPL e LoRaWAN (modelos didáticos), com tabela HTML de classificação de redes e slides de apoio de uma monitoria do curso. |

## Estrutura

```text
M2/
├── Aula_1_stacks_ferramentas/
│   └── pratica_01_ESP32_blink.ino
├── Aula_2_sensores/
│   ├── pratica_01_esp32_button_toggle_led.ino
│   ├── pratica_02_esp32_rotary_encoder.ino
│   └── pratica_03_esp32_potentiometer.ino
├── Aula_4_adc/
│   ├── pratica_01_esp32_potentiometer.ino
│   └── pratica_02_esp32_ntc.ino
├── Aula_7_mqtt/
│   └── pratica_mqtt.ino
├── Aula_8_pipeline_iot/
│   ├── backend/
│   ├── grafana/provisioning/
│   ├── init-db/
│   ├── mosquitto/
│   ├── esp32_dht22_mqtt.ino
│   └── docker-compose.yml
└── Extras/
    ├── Aula_sobre_Amostragem/
    │   ├── adc_didatico.ipynb
    │   └── application/
    └── Aula_sobre_Redes_Mesh/
        ├── iot_mesh_zigbee_rpl_lorawan_concepts.ipynb
        ├── classificacao_redes_iot.html
        └── Monitoria_OpAIoT_27-05-2026.pdf
```

## Ambientes de execução

### ESP32 físico ou simulador Wokwi

Caminho principal das Aulas 1, 2, 4 e 7, e do firmware das Aulas 8 e dos Extras. Abra o `.ino` (ou `.py`, no caso do MicroPython) na Arduino IDE ou cole no simulador [wokwi.com](https://wokwi.com) e ajuste pinos, Wi-Fi e broker conforme os comentários no topo de cada arquivo.

Entradas úteis:

| Tema | Arquivo |
| --- | --- |
| Aula 1 | [Aula_1_stacks_ferramentas/pratica_01_ESP32_blink.ino](Aula_1_stacks_ferramentas/pratica_01_ESP32_blink.ino) |
| Aula 2 | [Aula_2_sensores/](Aula_2_sensores/) |
| Aula 4 | [Aula_4_adc/](Aula_4_adc/) |
| Aula 7 | [Aula_7_mqtt/pratica_mqtt.ino](Aula_7_mqtt/pratica_mqtt.ino) |
| Firmware da Aula 8 | [Aula_8_pipeline_iot/esp32_dht22_mqtt.ino](Aula_8_pipeline_iot/esp32_dht22_mqtt.ino) |
| Firmware dos Extras (Amostragem) | [Extras/Aula_sobre_Amostragem/application/](Extras/Aula_sobre_Amostragem/application/) (Arduino ou MicroPython) |

### Docker local

Use este caminho para subir os serviços de apoio (broker MQTT, banco de dados e Grafana) em qualquer máquina com Docker.

Entradas úteis:

| Tema | Arquivo |
| --- | --- |
| Aula 8 - stack completa | [Aula_8_pipeline_iot/README.md](Aula_8_pipeline_iot/README.md) |
| Extras - Amostragem | [Extras/Aula_sobre_Amostragem/application/README.md](Extras/Aula_sobre_Amostragem/application/README.md) |

## Serviços e portas comuns

| Serviço | Porta padrão | Onde aparece |
| --- | --- | --- |
| Mosquitto (MQTT) | `1883` (`8883` TLS) | Aula 8 |
| Backend Node.js (API HTTP) | `3000` | Aula 8 |
| PostgreSQL / TimescaleDB | `5432` | Aula 8 |
| Grafana | `3001` (Aula 8) / `3000` (Extras) | Aula 8, Extras |
| InfluxDB | `8086` | Extras - Amostragem |
| Broker MQTT público `broker.emqx.io` | `1883` | Aula 7, Extras - Amostragem |

> As Aula 7 e o laboratório de Amostragem usam o broker público `broker.emqx.io`, sem
> precisar subir Mosquitto local. Já a Aula 8 sobe seu próprio broker Mosquitto em
> Docker. Se Aula 8 e Extras - Amostragem forem executados ao mesmo tempo, note que
> ambos publicam o Grafana em portas de host diferentes (`3001` e `3000`) para evitar
> conflito.

## Fluxo geral do módulo

```text
ESP32 (Wokwi ou físico)
  -> saída digital (LED)                    (Aula 1)
  -> entradas digitais e sensores           (Aula 2)
  -> conversão analógico-digital (ADC)      (Aula 4)
  -> publicação MQTT                        (Aula 7)
  -> pipeline fim a fim (MQTT/BD/Grafana)   (Aula 8)

Extras
  -> amostragem, FFT e séries temporais     (Amostragem e Conversão A/D)
  -> topologias e conectividade IoT         (Redes Mesh)
```

## Requisitos gerais

- Arduino IDE, ou apenas um navegador para usar o simulador [Wokwi](https://wokwi.com).
- Placa ESP32 (opcional — todas as práticas também rodam no simulador).
- Docker e Docker Compose para a Aula 8 e para o laboratório de Amostragem dos Extras.
- Acesso à internet (broker MQTT público `broker.emqx.io`, simulador Wokwi).
- Git para clonar o repositório.

Cada prática comenta, no topo do próprio código (ou no README, quando houver), os requisitos específicos de ligação, bibliotecas e configuração. Use este README como índice do módulo e siga a documentação específica antes de executar a prática.

[Voltar ao início do curso](../README.md)
