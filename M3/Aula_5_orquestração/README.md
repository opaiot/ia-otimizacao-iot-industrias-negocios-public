# Aula 5 - Orquestração com Docker Compose, Kubernetes e IoT

Esta prática demonstra uma stack IoT local com Docker Compose e uma leitura equivalente, simplificada e didática, em Kubernetes.

## Objetivo

Ao final da prática, você deve conseguir:

- subir uma arquitetura IoT completa com Docker Compose;
- observar mensagens passando de MQTT para Kafka;
- consumir eventos Kafka com Python;
- expor métricas Prometheus;
- visualizar os dados no Grafana;
- relacionar os mesmos componentes com Deployments, Services e ConfigMaps no Kubernetes.

## Arquitetura

```text
sensor-simulator
  -> Mosquitto MQTT
  -> mqtt-to-kafka
  -> Kafka
  -> iot-processor
  -> Prometheus
  -> Grafana
```

O Kafka UI também é incluído no Docker Compose para inspecionar tópicos, mensagens e broker.

## Pré-requisitos

- Docker 20.10.4 ou superior.
- Docker Compose v2.
- Navegador para Kafka UI, Prometheus e Grafana.
- Para Kubernetes: `kubectl` e um cluster local ou playground como KillerCoda, Minikube ou K3s.

## Portas

| Serviço | Porta no host | Uso |
| --- | --- | --- |
| Mosquitto | `1883` | MQTT local de laboratório |
| Kafka | `29092` | listener para clientes executados no host |
| Kafka UI | `8080` | interface web para Kafka |
| iot-processor | `8000` | endpoint `/metrics` |
| Prometheus | `9090` | consultas PromQL e targets |
| Grafana | `3000` | dashboard IoT, `admin/admin` |

No Docker Compose, use `kafka:9092` entre containers. Use `localhost:29092` para ferramentas Kafka executadas diretamente no host.

## Como subir com Docker Compose

Entre no diretório da aula:

```bash
cd Modulo_3/Aula_5_orquestração
```

Suba a stack:

```bash
docker compose up --build -d
```

Acompanhe os logs principais:

```bash
docker compose logs -f --tail=50 sensor-simulator mqtt-to-kafka iot-processor
```

## Como acessar

- Kafka UI: <http://localhost:8080>
- Prometheus: <http://localhost:9090>
- Prometheus targets: <http://localhost:9090/targets>
- Grafana: <http://localhost:3000>
- Dashboard Grafana: <http://localhost:3000/d/iot-local-telemetry>
- Métricas do processador: <http://localhost:8000/metrics>

Credenciais didáticas do Grafana:

```text
usuário: admin
senha: admin
```

## Como encerrar

Pare os containers mantendo volumes:

```bash
docker compose down
```

Pare e remova volumes da prática:

```bash
docker compose down -v
```

## Kubernetes

A pasta `k8s/` contém manifests simples para namespace, Deployments, Services, ConfigMaps, Prometheus, Grafana e Kafka UI.

Os três serviços Python usam imagens locais:

```text
opaiot/sensor-simulator:local
opaiot/mqtt-to-kafka:local
opaiot/iot-processor:local
```

Antes de aplicar os manifests em Minikube, K3s ou KillerCoda, construa e carregue essas imagens conforme o runtime do ambiente. O roteiro Kubernetes mostra comandos e alternativas.

## Roteiros

- [Prática Docker Compose](docs/docker-compose-pratica.md)
- [Prática Kubernetes](docs/kubernetes-pratica.md)
- [README dos manifests Kubernetes](k8s/README.md)

## Progressão sugerida

1. Rode a stack local com Docker Compose.
2. Observe logs e mensagens MQTT.
3. Inspecione tópicos e eventos no Kafka UI.
4. Veja métricas em `/metrics` e no Prometheus.
5. Abra o dashboard do Grafana.
6. Leia os manifests Kubernetes comparando cada conceito com o Compose.
7. Aplique a versão Kubernetes em playground ou cluster local.
