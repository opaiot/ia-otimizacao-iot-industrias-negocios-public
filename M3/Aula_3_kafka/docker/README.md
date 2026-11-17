# Aula 3 - Stack Docker

Referência da stack que sobe a prática completa da Aula 3 em containers. O roteiro passo a passo, com os experimentos, está no [README da aula](../README.md). Os scripts Python da pasta [`../scripts`](../scripts) são usados **sem modificação**: toda a configuração é injetada por variáveis de ambiente que os próprios scripts já leem.

## Topologia

```text
producer ──> kafka (KRaft) ──> consumer (/metrics:8000) ──> prometheus:9090 ──> grafana:3000
```

| Serviço      | Função                                              | Porta no host |
|--------------|-----------------------------------------------------|---------------|
| `kafka`      | Broker Kafka 4.x em modo KRaft (sem ZooKeeper)      | `29092`       |
| `kafka-init` | Cria o tópico `iot.air_quality` com 3 partitions    | -             |
| `producer`   | `scripts/producer.py` simulando sensores            | -             |
| `consumer`   | `scripts/consumer_metrics.py` expondo `/metrics`    | dinâmica (`docker compose port consumer 8000`) |
| `prometheus` | Coleta as métricas dos consumers                    | `9090`        |
| `grafana`    | Dashboard provisionado automaticamente              | `3000`        |

O serviço `consumer` não tem `container_name` nem porta fixa no host de propósito: assim ele pode ser escalado com `docker compose up -d --scale consumer=3`. O Prometheus descobre todas as réplicas pelo DNS interno do Docker (`dns_sd_configs` no [prometheus/prometheus.yml](prometheus/prometheus.yml)), então nenhuma configuração muda ao escalar.

## Subir, parar e limpar

A partir desta pasta (`M3/Aula_3_kafka/docker`):

```bash
docker compose up --build -d   # sobe a stack
docker compose down            # para os containers
docker compose down -v         # para e remove os volumes (Kafka, Prometheus, Grafana)
```

## Endpoints

- Prometheus: <http://localhost:9090> (targets em `/targets`, job `iot-kafka-consumers`)
- Grafana: <http://localhost:3000> (usuário `admin`, senha `admin`)
- Dashboard: <http://localhost:3000/d/iot-kafka-telemetry>
- Kafka a partir do host: `localhost:29092` (dentro da rede Docker, os serviços usam `kafka:9092`)
- Métricas do consumer: porta dinâmica; descubra com `docker compose port consumer 8000`

O data source `Prometheus - Kafka IoT` e o dashboard `Kafka IoT - Telemetria Observavel` vêm provisionados dos arquivos em [grafana/provisioning/](grafana/provisioning/).

## Configuração

As variáveis de ambiente dos scripts podem ser ajustadas no [`docker-compose.yml`](docker-compose.yml):

```text
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=iot.air_quality
SEND_INTERVAL_SECONDS=1
GROUP_ID=air-quality-processors
AUTO_OFFSET_RESET=earliest
METRICS_PORT=8000
CONSUMER_ID=consumer-docker
```

A descrição de cada variável está em [../scripts/README.md](../scripts/README.md).
