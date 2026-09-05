# Aula 4 - MQTT para Kafka

Esta aula conecta telemetria MQTT ao tópico Kafka `iot.air_quality` da [Aula 3](../Aula_3_kafka/README.md), mantendo o mesmo formato de evento usado pelo `producer.py` da prática anterior.

## Pré-requisitos

- Docker & Docker Compose instalados e funcionais
- Kafka da [Aula 3](../Aula_3_kafka/README.md) em execução (veja instruções na Aula 3)
- Python 3.10+ (para executar os scripts localmente, opcional se usar Docker)

## Rápido (quick start)

1. Suba o Kafka da Aula 3:

```bash
cd Modulo_3/Aula_3_kafka/docker
docker compose up -d
```

2. Na pasta desta aula copie o exemplo de variáveis e suba a stack:

```bash
cd Modulo_3/Aula_4_esp32_mqtt_kafka
cp .env.example .env
docker compose up --build -d
```

3. Logs:

```bash
docker compose logs -f --tail=50 mosquitto mqtt-kafka-producer
```

## Objetivo

- ler mensagens JSON de um broker MQTT;
- normalizar o payload para o formato da Aula 3;
- publicar no Kafka com `sensor_id` como chave da mensagem.

## Arquitetura

```text
ESP32 + DHT22 + MQ-7 (firmware/)
  -> Mosquitto MQTT
  -> mqtt_kafka_producer.py
  -> Kafka topic iot.air_quality
  -> consumers da Aula 3
```

## Portas

| Serviço | Porta no host | Onde sobe |
| --- | --- | --- |
| Mosquitto | `1883` | `docker-compose.yml` desta aula |
| Kafka | `29092` | [Aula 3 - Kafka](../Aula_3_kafka/docker/docker-compose.yml) |

## Variáveis de ambiente

Copie o exemplo e ajuste se necessário:

```bash
cd Modulo_3/Aula_4_esp32_mqtt_kafka
cp .env.example .env
```

| Variável | Padrão | Uso |
| --- | --- | --- |
| `MQTT_HOST` | `localhost` | Broker MQTT no host (ESP32, Wokwi, script local) |
| `MQTT_INTERNAL_HOST` | `mosquitto` | Broker MQTT dentro da rede Docker |
| `MQTT_PORT` | `1883` | Porta MQTT |
| `MQTT_TOPIC` | `opaiot/temperature` | Tópico MQTT de telemetria |
| `KAFKA_BOOTSTRAP_SERVERS` | `host.docker.internal:29092` | Kafka visto pelo bridge no Docker |
| `KAFKA_EXTERNAL_BOOTSTRAP` | `localhost:29092` | Kafka visto pelo script no host |
| `KAFKA_TOPIC` | `iot.air_quality` | Tópico Kafka de destino (Aula 3) |

## Como subir com Docker Compose

Primeiro suba o Kafka da Aula 3:

```bash
cd Modulo_3/Aula_3_kafka/docker
docker compose up -d
```

Depois suba Mosquitto e o bridge desta aula:

```bash
cd Modulo_3/Aula_4_esp32_mqtt_kafka
cp .env.example .env
docker compose up --build -d
```

Esta stack sobe apenas Mosquitto (`allow_anonymous`) e o bridge `mqtt-kafka-producer`, que publica no Kafka externo da Aula 3.

Acompanhe os logs:

```bash
docker compose logs -f --tail=50 mosquitto mqtt-kafka-producer
```

## Fluxo sugerido

1. Suba o Kafka da Aula 3 e depois o compose desta aula.
2. Grave o firmware em [firmware/esp32_mq7_mqtt.ino](firmware/esp32_mq7_mqtt.ino) no ESP32 ou no Wokwi.
3. Configure `MQTT_SERVER` no firmware com o IP do host (porta `1883`).
4. Valide as mensagens no Kafka da Aula 3 com `kafka-console-consumer.sh` ou com o consumer da Aula 3.

Alternativa sem Docker: execute [scripts/mqtt_kafka_producer.py](scripts/mqtt_kafka_producer.py) no host apontando para Mosquitto e Kafka já em execução.

## Entrada principal

| Arquivo | Descrição |
| --- | --- |
| [.env.example](.env.example) | Servidores MQTT/Kafka e tópicos da prática |
| [docker-compose.yml](docker-compose.yml) | Mosquitto e bridge MQTT -> Kafka (externo, Aula 3) |
| [mosquitto/mosquitto.conf](mosquitto/mosquitto.conf) | Broker MQTT de laboratório com `allow_anonymous` |
| [firmware/esp32_mq7_mqtt.ino](firmware/esp32_mq7_mqtt.ino) | Firmware ESP32 + DHT22 + MQ-7 publicando MQTT |
| [firmware/README.md](firmware/README.md) | Configuração Wokwi, hardware e testes |
| [scripts/mqtt_kafka_producer.py](scripts/mqtt_kafka_producer.py) | Ponte MQTT -> Kafka |
| [scripts/README.md](scripts/README.md) | Instalação, variáveis e verificação |
