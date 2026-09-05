# Módulo 3 - Dados, Observabilidade e Eventos

Este módulo reúne as práticas do OpAIoT 2026 voltadas ao tratamento de dados IoT, séries temporais, observabilidade com Prometheus/Grafana e processamento de telemetria com Apache Kafka.

As atividades foram pensadas para execução na VM Linux conteinerizada disponibilizada na nuvem privada LASDPC. Quando houver suporte local, a própria aula traz arquivos Docker ou Docker Compose para reproduzir o ambiente fora da VM.

## Ordem sugerida

1. Comece pela [Aula 1 - Datasets](Aula_1_datasets/README.md) para inspecionar um CSV de sensores, normalizar eventos IoT e expor métricas Prometheus.
2. Use a [Aula 2 - Séries Temporais](Aula_2_series_temporais/README.md) como ambiente de apoio para Grafana com datasource Prometheus provisionado.
3. Avance para a [Aula 3 - Kafka](Aula_3_kafka/README.md) para produzir, consumir e observar eventos IoT em um tópico Kafka.
4. Conecte telemetria MQTT ao Kafka na [Aula 4 - MQTT para Kafka](Aula_4_esp32_mqtt_kafka/README.md), reaproveitando o tópico da Aula 3.
5. Compare a stack IoT em Docker Compose e Kubernetes na [Aula 5 - Orquestração](Aula_5_orquestração/README.md).
6. Feche com a [Aula 6 - Segurança e Governança](Aula_6_seguranca_governanca/README.md) para aplicar autenticação e ACL no MQTT.

## Aulas

| Aula | Entrada principal | Conteúdo |
| --- | --- | --- |
| Aula 1 - Datasets | [Aula_1_datasets/README.md](Aula_1_datasets/README.md) | Inspeção de dataset de qualidade do ar, geração de artefatos, exportador Prometheus e dashboard Grafana. |
| Aula 2 - Séries temporais | [Aula_2_series_temporais/README.md](Aula_2_series_temporais/README.md) | Uso do Grafana com roteiro para VM e alternativa com Docker local. |
| Aula 3 - Kafka | [Aula_3_kafka/README.md](Aula_3_kafka/README.md) | Producer e consumer Kafka para telemetria IoT, partitions, offsets, lag, Prometheus e Grafana. |
| Aula 4 - MQTT para Kafka | [Aula_4_esp32_mqtt_kafka/README.md](Aula_4_esp32_mqtt_kafka/README.md) | Ponte MQTT -> Kafka com Mosquitto, firmware ESP32 (DHT22 + MQ-7) e reaproveitamento do tópico da Aula 3. |
| Aula 5 - Orquestração | [Aula_5_orquestração/README.md](Aula_5_orquestração/README.md) | Stack IoT local com Docker Compose, observabilidade e manifests Kubernetes didáticos. |
| Aula 6 - Segurança e Governança | [Aula_6_seguranca_governanca/README.md](Aula_6_seguranca_governanca/README.md) | Autenticação MQTT, ACL por tópico e Grafana como camada de governança. |

## Estrutura

```text
Modulo_3/
├── Aula_1_datasets/
│   ├── data/
│   ├── docker/
│   ├── outputs_example/
│   └── scripts/
├── Aula_2_series_temporais/
│   ├── docker-compose.yml
│   └── grafana/provisioning/
├── Aula_3_kafka/
│   ├── docker/
│   ├── scripts/
│   ├── README.md
│   └── instalando_kafka_vm.md
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

## Ambientes de execução

### VM Linux LASDPC

Use este caminho quando a aula pedir execução na infraestrutura do curso. As práticas documentam os comandos para acessar a VM via SSH, preparar Python, instalar dependências e configurar Prometheus/Grafana.

Entradas úteis:

| Tema | Arquivo |
| --- | --- |
| Aula 1 na VM | [Aula_1_datasets/README.md](Aula_1_datasets/README.md) |
| Instalação do Kafka | [Aula_3_kafka/instalando_kafka_vm.md](Aula_3_kafka/instalando_kafka_vm.md) |
| Scripts Kafka | [Aula_3_kafka/scripts/README.md](Aula_3_kafka/scripts/README.md) |

### Docker local

Use este caminho para executar os serviços de apoio em uma máquina com Docker instalado.

Entradas úteis:

| Tema | Arquivo |
| --- | --- |
| Aula 1 com Docker | [Aula_1_datasets/docker/README.md](Aula_1_datasets/docker/README.md) |
| Aula 2 com Docker local | [Aula_2_series_temporais/README.md](Aula_2_series_temporais/README.md) |
| Aula 3 com Docker | [Aula_3_kafka/docker/README.md](Aula_3_kafka/docker/README.md) |
| Aula 4 ponte MQTT -> Kafka | [Aula_4_esp32_mqtt_kafka/README.md](Aula_4_esp32_mqtt_kafka/README.md) |
| Aula 5 stack completa (Compose + Kubernetes) | [Aula_5_orquestração/README.md](Aula_5_orquestração/README.md) |
| Aula 6 segurança MQTT | [Aula_6_seguranca_governanca/README.md](Aula_6_seguranca_governanca/README.md) |

## Serviços e portas comuns

| Serviço | Porta padrão | Onde aparece |
| --- | --- | --- |
| Exportador Prometheus da Aula 1 | `8000` | `Aula_1_datasets/scripts/2-prometheus.py` |
| Prometheus | `9090` | Aulas 1, 3 e 5 |
| Grafana | `3000` | Aulas 1, 2, 3 e 5 |
| Kafka | `9092` / `29092` | Aulas 3, 4 e 5 |
| Kafka UI | `8080` | Aula 5 |
| Mosquitto (MQTT) | `1883` | Aulas 4 e 6 |
| Métricas dos consumers Kafka | `8000`, `8001`, `8002`, `8003` | Aula 3 |

> A [Aula 6](Aula_6_seguranca_governanca/README.md) desloca as portas no host
> (`20202`/`20203` para MQTT e `9001` para o Grafana) para evitar conflito com
> outras práticas. Consulte sempre o README da aula antes de subir os serviços.

Se duas práticas forem executadas ao mesmo tempo, verifique conflitos de portas antes de subir os serviços.

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

- Acesso à VM Linux do curso ou a uma máquina local com Docker.
- Git para clonar o repositório.
- Python 3 e `venv` para executar os scripts das práticas.
- Docker e Docker Compose para os ambientes locais.
- Navegador para acessar Prometheus e Grafana.

Cada aula detalha suas próprias dependências e comandos de execução. Use este README como índice do módulo e siga o README específico da aula antes de executar a prática.
