# Firmware ESP32 + DHT22 + MQ-7 (MQTT)

Publica telemetria no broker MQTT no formato da Aula 3, pronta para o bridge `scripts/mqtt_kafka_producer.py`.

## Pré-requisitos

- Arduino IDE ou PlatformIO (para compilar/gravar)
- Wokwi (opcional, para simulação)
- Cabo USB para gravação em placa física

## Rápido (gravando e testando)

1. Abra `esp32_mq7_mqtt.ino` na Arduino IDE ou no PlatformIO.
2. Ajuste `MQTT_SERVER` com o IP do host (use `ipconfig` no Windows ou `ifconfig`/`ip a` no Linux).
3. Compile e grave na placa ESP32.
4. Para simular, crie um projeto no Wokwi e cole o código; ajuste `MQTT_SERVER` conforme o endpoint acessível.

## Componentes

| Item | Valor |
| --- | --- |
| Microcontrolador | ESP32 |
| DHT22 | GPIO 15 (temperatura e umidade) |
| MQ-7 | GPIO 34 / AOUT (monóxido de carbono) |
| Protocolo | MQTT (porta 1883) |
| Tópico padrão | `opaiot/temperature` |

## Payload MQTT

```json
{
  "sensor_id": "sensor-01",
  "room": "lab-01",
  "temperature": 25.40,
  "humidity": 58.20,
  "co2": 850,
  "timestamp": "2026-06-07T15:30:00Z"
}
```

| Campo | Origem |
| --- | --- |
| `temperature` | DHT22 |
| `humidity` | DHT22 |
| `co2` | MQ-7 (CO estimado, mapeado para o campo `co2` do pipeline da Aula 3) |
| `timestamp` | NTP em UTC, quando disponível |

## Configuração

Edite as constantes no topo de [esp32_mq7_mqtt.ino](esp32_mq7_mqtt.ino):

| Constante | Wokwi | Placa física |
| --- | --- | --- |
| `WIFI_SSID` | `Wokwi-GUEST` | SSID da sua rede |
| `WIFI_PASS` | `""` | Senha do WiFi |
| `MQTT_SERVER` | IP do host na rede local | IP do PC/servidor com Mosquitto |
| `MQTT_TOPIC` | `opaiot/temperature` | Igual ao `MQTT_TOPIC` do bridge Python |
| `SENSOR_ID` | `sensor-01` | Identificador do sensor |
| `ROOM` | `lab-01` | Sala ou ambiente |
| `DHT_PIN` | `15` | GPIO do DHT22 |
| `MQ7_AOUT_PIN` | `34` | GPIO com ADC para AOUT do MQ-7 |
| `RO_CLEAN_AIR_KOHM` | `10.0` | Calibração do MQ-7 em ar limpo |

Para descobrir o IP do host no Windows:

```powershell
ipconfig
```

Use o **Endereço IPv4** da interface ativa. Não use `localhost` no firmware.

## Wokwi

1. Crie um projeto ESP32 com DHT22 no pino 15 e MQ-7 com AOUT no GPIO 34.
2. Cole o conteúdo de `esp32_mq7_mqtt.ino`.
3. Ajuste `MQTT_SERVER` para o IP acessível pelo simulador.
4. Suba Mosquitto no host e execute o bridge Python.

## Hardware físico

```text
DHT22 VCC  -> ESP32 3.3V
DHT22 GND  -> ESP32 GND
DHT22 DATA -> ESP32 GPIO 15 (+ resistor 10 kΩ para 3.3V)

MQ-7 VCC   -> 5V
MQ-7 GND   -> GND
MQ-7 AOUT  -> ESP32 GPIO 34
```

Se o AOUT do MQ-7 ultrapassar 3,3 V, use divisor de tensão antes do GPIO.

Compile e grave com Arduino IDE ou PlatformIO, com as bibliotecas:

- `WiFi` (core ESP32)
- `PubSubClient`
- `DHT sensor library`

## Fluxo completo da aula

```text
ESP32 + DHT22 + MQ-7 (este firmware)
  -> Mosquitto MQTT
  -> mqtt_kafka_producer.py
  -> Kafka iot.air_quality
  -> consumer da Aula 3
```
