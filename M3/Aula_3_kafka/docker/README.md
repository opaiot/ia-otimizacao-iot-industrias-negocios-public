# Aula 3 - Kafka IoT no Docker

Esta pasta sobe a prática completa da Aula 3 em containers, sem necessidade de
instalar Kafka, Prometheus ou Grafana na máquina. Os scripts Python da pasta
[`../scripts`](../scripts) são usados **sem modificação**: toda a configuração é
injetada por variáveis de ambiente que os próprios scripts já leem.

> Os scripts de instalação na VM ([`../instalando_kafka_vm.md`](../instalando_kafka_vm.md),
> [`../scripts/configure_prometheus.sh`](../scripts/configure_prometheus.sh) e
> [`../scripts/configure_grafana.sh`](../scripts/configure_grafana.sh)) continuam
> válidos para o cenário de VM. Esta pasta é uma alternativa para rodar tudo no Docker.

## Topologia

```text
producer ──> kafka (KRaft) ──> consumer (/metrics:8000) ──> prometheus:9090 ──> grafana:3000
```

| Serviço      | Função                                              | Porta no host |
|--------------|-----------------------------------------------------|---------------|
| `kafka`      | Broker Kafka 4.x em modo KRaft (sem ZooKeeper)      | `29092`       |
| `kafka-init` | Cria o tópico `iot.air_quality` com 3 partitions    | -             |
| `producer`   | `scripts/producer.py` simulando sensores            | -             |
| `consumer`   | `scripts/consumer_metrics.py` expondo `/metrics`    | `8000`        |
| `prometheus` | Coleta as métricas do consumer                      | `9090`        |
| `grafana`    | Dashboard provisionado automaticamente              | `3000`        |

## Como subir

A partir desta pasta (`Modulo_3/Aula_3_kafka/docker`):

```bash
docker compose up --build
```

Para rodar em segundo plano:

```bash
docker compose up --build -d
```

## Endpoints

- Métricas do consumer: <http://localhost:8000/metrics>
- Prometheus: <http://localhost:9090> (página de targets em `/targets`)
- Grafana: <http://localhost:3000> (usuário `admin`, senha `admin`)
- Dashboard: <http://localhost:3000/d/iot-kafka-telemetry>

O data source `Prometheus - Kafka IoT` e o dashboard `Kafka IoT - Telemetria
Observavel` já vêm provisionados (mesma configuração do
[`configure_grafana.sh`](../scripts/configure_grafana.sh)).

## Experimentos

### Vários consumers no mesmo grupo

Escale o serviço `consumer` para observar o rebalanceamento entre as 3 partitions:

```bash
docker compose up --build -d --scale consumer=3
```

> Ao escalar, remova o mapeamento fixo de porta `8000:8000` do serviço `consumer`
> no [`docker-compose.yml`](docker-compose.yml) (ou troque por `"8000"` para porta
> dinâmica), pois várias réplicas não podem publicar na mesma porta do host.
> O Prometheus continua coletando todas as réplicas pelo nome do serviço.

### Inspecionar o tópico e os grupos

```bash
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --describe --topic iot.air_quality --bootstrap-server kafka:9092

docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --describe --group air-quality-processors --bootstrap-server kafka:9092
```

### Parar e retomar o consumer (offset)

```bash
docker compose stop consumer
# aguarde alguns segundos com o producer rodando
docker compose start consumer
```

O consumer retoma a partir do offset salvo pelo grupo.

### Acessar o Kafka a partir do host

O listener externo está publicado em `localhost:29092`. Ferramentas no host podem
apontar para esse endereço (dentro da rede docker, os serviços usam `kafka:9092`).

## Parar e limpar

```bash
docker compose down          # para os containers
docker compose down -v       # para e remove os volumes (Kafka, Prometheus, Grafana)
```

## Configuração

As variáveis de ambiente dos scripts podem ser ajustadas no
[`docker-compose.yml`](docker-compose.yml):

```text
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=iot.air_quality
SEND_INTERVAL_SECONDS=1
GROUP_ID=air-quality-processors
AUTO_OFFSET_RESET=earliest
METRICS_PORT=8000
CONSUMER_ID=consumer-docker
```
