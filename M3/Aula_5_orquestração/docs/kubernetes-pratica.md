# Roteiro - Kubernetes

Este roteiro executa no Kubernetes a mesma stack IoT da [prática com Docker Compose](docker-compose-pratica.md) e usa a comparação entre as duas para apresentar os conceitos centrais do Kubernetes. Os manifests estão em [`k8s/`](../k8s/), e o [README dos manifests](../k8s/README.md) resume o que cada arquivo contém.

> **Onde rodar:** esta prática roda **na sua máquina** (Docker Desktop, Minikube ou K3s) ou em um **playground online**. Veja o [passo 3](#3-construir-as-imagens-dos-apps).

## Objetivos

Ao final da prática, você deve conseguir:

- explicar a cadeia **Deployment → ReplicaSet → Pod** e por que um Pod apagado volta sozinho;
- usar **labels e selectors** para encontrar Pods e entender como um Service escolhe para onde enviar tráfego;
- distinguir um Pod `Running` de um Pod **pronto** (`READY`) e comprovar que os dados atravessam a stack de ponta a ponta;
- escalar um Deployment e medir o efeito no fluxo de mensagens;
- diferenciar uma mudança **imperativa** (`kubectl scale`, `kubectl set env`) de uma **declarativa** (editar o YAML e rodar `kubectl apply`);
- acessar serviços do cluster com `kubectl port-forward`;
- reconhecer o que se perde quando um Pod sem volume persistente é recriado.

## Arquitetura no cluster

Tudo roda no namespace `opaiot-p5`. Cada seta passa por um **Service**: nenhum Pod se conecta ao IP de outro Pod.

```text
sensor-simulator   Deployment, 1 Pod; publica em iot/<device_id>/telemetry
   │ MQTT
   ▼
mosquitto          Service mosquitto:1883  → Pod do broker MQTT
   │ assinatura iot/+/telemetry
   ▼
mqtt-to-kafka      Deployment, 1 Pod; produz no tópico iot.telemetry
   │ Kafka
   ▼
kafka              Service kafka:9092      → Pod do broker     ◀── kafka-ui (Service NodePort 30080)
   │ consome com group_id iot-processor
   ▼
iot-processor      Service iot-processor:8000 → Pod; expõe /metrics
   ▲ coleta a cada 5 s
prometheus         Service prometheus:9090 (NodePort 30090)
   ▲ consultas PromQL
grafana            Service grafana:3000    (NodePort 30300); dashboard provisionado
```

## Conceitos usados no roteiro

**Pod.** A menor unidade que o Kubernetes executa: um ou mais containers que compartilham rede e volumes. Nesta prática, cada Pod tem um container. Pods são descartáveis: quando um some, outro com **nome e IP diferentes** toma o lugar dele.

**Deployment → ReplicaSet → Pod.** Você não cria Pods diretamente. Você declara um Deployment ("quero N réplicas deste template de Pod"). O Deployment cria um ReplicaSet para cada versão do template, e o ReplicaSet mantém o número de Pods igual ao desejado:

```text
Deployment  sensor-simulator                      você declara: 1 réplica deste template
 └── ReplicaSet  sensor-simulator-d7486454f       uma por versão do template (o sufixo é um hash do template)
      └── Pod    sensor-simulator-d7486454f-274q7 o container em execução (sufixo aleatório)
```

O nome do Pod conta essa história: `<deployment>-<hash do template>-<sufixo>`. Esse ciclo de comparar o desejado com o real e corrigir a diferença se chama **reconciliação**. É ele que recria um Pod apagado ([passo 13](#13-apagar-pods-e-observar-a-reconciliação)).

**Labels e selectors.** Labels são pares chave/valor presos aos objetos. Selectors são filtros sobre essas labels. Em `k8s/iot-processor.yaml`, o mesmo par `app: iot-processor` aparece três vezes:

```yaml
# Deployment: "os meus Pods são os que têm app=iot-processor"
  selector:
    matchLabels:
      app: iot-processor
  template:
    metadata:
      labels:
        app: iot-processor     # todo Pod criado a partir do template recebe esta label
---
# Service: "envio tráfego para os Pods prontos que têm app=iot-processor"
spec:
  selector:
    app: iot-processor
```

Você vai usar o mesmo filtro na linha de comando: `kubectl get pods -l app=iot-processor`.

**Service.** Um nome DNS e um IP virtual **estáveis** na frente de um grupo de Pods, com balanceamento entre eles. O tipo padrão, `ClusterIP`, só é acessível **de dentro** do cluster. O tipo `NodePort` também abre uma porta (30000 a 32767) em todos os nodes. O Service existe para que os outros componentes não precisem saber nomes nem IPs de Pods, que mudam a cada recriação.

**Namespace.** Um espaço de nomes dentro do cluster. Todos os recursos desta prática ficam em `opaiot-p5`, por isso quase todo comando leva `-n opaiot-p5`. Apagar o namespace apaga tudo de uma vez.

**ConfigMap.** Configuração guardada no cluster e montada nos Pods como arquivo ou como variável. Aqui ela substitui os bind mounts do Compose: `mosquitto.conf`, `prometheus.yml` e o datasource e o dashboard do Grafana.

### Do Compose para o Kubernetes

| No Docker Compose | No Kubernetes | Nesta prática |
| --- | --- | --- |
| um `service` com `image` ou `build` | **Deployment**: o template do Pod e o número de réplicas. Ele cria um ReplicaSet, que cria os Pods. | um Deployment por componente |
| o nome do `service` como endereço na rede (`kafka:9092`) | **Service** do tipo `ClusterIP` (o padrão): nome DNS estável e balanceamento entre os Pods com a label do `selector`, **dentro** do cluster | `kafka`, `mosquitto`, `iot-processor`, ... O sensor e a ponte não têm Service porque nada se conecta a eles. |
| container | container dentro de um **Pod** (um Pod pode ter mais de um container) | um container por Pod |
| `ports: "9090:9090"` (publicar no host) | Service do tipo **`NodePort`** (porta aberta em todos os nodes), `LoadBalancer` ou Ingress; para acesso pontual, **`kubectl port-forward`** | NodePorts `30080`, `30090` e `30300`, e `port-forward` como caminho principal |
| `depends_on` com `condition` | **não há equivalente direto.** O Kubernetes sobe todos os Pods em paralelo, e cada aplicação precisa tentar de novo até a dependência responder. A `readinessProbe` **não ordena a subida**: ela só decide quando o Pod passa a receber tráfego do Service. | os apps Python repetem a conexão com MQTT e Kafka até conseguir |
| `healthcheck` | `readinessProbe` (pronto para receber tráfego) e `livenessProbe` (reinicia o container se travar) | readiness em Kafka, Mosquitto e `iot-processor` |
| `restart: unless-stopped` | **reconciliação**: o kubelet reinicia containers que caem e o ReplicaSet recria Pods que somem | [passo 13](#13-apagar-pods-e-observar-a-reconciliação) |
| `docker compose up --scale` | `kubectl scale` (imperativo) ou `replicas:` no YAML (declarativo) | passos [11](#11-escalar-o-sensor) e [12](#12-imperativo-x-declarativo) |
| `environment` | `env`, ConfigMap ou Secret | `env` direto nos Deployments |
| bind mount de arquivo de configuração | **ConfigMap** montado como volume | Mosquitto, Prometheus e Grafana |
| volume nomeado (`kafka-data:`) | **PersistentVolumeClaim**, normalmente com **StatefulSet** | **não usado**: o Kafka grava em `emptyDir`, que some junto com o Pod ([passo 13](#13-apagar-pods-e-observar-a-reconciliação)) |
| serviço de inicialização (`kafka-init`) | Job ou `initContainer` | não usado: o tópico é criado na primeira mensagem, com 1 partição (no Compose são 3) |
| `networks` | uma rede única para o cluster; o namespace separa os nomes | namespace `opaiot-p5` |

## Antes de começar

- **Comandos com `\` no fim da linha** são para bash (Linux, macOS, Git Bash). No PowerShell, escreva o comando em uma linha só.
- Em vários passos você vai precisar de **mais de um terminal**, por exemplo um com `kubectl port-forward` e outro para os comandos.
- Se a stack do Docker Compose desta aula estiver no ar, pare-a antes com `docker compose down`: o `port-forward` do passo 10 usa as mesmas portas locais (`9090`, `3000` e `8080`).

## 1. Obter os arquivos

Clone o repositório no ambiente onde está o `kubectl`:

```bash
git clone https://github.com/opaiot/ia-otimizacao-iot-industrias-negocios-public.git
cd ia-otimizacao-iot-industrias-negocios-public/M3/Aula_5_orquestra*
```

O `*` evita digitar `ção` no nome da pasta e funciona no bash e no PowerShell. Todos os comandos a seguir partem desse diretório. Confira:

```bash
ls k8s
```

Você deve ver `00-namespace.yaml`, `grafana.yaml`, `kafka.yaml`, ..., `sensor-simulator.yaml` e a pasta `alternativas`.

## 2. Conferir o cluster

Confirme para qual cluster o `kubectl` aponta e se os nodes estão prontos:

```bash
kubectl config current-context
kubectl get nodes
```

Saída esperada no Docker Desktop (nome, idade e versão variam conforme o ambiente):

```text
NAME             STATUS   ROLES           AGE   VERSION
docker-desktop   Ready    control-plane   12m   v1.32.2
```

O que importa é `STATUS` igual a `Ready`. Anote **quantos nodes** existem: isso importa no próximo passo. Para ver IPs e o runtime de containers de cada node, use `kubectl get nodes -o wide`.

## 3. Construir as imagens dos apps

Kafka, Mosquitto, Prometheus, Grafana e Kafka UI usam imagens públicas, que o cluster baixa sozinho. Os três apps Python usam imagens construídas por você:

```text
opaiot/sensor-simulator:local
opaiot/mqtt-to-kafka:local
opaiot/iot-processor:local
```

Esses manifests usam `imagePullPolicy: Never`: o cluster **não tenta baixar** essas imagens de nenhum registry. A imagem precisa existir no runtime de containers do node onde o Pod vai rodar. Se não existir, o Pod fica em `ErrImageNeverPull`. Escolha o seu ambiente:

### Docker Desktop (Windows ou macOS)

1. Em **Settings > Kubernetes**, habilite o Kubernetes. Se houver escolha de tipo de cluster, prefira **kubeadm** com um node: nesse modo, o cluster enxerga as imagens criadas com `docker build`.
2. Selecione o contexto e construa as imagens:

```bash
kubectl config use-context docker-desktop
docker build -t opaiot/sensor-simulator:local services/sensor-simulator
docker build -t opaiot/mqtt-to-kafka:local services/mqtt-to-kafka
docker build -t opaiot/iot-processor:local services/iot-processor
docker images "opaiot/*"
```

Se o PowerShell não encontrar `kubectl`, confira se a instalação do Kubernetes terminou, reabra o terminal e teste com `where.exe kubectl`.

### Minikube

Construa as imagens direto dentro do Minikube:

```bash
minikube start --memory=4096
minikube image build -t opaiot/sensor-simulator:local services/sensor-simulator
minikube image build -t opaiot/mqtt-to-kafka:local services/mqtt-to-kafka
minikube image build -t opaiot/iot-processor:local services/iot-processor
minikube image ls | grep opaiot
```

Se as imagens já existirem no Docker da sua máquina, `minikube image load opaiot/sensor-simulator:local` (e o mesmo para as outras duas) também resolve.

### K3s (Linux)

O K3s usa containerd, não o Docker. Construa com Docker e importe no K3s:

```bash
docker build -t opaiot/sensor-simulator:local services/sensor-simulator
docker build -t opaiot/mqtt-to-kafka:local services/mqtt-to-kafka
docker build -t opaiot/iot-processor:local services/iot-processor
docker save opaiot/sensor-simulator:local | sudo k3s ctr images import -
docker save opaiot/mqtt-to-kafka:local | sudo k3s ctr images import -
docker save opaiot/iot-processor:local | sudo k3s ctr images import -
```

### Playground online (KillerCoda e similares)

Antes de começar, confira duas coisas: quantos nodes o cluster tem (`kubectl get nodes`) e se há Docker (`docker version`).

- **Um node, com Docker e containerd:** construa como no K3s e importe com `docker save opaiot/sensor-simulator:local | sudo ctr -n k8s.io images import -` (e o mesmo para as outras duas).
- **Mais de um node:** a imagem precisa existir em **cada** node onde os Pods podem ser agendados, e importar só em um deles não basta. Sem Docker, não há como construir as imagens no playground. Nesses casos, prefira Docker Desktop ou Minikube.

## 4. Ler os manifests antes de aplicar

Abra `k8s/iot-processor.yaml` e `k8s/sensor-simulator.yaml` no editor e localize:

1. `replicas`, o número de Pods desejado;
2. a label em `template.metadata.labels` e o `selector` do Deployment e do Service, que precisam bater;
3. a `readinessProbe` do `iot-processor`, que testa `/metrics`;
4. no sensor, o `DEVICE_ID`, que vem de `fieldRef: metadata.name` (a **Downward API**). Cada Pod usa o **próprio nome** como identificador de dispositivo. Isso vai importar quando você escalar o sensor.

## 5. Aplicar os manifests

```bash
kubectl apply -f k8s/
```

O `kubectl` lê os arquivos da pasta em **ordem alfabética**. O prefixo de `00-namespace.yaml` garante que o namespace seja criado antes dos recursos que dependem dele. A subpasta `alternativas/` **não** é aplicada, porque o `kubectl` só entra em subpastas com `-R`. Saída esperada (resumida):

```text
namespace/opaiot-p5 created
configmap/grafana-dashboards created
configmap/grafana-datasources created
configmap/grafana-dashboard-provider created
deployment.apps/grafana created
service/grafana created
...
deployment.apps/sensor-simulator created
```

Espere todos os Deployments ficarem disponíveis. Na primeira vez, isso pode levar alguns minutos, porque o cluster baixa as imagens públicas (centenas de MB cada):

```bash
kubectl wait --for=condition=Available deployment --all -n opaiot-p5 --timeout=300s
```

Saída esperada: uma linha `deployment.apps/<nome> condition met` para cada um dos 8 Deployments. Se o comando expirar, vá para o [Diagnóstico](#diagnóstico).

## 6. Ler o estado dos Pods

```bash
kubectl get pods -n opaiot-p5
```

```text
NAME                               READY   STATUS    RESTARTS   AGE
grafana-7d4768d678-rk4gv           1/1     Running   0          3m
iot-processor-b8cfffdf9-bm5fc      1/1     Running   0          3m
kafka-8469fdb5b7-rf6v6             1/1     Running   0          3m
kafka-ui-7d9984ffc5-mpmd8          1/1     Running   0          3m
mosquitto-8658dc66bc-tmjwn         1/1     Running   0          3m
mqtt-to-kafka-554868c964-848f9     1/1     Running   0          3m
prometheus-79685d6879-s6cs4        1/1     Running   0          3m
sensor-simulator-d7486454f-274q7   1/1     Running   0          3m
```

Os sufixos dos nomes vão ser outros no seu cluster. Leia as colunas:

- **`READY`**: containers prontos / containers do Pod. Um Pod pronto entra no balanceamento do Service.
  - Nos Pods **com** `readinessProbe` (Kafka, Mosquitto e `iot-processor`), pronto quer dizer que a probe passou. O Kafka costuma ficar 30 a 60 segundos em `0/1`.
  - Nos Pods **sem** probe (sensor, ponte, Prometheus, Grafana e Kafka UI), pronto quer dizer só que o processo iniciou.
- **`STATUS`**: `Running` quer dizer que o container está em execução. **Não** quer dizer que a aplicação funciona.
- **`RESTARTS`**: quantas vezes o container caiu e foi reiniciado. Um valor que só cresce indica problema: veja `kubectl logs <pod> -n opaiot-p5 --previous`.

> **`Running` não prova que a stack funciona.** Se o sensor ou a ponte não conseguirem falar com o MQTT ou o Kafka, eles continuam `Running` e `1/1`, só repetindo `waiting for ...` nos logs. A prova é ver os dados passarem, no [passo 9](#9-comprovar-o-fluxo-de-ponta-a-ponta).

Veja também os Deployments e os Services:

```bash
kubectl get deploy,svc -n opaiot-p5
```

Na lista de Services, compare `TYPE`: `ClusterIP` (só dentro do cluster) e `NodePort` (`3000:30300/TCP` quer dizer porta 3000 no Service e 30300 nos nodes).

## 7. Deployment, ReplicaSet, Pod e labels

Siga a cadeia do sensor:

```bash
kubectl get deployment sensor-simulator -n opaiot-p5
kubectl get rs,pods -n opaiot-p5 -l app=sensor-simulator
```

```text
NAME                                         DESIRED   CURRENT   READY   AGE
replicaset.apps/sensor-simulator-d7486454f   1         1         1       4m

NAME                                   READY   STATUS    RESTARTS   AGE
pod/sensor-simulator-d7486454f-274q7   1/1     Running   0          4m
```

Repare que o hash `d7486454f` aparece no ReplicaSet e no Pod. O `-l app=sensor-simulator` é um selector: ele filtra pela label. Veja todas as labels:

```bash
kubectl get pods -n opaiot-p5 --show-labels
```

Inspecione um Pod sem copiar o nome dele, usando o selector:

```bash
kubectl describe pod -n opaiot-p5 -l app=sensor-simulator
```

Procure:

- `Labels:` (a label `app` e a `pod-template-hash`, que liga o Pod ao ReplicaSet);
- `Controlled By: ReplicaSet/sensor-simulator-...` (quem criou este Pod);
- `Environment:`, com `DEVICE_ID: sensor-simulator-... (v1:metadata.name)` (o valor e a origem dele) e `MQTT_TOPIC: iot/$(DEVICE_ID)/telemetry`;
- `Events:` no fim (agendamento, imagem, início do container). É o primeiro lugar a olhar quando algo dá errado.

## 8. Ver os logs

```bash
kubectl logs deploy/sensor-simulator -n opaiot-p5 --tail=3
kubectl logs deploy/mqtt-to-kafka -n opaiot-p5 --tail=3
kubectl logs deploy/iot-processor -n opaiot-p5 --tail=3
```

Saída esperada (linhas encurtadas):

```text
[sensor] published device_id=sensor-simulator-d7486454f-274q7 payload={... 'temperature': 23.88, ...}
[mqtt-to-kafka] forwarded mqtt_topic=iot/sensor-simulator-d7486454f-274q7/telemetry kafka_topic=iot.telemetry partition=0 offset=28 ...
[iot-processor] processed topic=iot.telemetry partition=0 offset=28 device_id=sensor-simulator-d7486454f-274q7 temperature=23.88 ...
```

O mesmo `offset` na ponte e no processador mostra a mesma mensagem passando pelo Kafka. Para acompanhar em tempo real, use `-f` (e `Ctrl+C` para sair). Os logs do broker ficam em `kubectl logs deploy/kafka -n opaiot-p5 --tail=20`.

> `kubectl logs deploy/<nome>` mostra os logs de **um** Pod do Deployment. Com uma réplica isso basta. No [passo 11](#11-escalar-o-sensor) você vai ver como ler todos os Pods de uma vez.

## 9. Comprovar o fluxo de ponta a ponta

Os testes abaixo criam Pods temporários dentro do cluster (`--rm` os apaga ao final). Lá dentro, os nomes dos Services funcionam como endereços, igual aos nomes de serviço no Compose.

**MQTT.** Assine o tópico de telemetria pelo Service `mosquitto`:

```bash
kubectl run mqtt-test --rm -it --restart=Never -n opaiot-p5 --image=eclipse-mosquitto:2 -- mosquitto_sub -h mosquitto -t 'iot/+/telemetry' -C 3 -v
```

São esperadas três linhas `iot/sensor-simulator-.../telemetry {"device_id": ...}`. As mensagens `If you don't see a command prompt...` e `pod "mqtt-test" deleted` são normais.

**Kafka.** Descreva o tópico e leia algumas mensagens pelo Pod do broker:

```bash
kubectl exec deploy/kafka -n opaiot-p5 -- \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic iot.telemetry

kubectl exec deploy/kafka -n opaiot-p5 -- \
  /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 \
  --topic iot.telemetry --from-beginning --max-messages 5
```

O tópico tem `PartitionCount: 1`. No Compose são 3, porque lá o `kafka-init` cria o tópico. Aqui ele é criado automaticamente na primeira mensagem.

**Métricas.** Leia o `/metrics` do processador pelo Service `iot-processor`:

```bash
kubectl run metrics-test --rm -it --restart=Never -n opaiot-p5 --image=busybox:1.36 -- sh -c 'wget -qO- http://iot-processor:8000/metrics | grep ^iot_'
```

```text
iot_messages_total 33.0
iot_messages_created 1.794453757611872e+09
iot_temperature_celsius 26.77
iot_humidity_percent 60.78
iot_vibration_level 0.1185
```

**Rode o comando de novo depois de uns 10 segundos.** O `iot_messages_total` deve ter subido cerca de 5 (um sensor publicando a cada 2 s). Isso comprova o caminho inteiro: sensor → MQTT → ponte → Kafka → processador.

**Service → Pods.** Veja como o Service encontra o Pod:

```bash
kubectl describe svc iot-processor -n opaiot-p5
kubectl get pods -n opaiot-p5 -l app=iot-processor -o wide
```

Em `describe`, o `Selector` é `app=iot-processor` e `Endpoints` mostra `IP:8000` de cada Pod pronto que tem essa label. Compare com a coluna `IP` do segundo comando.

## 10. Acessar Prometheus, Grafana e Kafka UI

### Com `kubectl port-forward` (funciona em qualquer ambiente)

O `port-forward` abre uma porta no **seu computador** e a encaminha, pela API do Kubernetes, para um Service do cluster. Cada comando fica em primeiro plano, então use um terminal para cada um:

```bash
kubectl port-forward -n opaiot-p5 svc/prometheus 9090:9090
```

```bash
kubectl port-forward -n opaiot-p5 svc/grafana 3000:3000
```

```bash
kubectl port-forward -n opaiot-p5 svc/kafka-ui 8080:8080
```

Cada um deve mostrar `Forwarding from 127.0.0.1:<porta> -> <porta>`. No bash, dá para rodar os três no mesmo terminal com `&` no fim de cada linha e encerrá-los depois com `kill $(jobs -p)`.

Acesse no navegador:

- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000> (`admin` / `admin`; na troca de senha pedida no primeiro acesso, pode clicar em **Skip**)
- Kafka UI: <http://localhost:8080>

Em playgrounds online que expõem portas por um menu de tráfego (como o KillerCoda), acrescente `--address 0.0.0.0` ao `port-forward` e abra a porta por esse menu.

### Com NodePort (alternativa)

Os Services de Prometheus, Grafana e Kafka UI também são `NodePort`. O acesso por eles depende de o IP do node ser alcançável a partir do navegador:

| Ambiente | Endereço |
| --- | --- |
| Docker Desktop | `http://localhost:30090`, `http://localhost:30300`, `http://localhost:30080` |
| K3s | `http://<ip-do-node>:30090` etc. (IP em `kubectl get nodes -o wide`) |
| Minikube | `minikube service grafana -n opaiot-p5 --url` (o mesmo para `prometheus` e `kafka-ui`) |

### O que observar

1. **Prometheus**, em **Status > Targets**: o target `iot-processor` (`http://iot-processor:8000/metrics`) deve estar `UP`. O Prometheus encontra o processador pelo nome do Service, configurado no ConfigMap `prometheus-config`.
2. **Prometheus**, em **Graph**: execute as consultas abaixo. **Anote o valor da taxa**: você vai compará-lo nos passos 11 e 12.

   ```promql
   iot_messages_total
   ```

   ```promql
   rate(iot_messages_total[1m])
   ```

   Com um sensor publicando a cada 2 s, a taxa fica perto de `0.5` mensagem por segundo.

3. **Grafana**: abra **Dashboards > OpAIoT > IoT Local - Telemetria**, ou <http://localhost:3000/d/iot-local-telemetry>. O datasource e o dashboard vêm de ConfigMaps (`grafana.yaml` e `grafana-dashboard.yaml`); o dashboard é o mesmo da prática com Compose.
4. **Kafka UI**: no cluster `opaiot-k8s`, abra **Topics > iot.telemetry > Messages**. A chave (`Key`) de cada mensagem é o `device_id`.

## 11. Escalar o sensor

Peça 3 réplicas do sensor (mudança **imperativa**):

```bash
kubectl scale deployment sensor-simulator --replicas=3 -n opaiot-p5
kubectl get pods -n opaiot-p5 -l app=sensor-simulator
```

```text
NAME                               READY   STATUS    RESTARTS   AGE
sensor-simulator-d7486454f-274q7   1/1     Running   0          5m
sensor-simulator-d7486454f-4xmt8   1/1     Running   0          5s
sensor-simulator-d7486454f-dm4j6   1/1     Running   0          5s
```

Para ver os logs dos **três** Pods, use o selector com `--prefix`, que mostra de qual Pod veio cada linha:

```bash
kubectl logs -n opaiot-p5 -l app=sensor-simulator --prefix --tail=1
```

```text
[pod/sensor-simulator-d7486454f-274q7/sensor-simulator] [sensor] published device_id=sensor-simulator-d7486454f-274q7 ...
[pod/sensor-simulator-d7486454f-4xmt8/sensor-simulator] [sensor] published device_id=sensor-simulator-d7486454f-4xmt8 ...
[pod/sensor-simulator-d7486454f-dm4j6/sensor-simulator] [sensor] published device_id=sensor-simulator-d7486454f-dm4j6 ...
```

Como cada Pod usa o próprio nome como `DEVICE_ID`, agora há **três dispositivos** distintos. Confira no processador:

```bash
kubectl logs deploy/iot-processor -n opaiot-p5 --tail=6
```

Os `device_id` se alternam entre os três Pods. Depois de cerca de 1 minuto, `rate(iot_messages_total[1m])` no Prometheus (ou o painel **Taxa de mensagens** no Grafana) deve chegar perto de `1.5`, o triplo do valor anotado.

Por fim, olhe os ReplicaSets:

```bash
kubectl get rs -n opaiot-p5 -l app=sensor-simulator
```

Continua havendo **um** ReplicaSet, agora com `DESIRED 3`. Escalar não muda o template do Pod, só a quantidade de cópias.

## 12. Imperativo x declarativo

Até aqui, o YAML em `k8s/sensor-simulator.yaml` diz `replicas: 1`, e o cluster está com 3. Os dois **divergem**. Aplique a pasta de novo:

```bash
kubectl apply -f k8s/
kubectl get pods -n opaiot-p5 -l app=sensor-simulator
```

Quase tudo aparece como `unchanged`, exceto `deployment.apps/sensor-simulator configured`, e dois dos três sensores entram em `Terminating`. O `kubectl apply` leva o cluster ao que está nos arquivos. Por isso `kubectl scale` e `kubectl set env` são **imperativos**: mudam só o cluster, e o próximo `apply` os desfaz. Em equipe, os arquivos (versionados no Git) são a referência do estado desejado; comandos imperativos ficam para testes rápidos e emergências.

Agora faça uma mudança **declarativa**, editando o arquivo:

1. Abra `k8s/sensor-simulator.yaml` no editor e troque o valor de `PUBLISH_INTERVAL` de `"2"` para `"1"`. Salve.
2. Veja o que vai mudar antes de aplicar. No Linux e no macOS, ou no Git Bash, use o comando abaixo; se ele reclamar que não encontrou o programa `diff`, pule este item:

   ```bash
   kubectl diff -f k8s/sensor-simulator.yaml
   ```

3. Aplique e acompanhe a atualização:

   ```bash
   kubectl apply -f k8s/
   kubectl rollout status deployment/sensor-simulator -n opaiot-p5
   kubectl get rs,pods -n opaiot-p5 -l app=sensor-simulator
   ```

   ```text
   NAME                                          DESIRED   CURRENT   READY   AGE
   replicaset.apps/sensor-simulator-67c65dcb96   1         1         1       10s
   replicaset.apps/sensor-simulator-d7486454f    0         0         0       6m

   NAME                                    READY   STATUS    RESTARTS   AGE
   pod/sensor-simulator-67c65dcb96-5nxzb   1/1     Running   0          10s
   ```

   Desta vez o **template** mudou (uma variável de ambiente), então o Deployment criou um **ReplicaSet novo** e trocou o Pod antigo por um novo (*rolling update*). O ReplicaSet antigo fica com 0 réplicas, guardado para um eventual retorno. O Pod novo tem outro nome e, portanto, outro `device_id`. A taxa no Prometheus vai para perto de `1` mensagem por segundo.

4. Veja o histórico de versões:

   ```bash
   kubectl rollout history deployment/sensor-simulator -n opaiot-p5
   ```

Para voltar, desfaça a edição no arquivo e aplique de novo:

```bash
git diff k8s/
git restore k8s/sensor-simulator.yaml
kubectl apply -f k8s/
kubectl get rs -n opaiot-p5 -l app=sensor-simulator
```

Se você baixou o repositório sem Git, volte o valor para `"2"` no editor. Repare que o ReplicaSet `...d7486454f` voltou a ter `DESIRED 1`: o template é igual ao original, então o hash também é, e o Deployment reaproveita o ReplicaSet antigo.

> Atalhos imperativos como `kubectl set env deployment/sensor-simulator PUBLISH_INTERVAL=1 -n opaiot-p5` e `kubectl rollout undo` fazem o mesmo efeito no cluster, mas deixam o YAML desatualizado, e o próximo `kubectl apply -f k8s/` os desfaz.

## 13. Apagar Pods e observar a reconciliação

### Um Pod sem estado: o processador

Anote o `CLUSTER-IP` do Service, apague o Pod pelo selector e acompanhe:

```bash
kubectl get svc iot-processor -n opaiot-p5
kubectl delete pod -n opaiot-p5 -l app=iot-processor --wait=false
kubectl get pods -n opaiot-p5 -l app=iot-processor -w
```

```text
NAME                            READY   STATUS              RESTARTS   AGE
iot-processor-b8cfffdf9-bm5fc   1/1     Terminating         0          9m
iot-processor-b8cfffdf9-q47zz   0/1     ContainerCreating   0          1s
iot-processor-b8cfffdf9-q47zz   0/1     Running             0          2s
iot-processor-b8cfffdf9-q47zz   1/1     Running             0          11s
```

Saia do modo `-w` com `Ctrl+C`. O que aconteceu:

- O ReplicaSet viu 0 Pods onde deveria haver 1 e criou outro: é a reconciliação. O Pod novo tem **outro nome e outro IP**.
- Por uns 10 segundos o Pod novo ficou `0/1 Running`: o processo já rodava, mas a `readinessProbe` ainda não tinha passado. Nesse intervalo, o Service não enviou tráfego para ele.

Confira o que **não** mudou:

```bash
kubectl get svc iot-processor -n opaiot-p5
kubectl describe svc iot-processor -n opaiot-p5
kubectl logs deploy/iot-processor -n opaiot-p5 --tail=3
```

- O Service tem o mesmo nome e o mesmo `CLUSTER-IP`, e `Endpoints` passou a apontar para o IP do Pod novo. O Prometheus continuou coletando sem nenhuma reconfiguração.
- O processador retomou a leitura do Kafka **do offset onde parou**, porque o grupo `iot-processor` guarda a posição no broker.
- Já o `iot_messages_total` voltou a zero, porque o contador vive na memória do processo. Veja o painel **Total de mensagens** no Grafana. O painel **Taxa de mensagens** quase não muda, porque `rate()` sabe lidar com contadores que reiniciam.

### Um Pod com estado: o Kafka

Anote o último `offset` nos logs do processador e apague o Pod do Kafka:

```bash
kubectl delete pod -n opaiot-p5 -l app=kafka
kubectl get pods -n opaiot-p5 -l app=kafka -w
```

Espere o Pod novo chegar a `1/1` (30 a 60 s), saia com `Ctrl+C` e veja os logs:

```bash
kubectl logs deploy/mqtt-to-kafka -n opaiot-p5 --tail=8
kubectl logs deploy/iot-processor -n opaiot-p5 --tail=3
```

Na ponte aparecem `kafka send failed ...` e `waiting for kafka: NoBrokersAvailable`, depois `connected kafka=kafka:9092` de novo. E os **offsets recomeçaram do zero**: compare com o valor que você anotou.

O motivo é que o Kafka desta prática grava os dados em um volume `emptyDir`, que existe enquanto o Pod existe. O Pod novo começou com o disco vazio: o tópico foi recriado na primeira mensagem, e o que foi publicado durante a troca se perdeu (o sensor usa MQTT QoS 0 e a ponte não guarda nada). É uma **simplificação de laboratório**. Em produção, um serviço com estado como o Kafka roda como **StatefulSet** com **PersistentVolumeClaim**: o Pod recriado mantém o mesmo nome e se reconecta ao mesmo volume.

O mesmo vale, em menor escala, para Prometheus e Grafana, que também não têm volume. Apagar o Pod do Prometheus apaga o histórico das séries. O Grafana volta com o datasource e o dashboard, porque eles vêm de ConfigMaps: **a configuração declarada no cluster sobrevive; o estado guardado dentro do Pod, não.**

> Um `port-forward` aberto para um Pod que foi apagado termina com erro (`lost connection to pod`). Basta rodá-lo de novo.

## 14. Remover os recursos

Encerre os `port-forward` (`Ctrl+C` em cada terminal) e apague o namespace, que leva todos os recursos da prática junto:

```bash
kubectl delete namespace opaiot-p5
kubectl get ns opaiot-p5
```

A remoção pode levar alguns segundos. Ao final, o segundo comando responde `Error from server (NotFound): namespaces "opaiot-p5" not found`. As imagens dos apps continuam no Docker ou no Minikube. Para removê-las: `docker rmi opaiot/sensor-simulator:local opaiot/mqtt-to-kafka:local opaiot/iot-processor:local` (ou `minikube image rm ...`).

## Alternativa Redpanda

Se o Kafka não couber na memória do seu ambiente, troque-o pelo Redpanda, um broker compatível com o protocolo Kafka:

```bash
kubectl delete -f k8s/kafka.yaml
kubectl apply -f k8s/alternativas/redpanda.yaml
kubectl rollout status deployment/redpanda -n opaiot-p5
```

**Nenhum app precisa ser alterado.** O Service do Redpanda também se chama `kafka`, então ponte, processador e Kafka UI continuam usando `kafka:9092` e se reconectam sozinhos em cerca de 1 minuto. É o papel do Service: o nome é o contrato, e o que roda atrás dele pode mudar.

Com Redpanda, os comandos do broker mudam:

```bash
kubectl exec deploy/redpanda -n opaiot-p5 -- rpk topic list
kubectl exec deploy/redpanda -n opaiot-p5 -- rpk topic consume iot.telemetry --num 3
```

Enquanto estiver com Redpanda, **não rode `kubectl apply -f k8s/`**: isso recriaria o Kafka e devolveria o Service `kafka` para ele. Aplique só o arquivo alterado, por exemplo `kubectl apply -f k8s/sensor-simulator.yaml`. Para voltar ao Kafka:

```bash
kubectl delete -f k8s/alternativas/redpanda.yaml
kubectl apply -f k8s/
```

## Diagnóstico

| Sintoma | Causa provável | O que fazer |
| --- | --- | --- |
| Pod em `ErrImageNeverPull` | A imagem do app não está no node | Refaça o [passo 3](#3-construir-as-imagens-dos-apps) para o seu ambiente. `kubectl describe pod -n opaiot-p5 -l app=<app>` mostra `Container image "..." is not present with pull policy of Never`. Depois de corrigir, o Pod sobe sozinho; para acelerar, apague-o com `kubectl delete pod -n opaiot-p5 -l app=<app>`. |
| Pod em `Pending` por muito tempo | Falta CPU ou memória no node | Em `kubectl describe pod`, procure `Insufficient memory` nos `Events`. Dê mais memória ao Docker Desktop ou ao Minikube, ou use a [alternativa Redpanda](#alternativa-redpanda). |
| Kafka em `CrashLoopBackOff` ou `OOMKilled` | Memória insuficiente | `kubectl logs deploy/kafka -n opaiot-p5 --previous`; use a alternativa Redpanda. |
| Kafka `0/1 Running` por até 1 minuto | A `readinessProbe` começa após 30 s | Normal. Espere. |
| `waiting for kafka` ou `waiting for mqtt broker` nos logs | A dependência ainda não respondeu | Normal na subida: os apps tentam de novo. Se não parar, confira o Pod do Kafka ou do Mosquitto. |
| `port-forward` falha com `unable to listen on port` | A porta local está ocupada, por exemplo pela stack do Compose | `docker compose down` ou outra porta local: `kubectl port-forward -n opaiot-p5 svc/grafana 3001:3000`. |
| `port-forward` termina com `lost connection to pod` | O Pod por trás do Service foi recriado | Rode o `port-forward` de novo. |
| `kubectl diff` reclama de `diff` | O programa `diff` não está instalado (comum no PowerShell) | Pule o `diff` ou use o Git Bash. |
| No Git Bash, `kubectl exec` falha com `exec: "C:/Program Files/Git/opt/kafka/..."` | O Git Bash converte argumentos que começam com `/` em caminhos do Windows | Comece o comando com `MSYS_NO_PATHCONV=1` (por exemplo, `MSYS_NO_PATHCONV=1 kubectl exec deploy/kafka ...`) ou use o PowerShell. |
| `The connection to the server ... was refused` | Cluster parado ou contexto errado | `kubectl config current-context`; no Docker Desktop, `kubectl config use-context docker-desktop`; no Minikube, `minikube start`. |

## Perguntas de verificação

Responda com base no que você observou:

1. No passo 11, `kubectl scale` criou um ReplicaSet novo? E a mudança do `PUBLISH_INTERVAL` no passo 12? Por que a diferença?
2. Por que o `kubectl apply -f k8s/` do passo 12 desfez o `kubectl scale` do passo 11? Onde fica, então, o estado desejado da aplicação?
3. Ao apagar o Pod do `iot-processor`, quem criou o Pod novo? O que mudou e o que permaneceu igual para o Prometheus, que coleta as métricas dele?
4. O Pod do `mqtt-to-kafka` aparece como `1/1 Running`. Isso prova que ele está encaminhando mensagens? Como você comprovou o fluxo?
5. O que aconteceu com o tópico `iot.telemetry` e com os offsets quando o Pod do Kafka foi apagado? O que mudaria com StatefulSet e PersistentVolumeClaim?
6. Os Services `iot-processor` e `grafana` são de tipos diferentes. Quem consegue acessar cada um? Por que o roteiro usa `port-forward` como caminho principal?

<details>
<summary>Respostas esperadas</summary>

1. Não. `scale` muda só a quantidade de réplicas, e o mesmo ReplicaSet passou a querer 3 Pods. A variável de ambiente faz parte do **template** do Pod: mudar o template gera um hash novo, um ReplicaSet novo e um *rolling update*. Voltar ao template original reaproveita o ReplicaSet antigo.
2. O arquivo diz `replicas: 1`, e o `apply` leva o cluster ao que está no arquivo. O estado desejado de referência fica nos manifests (versionados no Git). Comandos imperativos mudam só o cluster e se perdem no próximo `apply`.
3. O ReplicaSet, controlado pelo Deployment, viu 0 de 1 Pods e criou outro. Mudaram o nome e o IP do Pod. Permaneceram o nome DNS e o `ClusterIP` do Service `iot-processor`, cujos `Endpoints` passaram a apontar para o Pod novo. Por isso o Prometheus, que coleta por `iot-processor:8000`, não precisou ser reconfigurado. O contador `iot_messages_total` reiniciou, porque vive na memória do processo.
4. Não. Sem `readinessProbe`, "pronto" quer dizer apenas que o processo iniciou. O fluxo é comprovado pelos dados: `forwarded ... offset=N` na ponte e `processed ... offset=N` no processador, mensagens lidas no tópico Kafka e `iot_messages_total` crescendo entre duas leituras (ou `rate()` maior que zero no Prometheus).
5. O `emptyDir` foi apagado junto com o Pod. O Kafka novo começou vazio, o tópico foi recriado com offsets a partir de zero, e as mensagens do intervalo se perderam. Com StatefulSet e PVC, o Pod recriado teria o mesmo nome e reanexaria o mesmo volume, preservando tópico, mensagens e offsets do grupo.
6. `ClusterIP` (`iot-processor`) só é acessível de dentro do cluster, por outros Pods. `NodePort` (`grafana`) também abre uma porta em cada node, e funciona de fora quando o IP do node é alcançável. O `port-forward` cria um túnel do seu computador até o Service pela API do Kubernetes: funciona em qualquer ambiente (inclusive onde o IP do node não é alcançável, como no Minikube com driver Docker) e também com Services `ClusterIP`.

</details>
