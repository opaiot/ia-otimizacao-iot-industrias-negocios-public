# Módulo 3 - Dados, Observabilidade e Eventos

Este módulo reúne as práticas do OpAIoT 2026 voltadas ao tratamento de dados IoT, séries temporais, observabilidade com Prometheus/Grafana e processamento de telemetria com Apache Kafka.

Todas as práticas rodam **localmente com Docker**: cada aula traz seus arquivos Docker Compose (e, na Aula 5, também manifests Kubernetes) com os serviços já configurados. Os READMEs das aulas seguem a mesma estrutura: objetivo, conceitos, prática passo a passo e sugestão de exercícios.

## Ordem sugerida

1. Comece pela [Aula 1 - Datasets](Aula_1_datasets/README.md) para inspecionar um CSV de sensores, normalizar eventos IoT e expor métricas Prometheus.
2. Use a [Aula 2 - Séries Temporais](Aula_2_series_temporais/README.md) para explorar séries no Grafana com datasource Prometheus provisionado.
3. Avance para a [Aula 3 - Kafka](Aula_3_kafka/README.md) para produzir, consumir e observar eventos IoT em um tópico Kafka.
4. Conecte telemetria MQTT ao Kafka na [Aula 4 - MQTT para Kafka](Aula_4_esp32_mqtt_kafka/README.md), reaproveitando o tópico da Aula 3.
5. Compare a stack IoT em Docker Compose e Kubernetes na [Aula 5 - Orquestração](Aula_5_orquestração/README.md).
6. Feche com a [Aula 6 - Segurança e Governança](Aula_6_seguranca_governanca/README.md) para aplicar autenticação e ACL no MQTT.

## Aulas

| Aula | Entrada principal | Conteúdo |
| --- | --- | --- |
| Aula 1 - Datasets | [Aula_1_datasets/README.md](Aula_1_datasets/README.md) | Inspeção de dataset de qualidade do ar, geração de artefatos, exportador Prometheus e dashboard Grafana. |
| Aula 2 - Séries temporais | [Aula_2_series_temporais/README.md](Aula_2_series_temporais/README.md) | Séries temporais e PromQL no Grafana, com datasource provisionado e dashboard criado pela API. |
| Aula 3 - Kafka | [Aula_3_kafka/README.md](Aula_3_kafka/README.md) | Producer e consumer Kafka para telemetria IoT, partitions, offsets, lag, Prometheus e Grafana. |
| Aula 4 - MQTT para Kafka | [Aula_4_esp32_mqtt_kafka/README.md](Aula_4_esp32_mqtt_kafka/README.md) | Ponte MQTT -> Kafka com Mosquitto, firmware ESP32 (DHT22 + MQ-7) e reaproveitamento do tópico da Aula 3. |
| Aula 5 - Orquestração | [Aula_5_orquestração/README.md](Aula_5_orquestração/README.md) | Stack IoT local com Docker Compose, observabilidade e manifests Kubernetes didáticos. |
| Aula 6 - Segurança e Governança | [Aula_6_seguranca_governanca/README.md](Aula_6_seguranca_governanca/README.md) | Autenticação MQTT, ACL por tópico e Grafana como camada de governança. |

## Extras

Materiais complementares, fora da sequência numerada de aulas.

| Extra | Entrada principal | Conteúdo |
| --- | --- | --- |
| Filas, Escalonamento e Escalabilidade | [Extras/Escalonamento_e_filas/pratica_filas_escalonamento_usl.ipynb](Extras/Escalonamento_e_filas/pratica_filas_escalonamento_usl.ipynb) | Notebook de prática de uma monitoria do curso: divisão estática x fila dinâmica, diagramas de Gantt, métricas de desempenho e a Universal Scalability Law, mais um benchmark (`benchmark_filas_cpu.py`) com processos reais. |
| Hands-On Observabilidade e Resiliência em IoT | [Extras/Hands_On_Observability_Resilience_IoT/README.md](Extras/Hands_On_Observability_Resilience_IoT/README.md) | Laboratório em Docker Compose: publisher e consumer MQTT com fila interna limitada, Prometheus e Grafana (dashboard provisionado). Dois experimentos guiados: indisponibilidade do broker e sobrecarga do consumidor (backpressure). Inclui slides de apoio de uma monitoria do curso. |

## Estrutura

```text
M3/
├── Aula_1_datasets/
│   ├── data/
│   ├── docker/
│   ├── outputs_example/
│   └── scripts/
├── Aula_2_series_temporais/
│   ├── dashboard/
│   ├── grafana/provisioning/
│   ├── prometheus/
│   └── docker-compose.yml
├── Aula_3_kafka/
│   ├── docker/
│   └── scripts/
├── Aula_4_esp32_mqtt_kafka/
│   ├── docker/
│   ├── firmware/
│   ├── mosquitto/
│   ├── scripts/
│   └── docker-compose.yml
├── Aula_5_orquestração/
│   ├── k8s/
│   ├── services/
│   ├── docs/
│   └── docker-compose.yaml
└── Aula_6_seguranca_governanca/
    ├── mosquitto/
    ├── grafana/
    └── docker-compose.yml
```

## Serviços e portas comuns

| Serviço | Porta padrão | Onde aparece |
| --- | --- | --- |
| Exportador Prometheus da Aula 1 | `8000` | `Aula_1_datasets/docker` (serviço `exporter`) |
| Prometheus | `9090` | Aulas 1, 2, 3 e 5 |
| Grafana | `3000` | Aulas 1, 2, 3 e 5 |
| Kafka (listener do host) | `29092` | Aulas 3, 4 e 5 |
| Kafka UI | `8080` | Aula 5 |
| Mosquitto (MQTT) | `1883` | Aulas 4 e 5 |
| Métricas do consumer Kafka | dinâmica (`docker compose port consumer 8000`) | Aula 3 |

> A [Aula 6](Aula_6_seguranca_governanca/README.md) desloca as portas no host
> (`20202`/`20203` para MQTT e `9001` para o Grafana) para evitar conflito com
> outras práticas. Consulte sempre o README da aula antes de subir os serviços.

Se duas práticas forem executadas ao mesmo tempo, verifique conflitos de portas antes de subir os serviços — os READMEs indicam como parar cada stack (`docker compose down`).

## Fluxo geral do módulo

```text
Dataset IoT / sensores
  -> inspeção e normalização        (Aula 1)
  -> métricas Prometheus            (Aula 1)
  -> visualização Grafana           (Aula 2)
  -> eventos Kafka                  (Aula 3)
  -> ponte MQTT -> Kafka            (Aula 4)
  -> orquestração Compose/K8s       (Aula 5)
  -> segurança e governança MQTT    (Aula 6)
```

## Requisitos gerais

- Docker com Docker Compose v2.
- Git para clonar o repositório.
- Navegador para Prometheus, Grafana e Kafka UI.
- Opcional: Python 3.10+ com `venv`, para executar os scripts das práticas fora dos containers (cada `scripts/README.md` explica como).
- Para a parte Kubernetes da Aula 5: `kubectl` e um cluster local (Docker Desktop, Minikube, K3s) ou playground online.
