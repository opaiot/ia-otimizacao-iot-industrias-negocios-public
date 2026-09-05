# MQTT -> Kafka producer

Script que lê telemetria MQTT e publica no tópico Kafka `iot.air_quality` com o mesmo formato da [Aula 3](../../Aula_3_kafka/scripts/producer.py):

```json
{
  "sensor_id": "sensor-01",
  "room": "lab-01",
  "temperature": 27.45,
  "humidity": 62.10,
  "co2": 800,
  "timestamp": "2026-06-07T12:34:56.789012+00:00"
}
```

## Formato de entrada MQTT

O script aceita mensagens já no formato da Aula 3 ou converte automaticamente payloads comuns de IoT:

| Campo Kafka | Origem MQTT |
| --- | --- |
| `sensor_id` | `sensor_id`, `device_id`, `deviceId` ou `DEFAULT_SENSOR_ID` |
| `room` | `room`, `location` ou `DEFAULT_ROOM` |
| `temperature` | `temperature` |
| `humidity` | `humidity` |
| `co2` | `co2` ou `DEFAULT_CO2` |
| `timestamp` | `timestamp` ou horário UTC atual |

O firmware desta aula em [firmware/esp32_mq7_mqtt.ino](../firmware/esp32_mq7_mqtt.ino) já publica no formato da Aula 3.

Exemplo alternativo compatível com o ESP32 da [Aula 8](../../../Modulo_2/Aula_8_pipeline_iot/esp32_dht22_mqtt.ino):

```json
{
  "temperature": 25.4,
  "humidity": 58.2,
  "deviceId": "esp32-dht22",
  "location": "sala"
}
```

## Instalação

```bash
cd Modulo_3/Aula_4_esp32_mqtt_kafka/scripts
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Pré-requisitos

- Python 3.10+ e `pip`
- Docker (se for usar a stack em `docker compose`)

## Executar localmente (exemplo rápido)

Linux/macOS:

```bash
cd Modulo_3/Aula_4_esp32_mqtt_kafka
cp .env.example .env
cd scripts
source .venv/bin/activate
set -o allexport; source ../.env; set +o allexport
python mqtt_kafka_producer.py
```

Windows PowerShell:

```powershell
cd Modulo_3\Aula_4_esp32_mqtt_kafka
Copy-Item .env.example .env -ErrorAction SilentlyContinue
cd scripts
.venv\Scripts\Activate.ps1
# Carrega variáveis do .env para o processo (simples)
Get-Content ..\.env | ForEach-Object {
  if ($_ -match '^[^#=]+=(.*)$') {
    $parts = $_ -split '='; [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), 'Process')
  }
}
$env:KAFKA_BOOTSTRAP_SERVERS = $env:KAFKA_EXTERNAL_BOOTSTRAP
python mqtt_kafka_producer.py
```

## Execução

Com a stack da aula (`docker compose up --build -d` na raiz de `Aula_4_esp32_mqtt_kafka`), o serviço `mqtt-kafka-producer` já executa este script.

Para rodar manualmente no host, carregue o `.env` da raiz da aula:

```bash
cd Modulo_3/Aula_4_esp32_mqtt_kafka
cp .env.example .env   # se ainda nao existir

cd scripts
set -a && source ../.env && set +a
python mqtt_kafka_producer.py
```

No PowerShell:

```powershell
cd Modulo_3\Aula_4_esp32_mqtt_kafka
Copy-Item .env.example .env

cd scripts
Get-Content ..\.env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
  }
}
$env:KAFKA_BOOTSTRAP_SERVERS = $env:KAFKA_EXTERNAL_BOOTSTRAP
python mqtt_kafka_producer.py
```

## Variáveis de ambiente

Definidas em [../.env.example](../.env.example):

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `MQTT_HOST` | `localhost` | Broker MQTT no host |
| `MQTT_INTERNAL_HOST` | `mosquitto` | Broker MQTT na rede Docker |
| `MQTT_PORT` | `1883` | Porta MQTT |
| `MQTT_TOPIC` | `opaiot/temperature` | Tópico MQTT (aceita wildcard `+`) |
| `KAFKA_BOOTSTRAP_SERVERS` | `host.docker.internal:29092` | Kafka para o bridge no Docker (Aula 3 no host) |
| `KAFKA_EXTERNAL_BOOTSTRAP` | `localhost:29092` | Kafka no host (usado pelo script se `KAFKA_BOOTSTRAP_SERVERS` nao estiver definido) |
| `KAFKA_TOPIC` | `iot.air_quality` | Tópico Kafka de destino |
| `DEFAULT_SENSOR_ID` | `sensor-01` | Sensor usado quando a mensagem MQTT não traz identificador |
| `DEFAULT_ROOM` | `lab-01` | Sala usada quando a mensagem MQTT não traz `room`/`location` |
| `DEFAULT_CO2` | `800` | CO2 usado quando a mensagem MQTT não traz `co2` |

## Verificação

Consuma mensagens do tópico:

```bash
docker compose -f Modulo_3/Aula_3_kafka/docker/docker-compose.yml exec kafka \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.air_quality \
  --from-beginning \
  --property print.key=true \
  --max-messages 5
```

Ou use o consumer da Aula 3 (`consumer_metrics.py`) e o Grafana provisionado na stack Kafka.
