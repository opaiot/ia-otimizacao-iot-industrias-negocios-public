# Roteiro - Kubernetes

Este roteiro usa os manifests de `k8s/` para comparar Docker Compose com Kubernetes em uma stack IoT simplificada.

## 1. Abrir o playground

Abra um ambiente como KillerCoda, Minikube ou K3s e envie esta pasta da prática para o ambiente.

Entre no diretório da aula:

```bash
cd Modulo_3/Aula_5_orquestração
```

## 2. Verificar nodes

```bash
kubectl get nodes
```

Para ver IPs e versão:

```bash
kubectl get nodes -o wide
```

## 3. Preparar imagens locais dos serviços Python

Os manifests usam imagens locais para os três apps Python:

```bash
docker build -t opaiot/sensor-simulator:local services/sensor-simulator
docker build -t opaiot/mqtt-to-kafka:local services/mqtt-to-kafka
docker build -t opaiot/iot-processor:local services/iot-processor
```

Em Minikube, carregue:

```bash
minikube image load opaiot/sensor-simulator:local
minikube image load opaiot/mqtt-to-kafka:local
minikube image load opaiot/iot-processor:local
```

Em K3s, uma alternativa comum é importar o tar:

```bash
docker save opaiot/sensor-simulator:local | sudo k3s ctr images import -
docker save opaiot/mqtt-to-kafka:local | sudo k3s ctr images import -
docker save opaiot/iot-processor:local | sudo k3s ctr images import -
```

Se o playground já compartilha o Docker local com o cluster, o carregamento extra pode não ser necessário.

## 4. Criar namespace

```bash
kubectl apply -f k8s/namespace.yaml
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/opaiot-p5 --timeout=60s
```

Verifique:

```bash
kubectl get ns opaiot-p5
```

## 5. Aplicar manifests

```bash
kubectl apply -f k8s/mosquitto.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/kafka-ui.yaml
kubectl apply -f k8s/sensor-simulator.yaml
kubectl apply -f k8s/mqtt-to-kafka.yaml
kubectl apply -f k8s/iot-processor.yaml
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml
```

O arquivo `k8s/alternativas/redpanda.yaml` é uma alternativa didática. Por padrão, use `kafka.yaml`; aplique Redpanda separadamente apenas se quiser trocar o broker.

Evite `kubectl apply -f k8s/` nesta prática. O diretório contém arquivos com funções diferentes e a aplicação em lote pode tentar criar recursos antes de o namespace estar pronto.

## 6. Listar Pods, Deployments e Services

```bash
kubectl get pods -n opaiot-p5
kubectl get deploy -n opaiot-p5
kubectl get svc -n opaiot-p5
```

Espere os Pods ficarem `Running`. Kafka pode levar mais tempo para ficar pronto.

## 7. Inspecionar um Pod

Liste os Pods:

```bash
kubectl get pods -n opaiot-p5
```

Descreva um deles:

```bash
kubectl describe pod <pod> -n opaiot-p5
```

Veja eventos, imagem, readiness probe e variáveis de ambiente.

## 8. Ver logs

Sensor:

```bash
kubectl logs deploy/sensor-simulator -n opaiot-p5
```

Ponte MQTT para Kafka:

```bash
kubectl logs deploy/mqtt-to-kafka -n opaiot-p5
```

Processador:

```bash
kubectl logs deploy/iot-processor -n opaiot-p5
```

Kafka:

```bash
kubectl logs deploy/kafka -n opaiot-p5
```

## 9. Testar Service interno

Assine mensagens MQTT dentro do cluster:

```bash
kubectl run mqtt-test \
  --rm -it \
  --restart=Never \
  -n opaiot-p5 \
  --image=eclipse-mosquitto:2 \
  -- mosquitto_sub -h mosquitto -t 'iot/+/telemetry' -C 3
```

Liste tópicos Kafka pelo Pod do broker:

```bash
kubectl exec deploy/kafka -n opaiot-p5 -- \
  /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --list
```

Consuma mensagens:

```bash
kubectl exec deploy/kafka -n opaiot-p5 -- \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.telemetry \
  --from-beginning \
  --max-messages 5
```

## 10. Acessar Grafana e Prometheus via NodePort

Liste Services:

```bash
kubectl get svc -n opaiot-p5
```

NodePorts usados:

```text
Prometheus: 30090
Grafana:    30300
Kafka UI:   30080
```

Descubra o IP de um node:

```bash
kubectl get nodes -o wide
```

Acesse:

```text
http://<node-ip>:30090
http://<node-ip>:30300
http://<node-ip>:30080
```

No Grafana, use `admin/admin`.

## 11. Escalar um Deployment

Escale sensores:

```bash
kubectl scale deployment sensor-simulator --replicas=3 -n opaiot-p5
```

Veja o resultado:

```bash
kubectl get pods -n opaiot-p5 -l app=sensor-simulator
kubectl logs deploy/sensor-simulator -n opaiot-p5 --tail=30
```

Volte para uma réplica:

```bash
kubectl scale deployment sensor-simulator --replicas=1 -n opaiot-p5
```

## 12. Apagar um Pod e observar reconciliação

Pegue o nome de um Pod:

```bash
kubectl get pods -n opaiot-p5
```

Apague:

```bash
kubectl delete pod <pod> -n opaiot-p5
```

Observe o Deployment recriando o Pod:

```bash
kubectl get pods -n opaiot-p5 -w
```

Use `Ctrl+C` para sair do modo watch.

## 13. Aplicar uma alteração

Altere o intervalo do sensor:

```bash
kubectl set env deployment/sensor-simulator PUBLISH_INTERVAL=1 -n opaiot-p5
```

Acompanhe o rollout:

```bash
kubectl rollout status deployment/sensor-simulator -n opaiot-p5
kubectl logs deploy/sensor-simulator -n opaiot-p5 --tail=30
```

Volte para 2 segundos:

```bash
kubectl set env deployment/sensor-simulator PUBLISH_INTERVAL=2 -n opaiot-p5
```

## 14. Remover recursos

Apague tudo pelo namespace:

```bash
kubectl delete namespace opaiot-p5
```

Verifique:

```bash
kubectl get ns opaiot-p5
```

## Relação entre Compose e Kubernetes

| Docker Compose | Kubernetes |
| --- | --- |
| `service` | `Deployment` para declarar réplicas e estado desejado; `Service` quando há tráfego de entrada |
| container | `Pod`, que encapsula um ou mais containers |
| `depends_on` | readiness, retries da aplicação, ordem lógica e reconciliação |
| `ports` | `Service`, `ClusterIP` e `NodePort` |
| `environment` | `env`, `ConfigMap` e `Secret` |
| `volumes` | `PersistentVolume`, `PersistentVolumeClaim`, `emptyDir` ou `ConfigMap` |

## Observações

- Esta versão usa Kafka single-node em KRaft. É boa para aula, não para produção.
- Os apps Python precisam de imagens locais ou de um registry acessível pelo cluster.
- Se Kafka ficar pesado no playground, use `k8s/alternativas/redpanda.yaml` como alternativa e ajuste `KAFKA_BOOTSTRAP_SERVERS` para `redpanda:9092`.
