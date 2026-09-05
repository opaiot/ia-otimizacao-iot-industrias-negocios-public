# Aula 1 - Datasets / Observabilidade no Docker

Esta pasta sobe a prática da Aula 1 em containers, sem precisar instalar Python,
Prometheus ou Grafana na máquina. Os scripts da pasta [`../scripts`](../scripts)
são usados **sem modificação**.

> Os scripts da prática usam **constantes** (`CSV_FILE`, `PORT`,
> `INTERVAL_SECONDS`) em vez de variáveis de ambiente. Por isso a imagem
> preserva a estrutura de pastas da aula (`scripts/` ao lado de `data/`) e o
> exportador roda de dentro de `scripts/`, exatamente como na VM.
>
> O fluxo de VM descrito em [`../README.md`](../README.md) continua válido. Esta
> pasta é uma alternativa para rodar tudo no Docker.

## Topologia

```text
2-prometheus.py (/metrics:8000) ──> prometheus:9090 ──> grafana:3000
1-inspect.py ──> ../outputs (execução única)
```

| Serviço      | Função                                                  | Porta no host |
|--------------|---------------------------------------------------------|---------------|
| `exporter`   | `2-prometheus.py` expondo `/metrics`                    | `8000`        |
| `prometheus` | Coleta as métricas do exporter (job `opaiot_iaq`)       | `9090`        |
| `grafana`    | Dashboard provisionado automaticamente                  | `3000`        |
| `inspect`    | `1-inspect.py` (one-shot, gera `../outputs`)            | -             |

## Como subir

A partir desta pasta (`Modulo_3/Aula_1_datasets/docker`):

```bash
docker compose up --build
```

Em segundo plano:

```bash
docker compose up --build -d
```

## Endpoints

- Métricas do exporter: <http://localhost:8000/metrics>
- Prometheus: <http://localhost:9090> (página de targets em `/targets`, job `opaiot_iaq` deve ficar `UP`)
- Grafana: <http://localhost:3000> (usuário `admin`, senha `admin`)
- Dashboard: <http://localhost:3000/d/opaiot-iaq>

O data source `Prometheus - IAQ` e o dashboard `OpAIoT - IAQ Datasets` já vêm
provisionados.

## Gerar os artefatos de inspeção

O serviço `inspect` roda `1-inspect.py` uma vez e grava os arquivos em
[`../outputs`](../outputs) no host:

```bash
docker compose --profile inspect run --rm inspect
```

Arquivos gerados (compare com [`../outputs_example`](../outputs_example)):

```text
columns_profile.csv
semantic_classification.csv
numeric_summary.csv
normalized_events.jsonl
iot_event_schema.json
inspection_summary.json
```

## Consultas PromQL úteis

```promql
opaiot_iaq_sensor_value
opaiot_iaq_anomaly_flag
opaiot_iaq_stream_index
opaiot_iaq_dataset_rows
opaiot_iaq_active_metrics
```

## Parar e limpar

```bash
docker compose down          # para os containers
docker compose down -v       # para e remove os volumes (Prometheus, Grafana)
```

## Observações

- O exportador publica uma linha do CSV a cada 5 segundos (`INTERVAL_SECONDS`).
  Para alterar porta ou intervalo, edite as constantes no topo de
  [`../scripts/2-prometheus.py`](../scripts/2-prometheus.py) e refaça o build.
- O dataset usado é [`../data/IoT_Indoor_Air_Quality_Dataset.csv`](../data/IoT_Indoor_Air_Quality_Dataset.csv),
  copiado para a imagem no build.
