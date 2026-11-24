# Aula 4 - MQTT para Kafka na VM

Esta é a variante da prática para a **VM do curso**. O caminho principal da aula é com Docker Compose (veja o [README](README.md)). Aqui, sem Docker, você instala o Mosquitto na VM, usa o Kafka que instalou na [Aula 3](../Aula_3_kafka/instalando_kafka_vm.md) e roda a ponte Python em primeiro plano.

> **Atenção — limitações da VM.** Leia antes de começar; elas mudam o que dá para fazer nesta prática:
>
> - **Sem Docker e sem `systemd`.** A VM é um container Ubuntu. O Mosquitto é instalado com `apt` e roda como processo solto (`nohup`); a ponte roda em primeiro plano e **para se a sua sessão SSH cair**. Se o ambiente reiniciar, nada volta sozinho: broker, Kafka e ponte precisam ser iniciados de novo.
> - **ESP32 e Wokwi não conseguem publicar no Mosquitto da VM.** Apenas o SSH, o Prometheus e o Grafana têm porta acessível de fora, e o túnel SSH (`ssh -L`) é bloqueado. Nesta variante, o "dispositivo" é o `mosquitto_pub` executado **dentro** da VM. Para o fluxo completo com ESP32 ou Wokwi, use o README com Docker na sua máquina.
> - **Memória e processos são poucos.** O container tem 1 GiB de memória e limite de 256 processos/threads, divididos com Kafka (≈ 108 threads), Prometheus e Grafana. Rode **um** comando `kafka-*.sh` por vez, use no máximo 3 sessões SSH e encerre o que não estiver usando. Detalhes no [guia da VM](../ambiente_vm.md#6-limites-de-memória-e-de-processos).
> - **Só `~/workspace` é preservado.** Mantenha o repositório, o ambiente virtual e o log do Mosquitto lá.
>
> Todo o ambiente está descrito no [guia da VM](../ambiente_vm.md). Se algo se comportar de outra forma na sua VM, avise os monitores.

## 1. O que muda em relação ao README com Docker

| README (Docker Compose) | Esta variante (VM) |
| --- | --- |
| Mosquitto em container, com o `mosquitto.conf` da aula | Mosquitto instalado com `apt`, iniciado com o **mesmo** `mosquitto/mosquitto.conf` |
| Ponte no serviço `mqtt-kafka-producer` | Ponte iniciada à mão com Python, em um ambiente virtual |
| Kafka em `kafka:9092`, pela rede Docker da Aula 3 | Kafka da VM em `localhost:9092` |
| Variáveis no arquivo `.env` | Variáveis passadas na linha de comando |
| `docker compose exec mosquitto mosquitto_pub ...` | `mosquitto_pub ...` direto (os clientes já vêm na VM) |
| `docker compose logs` | A própria saída do terminal da ponte e o log do Mosquitto |
| ESP32 / Wokwi publicam no IP da sua máquina | **Não é possível** (veja o alerta acima) |

## 2. Pré-requisitos

Acesse a VM por SSH conforme a [seção 2 do guia da VM](../ambiente_vm.md#2-acesso-por-ssh) e entre no diretório da aula:

```bash
cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_4_esp32_mqtt_kafka
```

Se o repositório ainda não estiver na VM, clone-o dentro de `~/workspace` (veja a [seção 3 do guia](../ambiente_vm.md#3-onde-guardar-os-arquivos)).

Você precisa do **Kafka da Aula 3 em execução** e do tópico `iot.air_quality` criado. Confira:

```bash
pgrep -af 'kafka\.Kafka'
ss -ltn | grep 9092
/opt/kafka/bin/kafka-topics.sh --describe --topic iot.air_quality --bootstrap-server localhost:9092
```

A saída deve mostrar o processo do Kafka, a porta `9092` em `LISTEN` e o tópico com `PartitionCount: 3`. Se não, siga o [roteiro de instalação do Kafka](../Aula_3_kafka/instalando_kafka_vm.md) (passo 4, para iniciar) e os passos 3 e 4 do [README dos scripts da Aula 3](../Aula_3_kafka/scripts/README.md) (para criar o tópico).

> Os processos `producer.py` e `consumer_metrics.py` da Aula 3 **não** precisam estar rodando. Encerre-os se estiverem, para economizar processos.

## 3. Instalar e iniciar o Mosquitto

Os clientes `mosquitto_pub` e `mosquitto_sub` já vêm na VM, mas o **broker** não. Instale-o uma vez:

```bash
sudo apt update
sudo apt install -y mosquitto
```

Use o `sudo` só aqui: na VM, cada `sudo` pode deixar um processo zumbi que ocupa uma vaga do limite de processos. Se aparecerem avisos sobre `systemd` ou sobre o serviço não ter iniciado, ignore: o broker será iniciado à mão.

O pacote pode ter iniciado um broker por conta própria. Confira antes de seguir:

```bash
pgrep -af mosquitto
```

Se aparecer algum processo, encerre-o para usar a configuração da aula (porta `1883`, acesso anônimo):

```bash
sudo pkill -x mosquitto
```

Inicie o broker **em segundo plano**, com o `mosquitto.conf` desta aula, mandando o log para um arquivo em `~/workspace`:

```bash
cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_4_esp32_mqtt_kafka
nohup /usr/sbin/mosquitto -c mosquitto/mosquitto.conf > ~/workspace/mosquitto-aula4.log 2>&1 &
```

Confirme que subiu:

```bash
pgrep -af mosquitto
ss -ltn | grep 1883
tail ~/workspace/mosquitto-aula4.log
```

O processo deve estar listado, a porta `1883` em `LISTEN` e o log deve conter `Opening ipv4 listen socket on port 1883`.

## 4. Entender o MQTT com duas sessões

Antes de envolver a ponte, veja o modelo publicador/assinante só no broker. Abra **duas sessões SSH** na VM.

**Sessão A — assinante:**

```bash
mosquitto_sub -h localhost -p 1883 -t opaiot/temperature -v
```

**Sessão B — publicador:**

```bash
mosquitto_pub -h localhost -p 1883 -t opaiot/temperature -m "25.4"
```

Na sessão A deve aparecer `opaiot/temperature 25.4` (a opção `-v` imprime o tópico antes do payload). Publique mais algumas vezes, mudando o valor. Encerre o assinante com `Ctrl+C`.

Nada disso chega ao Kafka: a ponte assina `opaiot/air_quality`, e o broker só entrega mensagens a quem assinou o tópico.

## 5. Preparar o ambiente Python

Na sessão A (ou em qualquer uma), no diretório da aula:

```bash
cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_4_esp32_mqtt_kafka
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

O `requirements.txt` fixa `paho-mqtt==1.6.1`, versão que o script usa. Não instale o `paho-mqtt` sem a versão, pois a série 2.x mudou a API de callbacks e o script deixa de funcionar.

> Em **cada nova sessão** que for rodar Python, entre no diretório da aula e ative o ambiente virtual (a sessão começa em `~/workspace`, sem o venv):
>
> ```bash
> cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_4_esp32_mqtt_kafka
> source .venv/bin/activate
> ```

## 6. Executar a ponte (sessão A)

Com o Kafka e o Mosquitto no ar, inicie a ponte **em primeiro plano**:

```bash
MQTT_HOST=localhost MQTT_PORT=1883 \
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
python scripts/mqtt_kafka_producer.py
```

`MQTT_HOST` e `MQTT_PORT` repetem os padrões do script e estão aqui para deixar claro onde a ponte se conecta. `KAFKA_BOOTSTRAP_SERVERS` **precisa** ser informado: o padrão do script (`localhost:29092`) é o listener externo do Kafka da Aula 3 com Docker, e o Kafka da VM escuta em `localhost:9092`. Os demais valores (`MQTT_TOPIC=opaiot/air_quality`, `KAFKA_TOPIC=iot.air_quality`, `DEFAULT_*`) já têm padrão adequado. A lista de variáveis está no [README dos scripts](scripts/README.md).

A saída deve ser:

```text
[mqtt-kafka-producer] starting mqtt -> kafka bridge
[mqtt-kafka-producer] kafka bootstrap servers: localhost:9092
[mqtt-kafka-producer] kafka topic: iot.air_quality
[mqtt-kafka-producer] press Ctrl+C to stop
[mqtt-kafka-producer] connected mqtt=localhost:1883 subscribed=opaiot/air_quality
```

Deixe esta sessão aberta, acompanhando o log. Os próximos passos usam a **sessão B**.

## 7. Publicar uma mensagem de teste (sessão B)

```bash
mosquitto_pub -h localhost -p 1883 -t 'opaiot/air_quality' \
  -m '{"sensor_id":"sensor-99","room":"lab-99","temperature":28.4,"humidity":61.0,"co2":900}'
```

Na sessão A (a ponte) aparece na hora `forwarded mqtt payload=...` (a normalização). A linha `sent topic=iot.air_quality partition=... offset=... key=sensor-99` (a confirmação de entrega no Kafka) só é impressa quando a **próxima** mensagem chega à ponte, porque o callback de entrega do producer roda no `poll()`, que a ponte só chama ao publicar. Publique também a mensagem do passo 9 e, então, anote os valores de `partition` e `offset` da linha `sent` do `sensor-99`.

## 8. Conferir a mensagem no Kafka (sessão B)

**Opção A — ler a mensagem exata.** Depois de publicar também a mensagem do passo 9 (para a linha `sent` do `sensor-99` aparecer na ponte), substitua `<P>` e `<N>` pelos valores de `partition=` e `offset=` dessa linha:

```bash
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic iot.air_quality \
  --partition <P> --offset <N> \
  --max-messages 1 \
  --property print.key=true
```

Deve aparecer `sensor-99` seguido do JSON completo. O comando encerra sozinho depois de uma mensagem. Ele abre uma JVM (≈ 24 threads por alguns segundos), então rode um de cada vez.

**Opção B — acompanhar um fluxo contínuo.** Use o consumer Python da Aula 3, que consome menos processos que uma JVM. Em uma sessão com o ambiente virtual **da Aula 3** ativo (veja o [README dos scripts da Aula 3](../Aula_3_kafka/scripts/README.md#2-preparar-o-ambiente-python)):

```bash
cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_3_kafka
source .venv/bin/activate
GROUP_ID=aula4-verificacao AUTO_OFFSET_RESET=latest python scripts/consumer_metrics.py
```

Aguarde alguns segundos até o consumer receber as partitions, depois publique mensagens (passos 7, 9 e 10). Cada evento aparece como `[CONSUMER] partition=... key=sensor-99 ...`. Se você já configurou o Prometheus e o Grafana na Aula 3, o consumer expõe as métricas na porta `8000` e as leituras entram no dashboard (`http://andromeda.lasdpc.icmc.usp.br:13XXX/d/iot-kafka-telemetry`, com `XXX` os três dígitos do seu usuário). Encerre com `Ctrl+C`.

## 9. Testar a normalização (sessão B)

Publique um payload no formato "de dispositivo", sem `sensor_id` nem `co2`:

```bash
mosquitto_pub -h localhost -p 1883 -t 'opaiot/air_quality' \
  -m '{"temperature":25.4,"humidity":58.2,"deviceId":"esp32-dht22","location":"sala"}'
```

Na ponte, a linha `forwarded mqtt payload=` mostra o evento normalizado: `deviceId` virou `sensor_id`, `location` virou `room`, e `co2` (800) e `timestamp` foram preenchidos com os padrões.

Agora um payload que a ponte não aceita, sem `humidity`:

```bash
mosquitto_pub -h localhost -p 1883 -t 'opaiot/air_quality' -m '{"temperature":25.4}'
```

O log mostra `ignored unsupported payload` e nada é enviado ao Kafka.

## 10. Simular um dispositivo em laço (sessão B)

Sem ESP32, repita a publicação em um laço (20 mensagens, uma por segundo):

```bash
for i in $(seq 1 20); do
  mosquitto_pub -h localhost -p 1883 -t opaiot/air_quality \
    -m "{\"sensor_id\":\"sensor-sim\",\"room\":\"lab-sim\",\"temperature\":2$((RANDOM % 10)).$((RANDOM % 10)),\"humidity\":6$((RANDOM % 10)).0,\"co2\":$((700 + RANDOM % 300))}"
  sleep 1
done
```

Acompanhe a ponte na sessão A. Para simular dois dispositivos, rode o laço de novo em outra sessão com outro `sensor_id`.

## 11. ESP32 e Wokwi

O firmware em [firmware/esp32_mq7_mqtt.ino](firmware/esp32_mq7_mqtt.ino) vem configurado com `MQTT_SERVER "andromeda.lasdpc.icmc.usp.br"` e `MQTT_PORT 20202`. **Esse endereço não leva ao Mosquitto da sua VM**: o broker que você iniciou escuta na `1883` dentro do container, e a porta não é exposta fora dele.

Para ver o ESP32 ou o Wokwi alimentando o Kafka, use o [README com Docker](README.md) na sua máquina. Se os monitores indicarem um broker MQTT compartilhado, acessível pela internet, a ponte pode assiná-lo: inicie-a com `MQTT_HOST` e `MQTT_PORT` desse broker e o `MQTT_TOPIC` combinado, no lugar de `localhost:1883` do passo 6 (o firewall do ambiente pode bloquear a conexão de saída; nesse caso, avise os monitores).

## 12. Ao terminar

1. Encerre a ponte com `Ctrl+C` na sessão A.
2. Encerre o Mosquitto (é um processo seu, não precisa de `sudo`):

   ```bash
   pkill -x mosquitto
   ```

3. O Kafka pode continuar rodando para as próximas aulas. Se quiser liberar memória e processos, pare-o com `/opt/kafka/bin/kafka-server-stop.sh` (veja a [seção 7 do roteiro do Kafka](../Aula_3_kafka/instalando_kafka_vm.md#7-executar-o-kafka-sem-systemd)).

O ambiente virtual `.venv` e o log `~/workspace/mosquitto-aula4.log` podem ficar; o `.venv` está no `.gitignore` do repositório.

## 13. Problemas comuns

Se o Mosquitto não iniciar e o log mostrar `Address already in use`, já há um broker na porta `1883`. Veja com `pgrep -af mosquitto`; se for o que o `apt` iniciou, encerre-o com `sudo pkill -x mosquitto` e repita o comando do passo 3.

Se a ponte repetir `waiting for mqtt broker: [Errno 111] Connection refused`, o Mosquitto não está no ar ou a porta está errada. Confira `ss -ltn | grep 1883`.

Se a ponte registrar erros de conexão com o Kafka, confirme que o log inicial mostra `kafka bootstrap servers: localhost:9092` (sem a variável `KAFKA_BOOTSTRAP_SERVERS`, o script tenta `localhost:29092`, que não existe na VM) e que o Kafka está rodando: `pgrep -af 'kafka\.Kafka'`. Inicie-o conforme o [roteiro do Kafka](../Aula_3_kafka/instalando_kafka_vm.md).

Se aparecer `ModuleNotFoundError: No module named 'confluent_kafka'` (ou `paho`), o ambiente virtual não está ativo ou as dependências não foram instaladas. Rode `source .venv/bin/activate` e `pip install -r scripts/requirements.txt` no diretório da aula.

Se a mensagem foi publicada e nada aparece no Kafka, olhe o log da ponte: JSON inválido é descartado com `invalid json`, e JSON sem `temperature` ou `humidity` é ignorado com `ignored unsupported payload`. Confirme também que o tópico publicado é exatamente `opaiot/air_quality`.

Se um comando falhar com `pthread_create failed (EAGAIN)`, `Failed to start the native thread` ou `Resource temporarily unavailable`, o limite de 256 processos/threads foi atingido. Encerre consumers e sessões que não está usando, rode um comando `kafka-*.sh` por vez e confira `cat /sys/fs/cgroup/pids.current /sys/fs/cgroup/pids.max`. Veja o [guia da VM](../ambiente_vm.md#6-limites-de-memória-e-de-processos).

Se, depois de um reinício do ambiente, a ponte não conectar, `pgrep -af 'mosquitto|kafka\.Kafka'` mostrará que os processos não voltaram. Inicie o Kafka (passo 4 do roteiro dele), o Mosquitto (passo 3) e a ponte (passo 6), nessa ordem.
