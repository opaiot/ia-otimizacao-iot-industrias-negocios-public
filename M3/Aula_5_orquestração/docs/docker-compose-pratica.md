# Roteiro - Docker Compose

Este roteiro executa a stack IoT local:

```text
sensor-simulator -> Mosquitto -> mqtt-to-kafka -> Kafka -> iot-processor -> Prometheus -> Grafana
```

## 1. Entrar no diretório

```bash
cd Modulo_3/Aula_5_orquestração
```

Observe que o arquivo principal da prática é `docker-compose.yaml`.

## 2. Conferir estrutura

```bash
find . -maxdepth 3 -type f | sort
```

Em Windows PowerShell, use:

```bash
powershell -Command "Get-ChildItem -Recurse -File | Select-Object -ExpandProperty FullName"
```

Verifique se aparecem `services/`, `mosquitto/`, `prometheus/`, `grafana/` e `k8s/`.

## 3. Subir a stack

```bash
docker compose up --build -d
```

A primeira execução baixa imagens oficiais e constrói os três containers Python.

## 4. Verificar containers

```bash
docker compose ps
```

Espere os serviços `kafka`, `mosquitto`, `sensor-simulator`, `mqtt-to-kafka`, `iot-processor`, `prometheus`, `grafana` e `kafka-ui`.

## 5. Observar logs do sensor

```bash
docker compose logs -f --tail=50 sensor-simulator
```

Observe mensagens JSON com `temperature`, `humidity`, `vibration` e `timestamp`.

## 6. Observar logs da ponte MQTT para Kafka

```bash
docker compose logs -f --tail=50 mqtt-to-kafka
```

Observe o tópico MQTT de origem, o tópico Kafka de destino e o `device_id`.

## 7. Observar logs do processador

```bash
docker compose logs -f --tail=50 iot-processor
```

Observe `partition`, `offset` e métricas sendo atualizadas.

## 8. Testar MQTT com mosquitto_sub e mosquitto_pub

Assine o tópico de telemetria:

```bash
docker compose exec mosquitto mosquitto_sub -h localhost -t 'iot/+/telemetry' -C 5
```

Publique uma leitura manual:

```bash
docker compose exec mosquitto mosquitto_pub \
  -h localhost \
  -t 'iot/device-002/telemetry' \
  -m '{"device_id":"device-002","timestamp":"2026-06-06T12:00:00Z","temperature":28.4,"humidity":63.2,"vibration":0.12}'
```

Confira os logs do `mqtt-to-kafka` depois da publicação.

## 9. Abrir Kafka UI

Abra:

```text
http://localhost:8080
```

Entre no cluster `opaiot-local` e veja o tópico `iot.telemetry`.

## 10. Listar tópicos Kafka pelo terminal

```bash
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --list
```

O tópico esperado é `iot.telemetry`.

## 11. Consumir tópico Kafka pelo terminal

```bash
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.telemetry \
  --from-beginning \
  --max-messages 5
```

Observe os eventos JSON gravados no Kafka.

## 12. Abrir endpoint /metrics

```bash
curl http://localhost:8000/metrics
```

Procure estas métricas:

```text
iot_messages_total
iot_temperature_celsius
iot_humidity_percent
iot_vibration_level
```

## 13. Abrir Prometheus

Abra:

```text
http://localhost:9090
```

Use a tela principal para executar consultas PromQL.

## 14. Verificar targets

Abra:

```text
http://localhost:9090/targets
```

O target `iot-processor:8000` deve aparecer como `UP`.

## 15. Executar consultas PromQL

No Prometheus, teste:

```promql
iot_messages_total
```

```promql
rate(iot_messages_total[1m])
```

```promql
iot_temperature_celsius
```

```promql
iot_humidity_percent
```

```promql
iot_vibration_level
```

Observe os valores mudando conforme novas mensagens chegam.

## 16. Abrir Grafana

Abra:

```text
http://localhost:3000
```

Use:

```text
usuário: admin
senha: admin
```

O datasource Prometheus já vem provisionado.

## 17. Observar dashboard

Abra:

```text
http://localhost:3000/d/iot-local-telemetry
```

Observe total de mensagens, taxa, temperatura, umidade e vibração.

## 18. Escalar sensor-simulator

```bash
docker compose up -d --scale sensor-simulator=3
```

Veja os logs:

```bash
docker compose logs -f --tail=80 sensor-simulator
```

A taxa de mensagens deve aumentar. Para voltar a uma réplica:

```bash
docker compose up -d --scale sensor-simulator=1
```

## 19. Reiniciar serviços

Reinicie a ponte e o processador:

```bash
docker compose restart mqtt-to-kafka iot-processor
```

Confira se retomaram:

```bash
docker compose logs -f --tail=50 mqtt-to-kafka iot-processor
```

Observe que o processador continua lendo o tópico Kafka pelo mesmo grupo `iot-processor`.

## 20. Encerrar a stack

Pare a prática:

```bash
docker compose down
```

Remova volumes quando quiser zerar Kafka, Prometheus e Grafana:

```bash
docker compose down -v
```

Depois disso, `docker compose ps` não deve listar containers ativos desta prática.
