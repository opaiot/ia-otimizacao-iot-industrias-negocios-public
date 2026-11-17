# Manifests Kubernetes - Aula 5

Manifests didáticos da stack IoT no namespace `opaiot-p5`. Esta página é só a **referência dos arquivos**. O passo a passo da prática, com preparação do ambiente, verificações e exercícios, está no [roteiro Kubernetes](../docs/kubernetes-pratica.md).

## Arquivos

| Arquivo | Recursos | O que observar |
| --- | --- | --- |
| `00-namespace.yaml` | Namespace `opaiot-p5` | O prefixo `00-` faz este arquivo ser aplicado primeiro em `kubectl apply -f k8s/`. |
| `grafana-dashboard.yaml` | ConfigMap `grafana-dashboards` | Cópia de `grafana/dashboards/iot-dashboard.json`, o mesmo dashboard do Compose. |
| `grafana.yaml` | ConfigMaps do datasource e do provider de dashboards, Deployment, Service `NodePort` 30300 | Provisionamento do Grafana feito só com ConfigMaps. |
| `iot-processor.yaml` | Deployment, Service `ClusterIP` 8000 | `readinessProbe` em `/metrics`. |
| `kafka-ui.yaml` | Deployment, Service `NodePort` 30080 | Lê o cluster por `kafka:9092`. |
| `kafka.yaml` | Deployment, Service `ClusterIP` 9092 | KRaft com um nó só, dados em `emptyDir` e heap limitado a 512 MB. |
| `mosquitto.yaml` | ConfigMap, Deployment, Service `ClusterIP` 1883 | `mosquitto.conf` vem de um ConfigMap. |
| `mqtt-to-kafka.yaml` | Deployment | Não tem Service, porque nada se conecta à ponte. |
| `prometheus.yaml` | ConfigMap, Deployment, Service `NodePort` 30090 | Coleta `iot-processor:8000` pelo nome do Service. |
| `sensor-simulator.yaml` | Deployment | `DEVICE_ID` vem do nome do Pod (Downward API): cada réplica é um dispositivo diferente. |
| `alternativas/redpanda.yaml` | Deployment `redpanda`, Service `kafka` | Substitui o `kafka.yaml`. Não é aplicado por `kubectl apply -f k8s/`. Veja a [alternativa Redpanda](../docs/kubernetes-pratica.md#alternativa-redpanda). |

## Aplicar e remover

Do diretório da aula, depois de preparar as imagens dos apps ([passo 3 do roteiro](../docs/kubernetes-pratica.md#3-construir-as-imagens-dos-apps)):

```bash
kubectl apply -f k8s/
kubectl wait --for=condition=Available deployment --all -n opaiot-p5 --timeout=300s
```

O `kubectl` aplica os arquivos de uma pasta em ordem alfabética e não entra em subpastas sem `-R`. Por isso o namespace vem antes de tudo e `alternativas/` fica de fora.

Para remover tudo:

```bash
kubectl delete namespace opaiot-p5
```

## Imagens

| Imagem | Origem |
| --- | --- |
| `opaiot/sensor-simulator:local`, `opaiot/mqtt-to-kafka:local`, `opaiot/iot-processor:local` | Construídas localmente a partir de `services/`. Usam `imagePullPolicy: Never`: o cluster nunca tenta baixá-las e, se a imagem não estiver no node, o Pod mostra `ErrImageNeverPull`. |
| `apache/kafka:4.0.0`, `prom/prometheus:v2.53.0`, `grafana/grafana:10.4.0`, `eclipse-mosquitto:2` | As mesmas versões do `docker-compose.yaml`. |
| `provectuslabs/kafka-ui:v0.7.2` | Última versão publicada do Kafka UI (o Compose usa `latest`). |
| `docker.redpanda.com/redpandadata/redpanda:v24.2.7` | Só na alternativa Redpanda. |

As versões ficam fixas para a aula ser reproduzível. Uma tag `latest` muda sem aviso, e a configuração do Kafka, por exemplo, muda entre versões.

## Acesso às interfaces

O caminho principal é `kubectl port-forward` ([passo 10 do roteiro](../docs/kubernetes-pratica.md#10-acessar-prometheus-grafana-e-kafka-ui)). Os Services das interfaces também são `NodePort`:

| Serviço | Porta do Service | NodePort |
| --- | --- | --- |
| Kafka UI | `8080` | `30080` |
| Prometheus | `9090` | `30090` |
| Grafana | `3000` | `30300` |

## Simplificações deste laboratório

Estes manifests priorizam a leitura e a comparação com o Compose. Não use assim em produção:

- **Kafka sem persistência.** É um Deployment com `emptyDir`: se o Pod for recriado, tópicos, mensagens e offsets se perdem. Em produção, use StatefulSet com PersistentVolumeClaim e mais de um broker.
- **Prometheus e Grafana sem volume.** O histórico de métricas e o que for criado pela interface do Grafana somem com o Pod. Datasource e dashboard voltam porque vêm de ConfigMaps.
- **Senha do Grafana em texto puro** no `env`. Em produção, use um Secret.
- **Sensor e ponte sem probes.** `Running` e `1/1` só dizem que o processo iniciou, não que as conexões com MQTT e Kafka funcionam.
- **Sem `resources` (requests e limits).** O scheduler não sabe quanto cada Pod precisa.
- **Interfaces expostas por `NodePort`, sem autenticação** (e MQTT anônimo). Em produção, use Ingress com TLS e autenticação.
- **Tópico criado automaticamente**, com 1 partição. No Compose, o `kafka-init` cria o tópico com 3 partições; em produção, crie tópicos explicitamente (Job ou operador).
- **Imagens dos apps sem registry.** Em produção, as imagens ficam em um registry, com tags versionadas.

## Alterar o dashboard

O dashboard está em dois lugares: `grafana/dashboards/iot-dashboard.json` (Compose) e `k8s/grafana-dashboard.yaml` (Kubernetes). Ao alterar o JSON, atualize o ConfigMap. Em Linux ou macOS, o comando abaixo gera o YAML novo (depois, recoloque o comentário do topo do arquivo):

```bash
kubectl create configmap grafana-dashboards -n opaiot-p5 \
  --from-file=grafana/dashboards/iot-dashboard.json \
  --dry-run=client -o yaml > k8s/grafana-dashboard.yaml
```
