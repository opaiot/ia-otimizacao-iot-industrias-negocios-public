# Kubernetes - Aula 5

Manifests didáticos para executar a stack IoT no namespace `opaiot-p5`.

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `namespace.yaml` | Namespace da prática |
| `mosquitto.yaml` | ConfigMap, Deployment e Service MQTT |
| `kafka.yaml` | Kafka single-node em KRaft |
| `kafka-ui.yaml` | Kafka UI via NodePort |
| `sensor-simulator.yaml` | Deployment do sensor Python |
| `mqtt-to-kafka.yaml` | Deployment da ponte MQTT para Kafka |
| `iot-processor.yaml` | Deployment e Service de métricas |
| `prometheus.yaml` | ConfigMap, Deployment e NodePort |
| `grafana.yaml` | Datasource, Deployment e NodePort |
| `alternativas/redpanda.yaml` | Broker alternativo leve para laboratório |

## Executar no Windows com Docker Desktop

Use este caminho quando estiver rodando a aula no Windows com Docker Desktop.

### 1. Habilitar Kubernetes

1. Abra o Docker Desktop.
2. Entre na área **Kubernetes**.
3. Crie/habilite um cluster Kubernetes.
4. Para esta prática, prefira o modo **Kubeadm** com um nó. É o caminho mais simples para usar imagens criadas com `docker build` no próprio Docker Desktop.

Em versões mais antigas do Docker Desktop, o caminho pode aparecer como **Settings > Kubernetes > Enable Kubernetes > Apply & Restart**.

### 2. Conferir o contexto do kubectl

No PowerShell:

```powershell
kubectl config get-contexts
kubectl config use-context docker-desktop
kubectl get nodes
```

O esperado é ver um node chamado `docker-desktop` com status `Ready`.

Se o comando `kubectl` não for encontrado, confirme que o Docker Desktop terminou a instalação do Kubernetes, reabra o PowerShell e confira se o comando entrou no `PATH`:

```powershell
where.exe kubectl
kubectl version --client
```

### 3. Entrar no diretório da aula

```powershell
cd ./opaIOT_2026/Modulo_3/Aula_5_orquestração
```

Se o repositório estiver em outro local, ajuste o caminho antes de continuar.

### 4. Construir as imagens locais

Os manifests usam imagens locais para os três serviços Python. No Docker Desktop, construa as imagens antes de aplicar os YAML:

```powershell
docker build -t opaiot/sensor-simulator:local .\services\sensor-simulator
docker build -t opaiot/mqtt-to-kafka:local .\services\mqtt-to-kafka
docker build -t opaiot/iot-processor:local .\services\iot-processor
```

Confira:

```powershell
docker images opaiot/*
```

### 5. Aplicar os manifests

```powershell
kubectl apply -f .\k8s\namespace.yaml
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/opaiot-p5 --timeout=60s

kubectl apply -f .\k8s\mosquitto.yaml
kubectl apply -f .\k8s\kafka.yaml
kubectl apply -f .\k8s\kafka-ui.yaml
kubectl apply -f .\k8s\sensor-simulator.yaml
kubectl apply -f .\k8s\mqtt-to-kafka.yaml
kubectl apply -f .\k8s\iot-processor.yaml
kubectl apply -f .\k8s\prometheus.yaml
kubectl apply -f .\k8s\grafana.yaml
```

Evite `kubectl apply -f .\k8s\` nesta prática. Esse comando pode aplicar os arquivos fora da ordem esperada e, dependendo do ambiente, tentar criar recursos namespaced antes de o namespace `opaiot-p5` estar pronto.

Verifique os recursos:

```powershell
kubectl get pods -n opaiot-p5
kubectl get deploy -n opaiot-p5
kubectl get svc -n opaiot-p5
```

### 6. Acessar as interfaces

No Docker Desktop, os `NodePort` desta prática podem ser acessados pelo `localhost`:

```text
Kafka UI:   http://localhost:30080
Prometheus: http://localhost:30090
Grafana:    http://localhost:30300
```

No Grafana, use `admin/admin`.

### 7. Ver logs principais

```powershell
kubectl logs deploy/sensor-simulator -n opaiot-p5
kubectl logs deploy/mqtt-to-kafka -n opaiot-p5
kubectl logs deploy/iot-processor -n opaiot-p5
```

Para acompanhar em tempo real:

```powershell
kubectl logs -f deploy/iot-processor -n opaiot-p5
```

### 8. Diagnóstico rápido

Se algum Pod ficar com `ImagePullBackOff`, confirme que as imagens locais existem:

```powershell
docker images opaiot/*
kubectl describe pod <pod> -n opaiot-p5
```

Se o Kafka ficar pesado no Docker Desktop, use a alternativa Redpanda:

```powershell
kubectl delete -f .\k8s\kafka.yaml
kubectl apply -f .\k8s\alternativas\redpanda.yaml
kubectl set env deployment/mqtt-to-kafka KAFKA_BOOTSTRAP_SERVERS=redpanda:9092 -n opaiot-p5
kubectl set env deployment/iot-processor KAFKA_BOOTSTRAP_SERVERS=redpanda:9092 -n opaiot-p5
```

Se quiser começar do zero:

```powershell
kubectl delete namespace opaiot-p5
```

## Preparar imagens dos apps

```bash
docker build -t opaiot/sensor-simulator:local services/sensor-simulator
docker build -t opaiot/mqtt-to-kafka:local services/mqtt-to-kafka
docker build -t opaiot/iot-processor:local services/iot-processor
```

Em Minikube:

```bash
minikube image load opaiot/sensor-simulator:local
minikube image load opaiot/mqtt-to-kafka:local
minikube image load opaiot/iot-processor:local
```

## Aplicar

```bash
kubectl apply -f k8s/namespace.yaml
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/opaiot-p5 --timeout=60s
kubectl apply -f k8s/mosquitto.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/kafka-ui.yaml
kubectl apply -f k8s/sensor-simulator.yaml
kubectl apply -f k8s/mqtt-to-kafka.yaml
kubectl apply -f k8s/iot-processor.yaml
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml
```

## Listar

```bash
kubectl get pods -n opaiot-p5
kubectl get deploy -n opaiot-p5
kubectl get svc -n opaiot-p5
```

## Logs

```bash
kubectl logs deploy/sensor-simulator -n opaiot-p5
kubectl logs deploy/mqtt-to-kafka -n opaiot-p5
kubectl logs deploy/iot-processor -n opaiot-p5
```

## Inspecionar

```bash
kubectl describe pod <pod> -n opaiot-p5
```

## Escalar

```bash
kubectl scale deployment sensor-simulator --replicas=3 -n opaiot-p5
kubectl get pods -n opaiot-p5 -l app=sensor-simulator
```

## Remover

```bash
kubectl delete namespace opaiot-p5
```

## NodePorts

| Serviço | NodePort |
| --- | --- |
| Kafka UI | `30080` |
| Prometheus | `30090` |
| Grafana | `30300` |

## Alternativa Redpanda

Se o Kafka oficial ficar pesado no playground:

```bash
kubectl delete -f k8s/kafka.yaml
kubectl apply -f k8s/alternativas/redpanda.yaml
kubectl set env deployment/mqtt-to-kafka KAFKA_BOOTSTRAP_SERVERS=redpanda:9092 -n opaiot-p5
kubectl set env deployment/iot-processor KAFKA_BOOTSTRAP_SERVERS=redpanda:9092 -n opaiot-p5
```

Depois acompanhe:

```bash
kubectl rollout status deployment/mqtt-to-kafka -n opaiot-p5
kubectl rollout status deployment/iot-processor -n opaiot-p5
```
