# Prática 5 - Orquestração com Docker Compose, Kubernetes e IoT

Esta prática sobe uma stack IoT completa com Docker Compose e depois executa a mesma stack, em leitura simplificada e didática, no Kubernetes. Tudo roda localmente: Docker para o Compose e um cluster local (Docker Desktop, Minikube ou K3s) ou playground online para o Kubernetes.

## 1. Objetivo da prática

Ao final da prática, você deve conseguir:

- subir uma arquitetura IoT completa com Docker Compose;
- observar mensagens passando de MQTT para Kafka e eventos consumidos com Python;
- expor métricas Prometheus e visualizar os dados no Grafana;
- relacionar os mesmos componentes com Deployments, Services e ConfigMaps no Kubernetes;
- observar no Kubernetes a escala de réplicas, a recriação de Pods (reconciliação) e a diferença entre mudanças imperativas e declarativas.

## 2. Conceitos da prática

### Arquitetura

A mesma cadeia é executada nas duas plataformas:

```text
sensor-simulator
  -> Mosquitto MQTT
  -> mqtt-to-kafka
  -> Kafka
  -> iot-processor
  -> Prometheus
  -> Grafana
```

O Kafka UI também é incluído para inspecionar tópicos, mensagens e broker.

### Orquestração

O **Docker Compose** descreve e sobe um conjunto de containers em uma máquina: rede, volumes, ordem de subida (`depends_on`) e healthchecks. O **Kubernetes** generaliza a ideia para um cluster: você declara o estado desejado (Deployments, Services, ConfigMaps) e o cluster **reconcilia** o estado real com o declarado — recriando Pods que morrem, balanceando tráfego pelos Services e aplicando mudanças por rolling update. A tabela de equivalências Compose ↔ Kubernetes, conceito a conceito, está no [roteiro Kubernetes](docs/kubernetes-pratica.md#do-compose-para-o-kubernetes).

### Imagens e serviços

Os três serviços Python da stack são construídos a partir de [services/](services/):

```text
opaiot/sensor-simulator:local
opaiot/mqtt-to-kafka:local
opaiot/iot-processor:local
```

No Compose, o `build` acontece no `up`. No Kubernetes, você constrói as imagens e as disponibiliza ao cluster antes de aplicar os manifests — o [roteiro Kubernetes](docs/kubernetes-pratica.md#3-construir-as-imagens-dos-apps) traz os comandos para cada ambiente.

### Portas (Docker Compose)

| Serviço | Porta no host | Uso |
| --- | --- | --- |
| Mosquitto | `1883` | MQTT local de laboratório |
| Kafka | `29092` | listener para clientes executados no host |
| Kafka UI | `8080` | interface web para Kafka |
| iot-processor | `8000` | endpoint `/metrics` |
| Prometheus | `9090` | consultas PromQL e targets |
| Grafana | `3000` | dashboard IoT, `admin/admin` |

No Docker Compose, use `kafka:9092` entre containers e `localhost:29092` para ferramentas no host. No Kubernetes, o acesso às interfaces é por `kubectl port-forward` (ou NodePorts `30080`/`30090`/`30300`).

## 3. Prática passo a passo

A prática tem duas partes, cada uma com roteiro próprio e detalhado:

1. **[Roteiro Docker Compose](docs/docker-compose-pratica.md)** — suba a stack, observe os logs de sensor, ponte e processador, teste MQTT e Kafka pelo terminal, explore Kafka UI, Prometheus e o dashboard do Grafana, escale o sensor e encerre.
2. **[Roteiro Kubernetes](docs/kubernetes-pratica.md)** — execute a mesma stack em um cluster: conceitos (Deployment → ReplicaSet → Pod, labels, Services), construção das imagens por ambiente, aplicação dos manifests, verificação ponta a ponta, escala, reconciliação, imperativo x declarativo e remoção. Inclui diagnóstico e perguntas de verificação com gabarito.

Início rápido da parte Compose:

```bash
cd M3/Aula_5_orquestração
docker compose up --build -d
docker compose logs -f --tail=50 sensor-simulator mqtt-to-kafka iot-processor
```

Acessos: Kafka UI em <http://localhost:8080>, Prometheus em <http://localhost:9090>, Grafana em <http://localhost:3000> (`admin`/`admin`, dashboard em `/d/iot-local-telemetry`), métricas em <http://localhost:8000/metrics>.

Para encerrar:

```bash
docker compose down      # mantém volumes
docker compose down -v   # remove volumes da prática
```

> Pare a stack do Compose antes de iniciar a parte Kubernetes: as duas usam as mesmas portas locais.

A pasta [k8s/](k8s/README.md) documenta cada manifest, as versões das imagens e as simplificações de laboratório (Kafka sem persistência, sem resources, senha em texto puro).

## 4. Sugestão de exercícios sobre a prática

1. **Equivalências.** Para cada serviço do [docker-compose.yaml](docker-compose.yaml), aponte o recurso correspondente em [k8s/](k8s/) e o que **não** tem equivalente direto (por exemplo, `depends_on` e o job `kafka-init`). Use a tabela do roteiro Kubernetes como gabarito.
2. **Escala nos dois mundos.** Escale o sensor para 3 réplicas no Compose (`docker compose up -d --scale sensor-simulator=3`) e no Kubernetes (`kubectl scale ... --replicas=3`). Compare: identidade de cada réplica, efeito na taxa de mensagens no Grafana e o que acontece com a escala após um novo `docker compose up` / `kubectl apply`.
3. **Falha de um componente.** No Compose, `docker compose stop kafka` por 1 minuto e observe os logs da ponte e do processador; depois `start`. No Kubernetes, apague o Pod do Kafka. O que cada plataforma recupera sozinha, e o que se perde em cada caso (dica: volume nomeado x `emptyDir`)?
4. **Declarativo.** No Kubernetes, faça a mudança de `PUBLISH_INTERVAL` editando o YAML e aplicando (passo 12 do roteiro). Depois responda: por que `kubectl set env` seria desfeito pelo próximo `kubectl apply -f k8s/`? Onde fica a "fonte da verdade" em cada plataforma?
5. **Perguntas de verificação.** Responda às seis perguntas do fim do [roteiro Kubernetes](docs/kubernetes-pratica.md#perguntas-de-verificação) antes de abrir o gabarito.
6. **Desafio.** Acrescente um segundo sensor **com Deployment próprio** no Kubernetes (por exemplo, `sensor-simulator-b` publicando em outro tópico MQTT) sem alterar os demais manifests. O que precisou mudar? O que o Service do Mosquitto garantiu de graça?
