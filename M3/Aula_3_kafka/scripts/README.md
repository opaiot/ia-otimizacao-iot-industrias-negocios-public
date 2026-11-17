# Scripts da prática Kafka IoT

Este diretório contém os scripts da prática **Kafka para telemetria IoT observável**:

- `producer.py`: simula 5 sensores IoT e publica eventos JSON no tópico Kafka, com `sensor_id` como chave;
- `consumer_metrics.py`: consome os eventos, registra partition e offset e expõe métricas Prometheus em `/metrics`;
- `requirements.txt`: dependências Python (`confluent-kafka`, `prometheus-client`).

O caminho principal da prática é com Docker, descrito no [README da aula](../README.md): lá os dois scripts rodam em containers, sem instalar nada no host. Esta página documenta as variáveis de configuração e explica como executar os scripts **diretamente com Python**, contra o Kafka da stack Docker — útil para estudar ou modificar os scripts.

## Formato do evento

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

## Variáveis de ambiente

Os dois scripts leem toda a configuração de variáveis de ambiente:

| Variável | Padrão | Usada por | Descrição |
| --- | --- | --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | ambos | Endereço do broker |
| `KAFKA_TOPIC` | `iot.air_quality` | ambos | Tópico da prática |
| `SEND_INTERVAL_SECONDS` | `1` | producer | Intervalo entre eventos |
| `GROUP_ID` | `air-quality-processors` | consumer | Consumer group |
| `AUTO_OFFSET_RESET` | `earliest` | consumer | De onde ler quando o grupo não tem offset salvo |
| `METRICS_PORT` | `8000` | consumer | Porta do endpoint `/metrics` |
| `CONSUMER_ID` | `<hostname>:<porta>` | consumer | Identificador exibido nas métricas |

## Métricas expostas pelo consumer

```text
iot_events_consumed_total
iot_events_by_partition_total
iot_kafka_last_offset
iot_temperature_celsius
iot_humidity_percent
iot_co2_ppm
```

## Executar no host contra o Kafka do Docker

Suba a stack da aula (o broker publica um listener externo em `localhost:29092`):

```bash
cd M3/Aula_3_kafka/docker
docker compose up --build -d
```

Prepare o ambiente Python (o `confluent-kafka` instala por wheel, sem compilação):

```bash
cd ..
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r scripts/requirements.txt
```

Em um terminal, um producer extra:

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:29092 python scripts/producer.py
```

Em outro terminal (ative o venv de novo), um consumer extra em um grupo próprio — use uma porta diferente de qualquer consumer já em execução:

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:29092 \
GROUP_ID=meu-grupo-local \
METRICS_PORT=8005 \
CONSUMER_ID=consumer-host \
python scripts/consumer_metrics.py
```

Confira as métricas:

```bash
curl http://localhost:8005/metrics
```

No PowerShell, defina as variáveis antes de chamar o script:

```powershell
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"
$env:GROUP_ID = "meu-grupo-local"
$env:METRICS_PORT = "8005"
python scripts\consumer_metrics.py
```

## Problemas comuns

- `ModuleNotFoundError: No module named 'confluent_kafka'`: ative o venv e reinstale com `pip install -r scripts/requirements.txt`.
- Erro de conexão com o broker: confirme que a stack Docker está no ar e use `localhost:29092` (o `kafka:9092` só existe dentro da rede Docker).
- Porta de métricas em uso: troque `METRICS_PORT` (e `CONSUMER_ID`, para distinguir nas métricas).
