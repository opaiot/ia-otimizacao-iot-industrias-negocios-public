# Ponte MQTT -> Kafka

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

O caminho principal da prática é com Docker, descrito no [README da aula](../README.md): lá o serviço `mqtt-kafka-producer` já executa este script. Esta página documenta a normalização de payload, as variáveis de configuração e como rodar o script **diretamente com Python** no host. Para rodá-lo na VM do curso (sem Docker), siga o [roteiro para a VM](../roteiro_para_vm.md).

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

`temperature` e `humidity` são obrigatórios: payloads sem um deles, ou que não sejam um objeto JSON, são ignorados com um aviso no log.

O `sensor_id` resultante é usado como **chave** da mensagem Kafka, o que mantém os eventos de um mesmo sensor na mesma partition.

O firmware desta aula em [firmware/esp32_mq7_mqtt.ino](../firmware/esp32_mq7_mqtt.ino) já publica no formato da Aula 3. Exemplo alternativo, compatível com o ESP32 da [Aula 8 do M2](../../../M2/Aula_8_pipeline_iot/esp32_dht22_mqtt.ino):

```json
{
  "temperature": 25.4,
  "humidity": 58.2,
  "deviceId": "esp32-dht22",
  "location": "sala"
}
```

## Variáveis de ambiente

Lidas pelo script. No Compose, os valores vêm de [../docker-compose.yml](../docker-compose.yml) e do `.env` da aula (veja [../.env.example](../.env.example)).

| Variável | Padrão no script | No Compose | Descrição |
| --- | --- | --- | --- |
| `MQTT_HOST` | `localhost` | `mosquitto` | Broker MQTT (nome do serviço na rede Docker) |
| `MQTT_PORT` | `1883` | `1883` | Porta do broker. No Compose é fixa; a porta publicada no host é `MQTT_HOST_PORT` |
| `MQTT_TOPIC` | `opaiot/air_quality` | `opaiot/air_quality` | Tópico assinado (aceita wildcard, ex.: `opaiot/+/air_quality`) |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:29092` | `kafka:9092` | Kafka da Aula 3, pela rede compartilhada |
| `KAFKA_TOPIC` | `iot.air_quality` | `iot.air_quality` | Tópico Kafka de destino |
| `DEFAULT_SENSOR_ID` | `sensor-01` | `sensor-01` | Sensor usado quando a mensagem não traz identificador |
| `DEFAULT_ROOM` | `lab-01` | `lab-01` | Sala usada quando a mensagem não traz `room`/`location` |
| `DEFAULT_CO2` | `800` | `800` | CO2 usado quando a mensagem não traz `co2` |

O padrão do script para o Kafka (`localhost:29092`) é o endereço do listener externo da Aula 3, correto para quem roda o script **no host**. Dentro de um container ele não serve; por isso o Compose define `kafka:9092`. O script também aceita `KAFKA_EXTERNAL_BOOTSTRAP` como alternativa a `KAFKA_BOOTSTRAP_SERVERS`.

## Executar no host

Suba primeiro as duas stacks (Kafka da Aula 3 e Mosquitto desta aula), conforme o [README da aula](../README.md). Pare o serviço da ponte para não ter duas instâncias concorrendo:

```bash
cd M3/Aula_4_esp32_mqtt_kafka
docker compose stop mqtt-kafka-producer
```

Prepare o ambiente Python:

```bash
cd scripts
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Execute apontando para as portas publicadas no host (`1883` para o Mosquitto, `29092` para o Kafka da Aula 3):

```bash
MQTT_HOST=localhost MQTT_PORT=1883 \
KAFKA_BOOTSTRAP_SERVERS=localhost:29092 \
python mqtt_kafka_producer.py
```

No PowerShell:

```powershell
$env:MQTT_HOST = "localhost"
$env:MQTT_PORT = "1883"
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"
python mqtt_kafka_producer.py
```

> Rodando no host, `localhost:29092` é o endereço correto do Kafka: é o listener externo que o broker da Aula 3 anuncia. Dentro de um container, esse endereço não serve — por isso o Compose usa `kafka:9092` pela rede compartilhada.

Ao terminar, encerre o script com `Ctrl+C` e religue a ponte do Compose com `docker compose start mqtt-kafka-producer`.

## Verificação

Com a ponte rodando, publique uma mensagem de teste:

```bash
docker compose exec mosquitto mosquitto_pub -h localhost \
  -t 'opaiot/air_quality' \
  -m '{"sensor_id":"sensor-99","room":"lab-99","temperature":28.4,"humidity":61.0,"co2":900}'
```

No Windows PowerShell 5.1, escape as aspas duplas do JSON com barra invertida (`'{\"sensor_id\":...}'`); veja o passo 3.4 do [README da aula](../README.md).

A ponte registra `forwarded mqtt payload=...` (evento normalizado) e, ao receber a mensagem seguinte, `sent topic=iot.air_quality partition=... offset=... key=sensor-99` (o callback de entrega só roda no `poll()` da próxima publicação). Confirme a chegada no consumer da Aula 3:

```bash
docker compose -f ../../Aula_3_kafka/docker/docker-compose.yml logs consumer | grep sensor-99
```

Ou leia direto do tópico, na partition indicada no log da ponte (no Git Bash do Windows, prefixe o comando com `MSYS_NO_PATHCONV=1`; veja o [README da aula](../README.md)):

```bash
docker compose -f ../../Aula_3_kafka/docker/docker-compose.yml exec kafka \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.air_quality \
  --property print.key=true \
  --partition 0 --from-beginning --max-messages 2
```
