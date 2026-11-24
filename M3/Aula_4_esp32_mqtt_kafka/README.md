# Prática 4 - MQTT para Kafka

Esta aula conecta telemetria MQTT ao tópico Kafka `iot.air_quality` da [Aula 3](../Aula_3_kafka/README.md), mantendo o mesmo formato de evento usado pelo `producer.py` da prática anterior. Este roteiro usa **somente Docker Compose**: o dispositivo pode ser um ESP32 real, o simulador Wokwi ou uma publicação manual de teste.

> **Atenção — este roteiro não funciona na VM do curso.** A VM é um container Ubuntu **sem Docker**. Para executar a prática nela, use o [roteiro para a VM](roteiro_para_vm.md), sabendo das limitações:
>
> - não há `docker` nem `docker compose`: o Mosquitto é instalado com `apt` e a ponte roda como processo Python;
> - **ESP32 e Wokwi não conseguem publicar no Mosquitto da VM**: só o SSH, o Prometheus e o Grafana têm porta acessível de fora, e o túnel SSH é bloqueado. A validação se limita a `mosquitto_pub` dentro da VM;
> - a memória (1 GiB) e o limite de 256 processos/threads são divididos com Kafka, Prometheus e Grafana;
> - não há `systemd`: o broker e a ponte não voltam sozinhos se o ambiente reiniciar, e a ponte para se a sessão SSH cair.
>
> Se você tem Docker na sua máquina, prefira este README.

## 1. Objetivo da prática

Ao final da prática, você deve conseguir:

- explicar por que dispositivos IoT publicam em MQTT e por que o backend consome de Kafka, e o papel de uma **ponte** entre os dois;
- subir um broker Mosquitto e a ponte MQTT → Kafka com Docker Compose, conectando-a ao Kafka da Aula 3;
- publicar e assinar mensagens MQTT pela linha de comando, entendendo o modelo publicador/assinante;
- normalizar payloads MQTT heterogêneos para o schema de evento da Aula 3;
- validar o caminho completo dispositivo → MQTT → Kafka → consumer.

## 2. Conceitos da prática

**MQTT na borda, Kafka no backend.** MQTT é leve, tolera conexões instáveis e funciona bem em microcontroladores; Kafka dá durabilidade, particionamento, consumo paralelo e retenção para os sistemas que processam os dados. A ponte (`scripts/mqtt_kafka_producer.py`) assina um tópico MQTT, normaliza o payload e publica no Kafka com `sensor_id` como **chave** — exatamente como o producer da Aula 3, preservando a ordem por sensor.

**Publicador e assinante.** No MQTT, quem publica não conhece quem recebe: o broker entrega cada mensagem a **todos** os assinantes do tópico naquele momento. Por isso é possível assinar o mesmo tópico em um terminal (para observar) enquanto a ponte o assina em outro. Mensagens publicadas em um tópico que ninguém assina são descartadas pelo broker.

**Normalização de payload.** Dispositivos diferentes publicam JSON diferente. A ponte aceita o formato da Aula 3 e também converte payloads comuns (`device_id`/`deviceId` → `sensor_id`, `location` → `room`, CO2 e timestamp com valores padrão quando ausentes). Detalhes em [scripts/README.md](scripts/README.md).

**Arquitetura:**

```text
ESP32 + DHT22 + MQ-7 (firmware/)  ──┐
Wokwi (simulador)                 ──┤  MQTT (opaiot/air_quality)
mosquitto_pub (teste manual)      ──┘
            │
            ▼
   Mosquitto (porta 1883)            <- compose desta aula
            │  assinatura
            ▼
   mqtt_kafka_producer.py (ponte)    <- compose desta aula
            │  key = sensor_id
            ▼
   Kafka, tópico iot.air_quality     <- stack da Aula 3 (rede compartilhada)
            │
            ▼
   consumer, Prometheus e Grafana da Aula 3
```

**Duas stacks, uma rede compartilhada.** A ponte precisa falar com o Mosquitto (desta aula) e com o Kafka (da Aula 3), que estão em projetos Compose diferentes. Por isso o serviço `mqtt-kafka-producer` participa de **duas redes**: a desta aula e a da Aula 3, declarada como `external` no [docker-compose.yml](docker-compose.yml). Assim ele usa `kafka:9092`, o nome do serviço.

Por que não usar a porta `29092` publicada no host? Porque o listener externo do broker é **anunciado** como `localhost:29092`: o cliente conecta, recebe esse endereço nos metadados e passa a tentar `localhost` — que, dentro de um container, é o próprio container. É um detalhe de `KAFKA_ADVERTISED_LISTENERS` que costuma gerar confusão: a porta publicada serve a clientes no host, não a containers em outra rede.

**Portas:**

| Serviço | Porta no host | Quem usa | Onde sobe |
| --- | --- | --- | --- |
| Mosquitto | `1883` | ESP32, Wokwi e clientes MQTT na sua máquina | [docker-compose.yml](docker-compose.yml) desta aula |
| Kafka (listener externo) | `29092` | Clientes no host (a ponte **não** usa) | [Aula 3](../Aula_3_kafka/docker/docker-compose.yml) |
| Grafana | `3000` | Dashboard da Aula 3 | [Aula 3](../Aula_3_kafka/docker/docker-compose.yml) |

**Configuração (`.env`).** O Compose lê as variáveis de um arquivo `.env` ao lado do `docker-compose.yml`, criado a partir de [.env.example](.env.example):

| Variável | Valor no `.env.example` | Uso |
| --- | --- | --- |
| `MQTT_HOST` | `mosquitto` | Broker MQTT visto pela ponte (nome do serviço na rede Docker) |
| `MQTT_HOST_PORT` | `1883` | Porta publicada no host para ESP32, Wokwi e clientes locais (dentro das redes Docker o broker é sempre `mosquitto:1883`) |
| `MQTT_TOPIC` | `opaiot/air_quality` | Tópico assinado pela ponte (aceita wildcard, ex.: `opaiot/+/air_quality`) |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka visto pela ponte, pela rede da Aula 3 |
| `KAFKA_TOPIC` | `iot.air_quality` | Tópico Kafka de destino |
| `DEFAULT_SENSOR_ID` | `sensor-01` | Sensor usado quando o payload não traz identificador |
| `DEFAULT_ROOM` | `lab-01` | Sala usada quando o payload não traz `room`/`location` |
| `DEFAULT_CO2` | `800` | CO2 usado quando o payload não traz `co2` |

Todas têm padrão no `docker-compose.yml`, então o `.env` só é preciso se você quiser alterar algum valor. Para rodar a ponte direto no host, sem Compose, veja [scripts/README.md](scripts/README.md).

**Arquivos da aula:**

| Arquivo | Descrição |
| --- | --- |
| [docker-compose.yml](docker-compose.yml) | Mosquitto e ponte MQTT → Kafka |
| [.env.example](.env.example) | Servidores MQTT/Kafka e tópicos da prática |
| [mosquitto/mosquitto.conf](mosquitto/mosquitto.conf) | Broker MQTT de laboratório com `allow_anonymous` |
| [firmware/esp32_mq7_mqtt.ino](firmware/esp32_mq7_mqtt.ino) | Firmware ESP32 + DHT22 + MQ-7 publicando MQTT |
| [firmware/README.md](firmware/README.md) | Configuração Wokwi, hardware e testes |
| [scripts/mqtt_kafka_producer.py](scripts/mqtt_kafka_producer.py) | Ponte MQTT → Kafka |
| [scripts/README.md](scripts/README.md) | Normalização, variáveis e execução no host |
| [roteiro_para_vm.md](roteiro_para_vm.md) | Variante **sem Docker** para a VM do curso (veja o alerta no topo) |

## 3. Prática passo a passo

Pré-requisitos: Docker com Docker Compose v2. Para o dispositivo real: ESP32 com DHT22 e MQ-7, ou um projeto Wokwi.

> **Dica (Windows):** execute os comandos no PowerShell ou no Git Bash. Onde a sintaxe diferir (cópia de arquivo, aspas no JSON), o passo traz as duas formas. Os comandos com `| grep texto` funcionam no Git Bash; no PowerShell, troque por `| Select-String texto`. No Git Bash, um caminho absoluto do container (como `/opt/kafka/bin/...` no passo 3.4) exige o prefixo `MSYS_NO_PATHCONV=1` no comando; sem ele o Git Bash converte o caminho para `C:/Program Files/Git/opt/...` e o `exec` falha. No PowerShell não é preciso.

### 3.1. Subir o Kafka da Aula 3

```bash
cd M3/Aula_3_kafka/docker
docker compose up --build -d
docker compose ps
```

Isso sobe o broker, o tópico `iot.air_quality`, o consumer e a observabilidade da Aula 3, além de criar a rede Docker que a ponte desta aula vai usar. Aguarde o serviço `kafka` ficar `healthy` e o `kafka-init` terminar (`Exited (0)`).

Se este passo for pulado, o compose do passo seguinte falha com `network docker_kafka-iot declared as external, but could not be found`.

> **Dica:** o nome da rede é `<projeto>_kafka-iot`, e no compose da Aula 3 o projeto leva o nome da pasta (`docker`). Confirme com `docker network ls --filter name=kafka-iot`. Se o nome for outro, ajuste o `name:` da rede `aula3-kafka` no [docker-compose.yml](docker-compose.yml).

### 3.2. Subir o Mosquitto e a ponte

```bash
cd ../../Aula_4_esp32_mqtt_kafka
cp .env.example .env            # opcional; PowerShell: Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

O `.env` é opcional: só é preciso se quiser alterar os padrões da tabela da seção 2. Para conferir o que o Compose vai usar:

```bash
docker compose config | grep -E "MQTT_|KAFKA_"
```

Acompanhe os logs:

```bash
docker compose logs -f --tail=20 mosquitto mqtt-kafka-producer
```

A ponte deve registrar:

```text
[mqtt-kafka-producer] starting mqtt -> kafka bridge
[mqtt-kafka-producer] kafka bootstrap servers: kafka:9092
[mqtt-kafka-producer] kafka topic: iot.air_quality
[mqtt-kafka-producer] connected mqtt=mosquitto:1883 subscribed=opaiot/air_quality
```

Saia do `logs -f` com `Ctrl+C` (os containers continuam rodando).

### 3.3. Entender o MQTT com dois terminais

Antes de envolver a ponte, veja o modelo publicador/assinante funcionando só no broker. Os dois terminais entram no container do Mosquitto.

**Terminal A — assinante:**

```shell
docker exec -it opaiot-aula4-mosquitto-1 sh
mosquitto_sub -h localhost -p 1883 -t opaiot/temperature -v
```

**Terminal B — publicador:**

```shell
docker exec -it opaiot-aula4-mosquitto-1 sh
mosquitto_pub -h localhost -p 1883 -t opaiot/temperature -m "25.4"
```

No terminal A deve aparecer `opaiot/temperature 25.4` (a opção `-v` imprime o tópico antes do payload). Publique mais algumas vezes, mudando o valor. Encerre o assinante com `Ctrl+C` e saia do `sh` com `exit`.

Nada disso chega ao Kafka: a ponte assina `opaiot/air_quality`, não `opaiot/temperature`, e o broker só entrega mensagens a quem assinou o tópico. Repare também que `25.4` não é um JSON de objeto; mesmo que a ponte assinasse esse tópico, ela o ignoraria com `ignored non-object json`.

> **Dica:** `opaiot-aula4-mosquitto-1` é `<projeto>-<serviço>-<número>` (o projeto vem do `name: opaiot-aula4` do compose). Sem decorar o nome, rode na pasta desta aula `docker compose exec mosquitto sh`.
>
> **Dica (Windows):** dentro do `sh` do container as aspas funcionam como no Linux, então é o caminho mais simples para publicar JSON sem se preocupar com escape do PowerShell.

### 3.4. Publicar uma mensagem de teste na ponte

Agora publique no tópico que a ponte assina, com um evento no formato da Aula 3. Em Linux, macOS, Git Bash ou PowerShell 7.3+:

```bash
docker compose exec mosquitto mosquitto_pub \
  -h localhost \
  -t 'opaiot/air_quality' \
  -m '{"sensor_id":"sensor-99","room":"lab-99","temperature":28.4,"humidity":61.0,"co2":900}'
```

No **Windows PowerShell 5.1**, as aspas duplas do JSON precisam de barra invertida, em uma única linha (sem isso o broker recebe `{sensor_id:sensor-99,...}` e a ponte registra `invalid json`):

```powershell
docker compose exec mosquitto mosquitto_pub -h localhost -t 'opaiot/air_quality' -m '{\"sensor_id\":\"sensor-99\",\"room\":\"lab-99\",\"temperature\":28.4,\"humidity\":61.0,\"co2\":900}'
```

Use **só uma** das formas conforme o seu shell: no PowerShell 7.3+ a versão com barras quebra o JSON.

Nos logs da ponte aparecem `forwarded mqtt payload=...` (a normalização, na hora) e `sent topic=iot.air_quality partition=... offset=... key=sensor-99` (a confirmação de entrega no Kafka):

```bash
docker compose logs --tail=4 mqtt-kafka-producer
```

> **Atenção:** a linha `sent` de uma mensagem só é impressa quando a **próxima** mensagem chega à ponte. O callback de entrega do producer roda no `poll()`, que a ponte só chama ao publicar. Com uma única mensagem, você verá só o `forwarded`; publique outra (por exemplo, o passo 3.5) para ver o `sent` da primeira, ou confirme direto no consumer, logo abaixo.

Confirme que o evento chegou ao outro lado do pipeline, no consumer da Aula 3:

```bash
docker compose -f ../Aula_3_kafka/docker/docker-compose.yml logs consumer | grep sensor-99
```

A linha mostra `key=sensor-99` e o payload completo — o caminho MQTT → ponte → Kafka → consumer está fechado. Para ler direto do tópico, use a partition indicada na linha `sent` da ponte:

```bash
docker compose -f ../Aula_3_kafka/docker/docker-compose.yml exec kafka \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.air_quality \
  --property print.key=true \
  --partition 0 --from-beginning --max-messages 2
```

> Sem `--partition`, o consumidor lê as três partitions desde o início e a saída vem dominada pelos sensores simulados da Aula 3.

> **Dica:** deixe um terceiro terminal assinando tudo que passa pelo broker enquanto você publica e olha os logs da ponte:
>
> ```bash
> docker compose exec mosquitto mosquitto_sub -h localhost -t 'opaiot/#' -v
> ```
>
> Assim você vê o mesmo payload em três pontos — broker, ponte e Kafka — e identifica em qual deles a mensagem se perdeu.

### 3.5. Testar a normalização

Publique um payload no formato "de dispositivo", sem `sensor_id` nem `co2`:

```bash
docker compose exec mosquitto mosquitto_pub \
  -h localhost \
  -t 'opaiot/air_quality' \
  -m '{"temperature":25.4,"humidity":58.2,"deviceId":"esp32-dht22","location":"sala"}'
```

No Windows PowerShell 5.1, use as barras invertidas como no passo anterior. Verifique nos logs da ponte como os campos foram mapeados:

```bash
docker compose logs --tail=4 mqtt-kafka-producer
```

A linha `forwarded mqtt payload=` mostra o evento já normalizado: `deviceId` virou `sensor_id`, `location` virou `room`, e `co2` (800) e `timestamp` foram preenchidos com os padrões.

Agora um payload que a ponte **não** aceita, sem `humidity`:

```bash
docker compose exec mosquitto mosquitto_pub -h localhost -t 'opaiot/air_quality' -m '{"temperature":25.4}'
```

O log mostra `ignored unsupported payload` e nada é enviado ao Kafka.

### 3.6. Conectar o ESP32 (real ou Wokwi)

1. Descubra o IP da sua máquina na rede local (`ipconfig` no Windows, `ip a` no Linux). O broker está publicado na porta `1883` do host; **não use `localhost`** no firmware.
2. Abra [firmware/esp32_mq7_mqtt.ino](firmware/esp32_mq7_mqtt.ino) e ajuste as constantes do topo: `WIFI_SSID`/`WIFI_PASS`, `MQTT_SERVER` (o IP do passo 1), `MQTT_PORT` (`1883`, ou o `MQTT_HOST_PORT` do seu `.env`) e `SENSOR_ID`. O arquivo do repositório vem com `andromeda.lasdpc.icmc.usp.br` e a porta `20202`: **troque os dois**, senão o ESP32 não chega ao seu Mosquitto. O `MQTT_TOPIC` (`opaiot/air_quality`) já coincide com o da ponte.
3. Grave na placa (ou monte no Wokwi, conforme [firmware/README.md](firmware/README.md)).
4. Libere a porta `1883` no firewall do computador, para conexões vindas da rede local.
5. Acompanhe `docker compose logs -f mqtt-kafka-producer` e o dashboard da Aula 3 em <http://localhost:3000/d/iot-kafka-telemetry> (`admin` / `admin`): as leituras do ESP32 entram no mesmo pipeline dos sensores simulados.

> **Dica (depure em camadas):** se nada aparece no Kafka, verifique um elo por vez — primeiro o broker, com `mosquitto_sub -t 'opaiot/#' -v` (o ESP32 está publicando?), depois os logs da ponte, depois o consumer. A primeira camada sem mensagem mostra onde está o problema.
>
> **Wokwi:** o simulador roda fora da sua máquina, então um IP da rede local só é alcançável por meio do gateway do próprio Wokwi (veja a documentação deles). Sem isso, valide o pipeline com os passos 3.4 e 3.5.

Sem hardware e sem Wokwi, repita o passo 3.4 em um laço para simular um dispositivo (Git Bash/Linux/macOS):

```bash
for i in $(seq 1 20); do
  docker compose exec -T mosquitto mosquitto_pub -h localhost -t 'opaiot/air_quality' \
    -m "{\"sensor_id\":\"sensor-sim\",\"room\":\"lab-sim\",\"temperature\":2$((RANDOM % 10)).$((RANDOM % 10)),\"humidity\":6$((RANDOM % 10)).0,\"co2\":$((700 + RANDOM % 300))}"
  sleep 1
done
```

### 3.7. Encerrar

```bash
docker compose down                                              # stack desta aula
docker compose -f ../Aula_3_kafka/docker/docker-compose.yml down # stack da Aula 3
```

Derrube a stack desta aula **antes** da Aula 3: a rede `docker_kafka-iot` não é removida enquanto a ponte estiver conectada a ela. Para apagar também os dados do Kafka, Prometheus e Grafana, use `down -v` na Aula 3.

### Comandos úteis

| Tarefa | Comando (na pasta desta aula) |
| --- | --- |
| Ver o estado dos serviços | `docker compose ps` |
| Logs ao vivo | `docker compose logs -f --tail=20 mosquitto mqtt-kafka-producer` |
| Aplicar mudança no `.env` | `docker compose up -d` (recria só o que mudou) |
| Reconstruir a ponte após editar o script | `docker compose up --build -d mqtt-kafka-producer` |
| Reiniciar só a ponte | `docker compose restart mqtt-kafka-producer` |
| Shell no broker | `docker compose exec mosquitto sh` |

### Problemas comuns

- `network docker_kafka-iot declared as external, but could not be found`: a stack da Aula 3 precisa estar no ar **antes** (passo 3.1); confira `docker compose ps` lá e o nome da rede com `docker network ls`.
- Ponte com erro de conexão ao Kafka ou `kafka delivery failed` nos logs: confirme com `docker compose config` que `KAFKA_BOOTSTRAP_SERVERS` é `kafka:9092` (um `.env` antigo pode ter outro valor), que a ponte está nas duas redes (`docker inspect opaiot-aula4-mqtt-kafka-producer-1`) e que o container `kafka` está `healthy`.
- `Bind for 0.0.0.0:1883 failed: port is already allocated`: outro Mosquitto usa a porta (por exemplo, a stack da Aula 5). Pare-o com `docker compose down` na pasta dele, ou publique este broker em outra porta do host com `MQTT_HOST_PORT=1884` no `.env` (e use `1884` no firmware e nos clientes do host). A ponte não é afetada, pois fala com `mosquitto:1883` pela rede Docker.
- ESP32 não conecta ao broker: confirme que `MQTT_SERVER` é o IP do host (não `localhost`), que `MQTT_PORT` é a porta publicada (`1883` por padrão) e que o firewall libera a porta.
- Mensagem publicada mas nada no Kafka: veja os logs da ponte. Payloads que não são JSON válido são descartados com `invalid json`; JSON sem `temperature` ou `humidity` é ignorado com `ignored unsupported payload`. No Windows PowerShell 5.1, `invalid json` costuma ser o escape das aspas (passo 3.4).
- `docker exec` não encontra `opaiot-aula4-mosquitto-1`: o nome mudou (Compose v1 usa `_` no lugar de `-`) ou o serviço não está no ar. Use `docker compose exec mosquitto sh`.

## 4. Sugestão de exercícios sobre a prática

1. **Wildcard MQTT.** Altere `MQTT_TOPIC` no `.env` para `opaiot/+/air_quality`, aplique com `docker compose up -d` e faça dispositivos publicarem em `opaiot/<sala>/air_quality`. O que o `+` captura? Como a ponte poderia usar o segmento do tópico como `room`?
2. **Chave e partição.** Publique eventos com três `sensor_id` diferentes pelo passo 3.4 e, no `kafka-console-consumer.sh` com `--property print.partition=true`, confirme que cada sensor cai sempre na mesma partition.
3. **Vários assinantes.** Abra dois terminais assinando `opaiot/air_quality` com `mosquitto_sub` e publique uma mensagem. Quantos recebem? A ponte também recebe? O que isso diz sobre o desacoplamento entre publicador e assinantes?
4. **Resiliência da ponte.** Derrube o Kafka da Aula 3 (`docker compose -f ../Aula_3_kafka/docker/docker-compose.yml stop kafka`) com a ponte rodando, publique algumas mensagens MQTT e religue o Kafka. O que os logs da ponte mostram? As mensagens publicadas durante a queda chegaram? Relacione com QoS do MQTT e entrega do producer Kafka.
5. **Dois dispositivos, um tópico.** Rode o firmware no Wokwi (ou em uma placa) e, ao mesmo tempo, o laço de `mosquitto_pub` do passo 3.6 com outro `sensor_id`. Acompanhe no dashboard da Aula 3 os dois sensores lado a lado.
6. **Desafio.** Edite a ponte para rejeitar leituras fora de faixa física (por exemplo, temperatura fora de -40 a 85 °C) e contar as rejeições em um log próprio. Reconstrua com `docker compose up --build -d mqtt-kafka-producer`. Em que ponto do pipeline essa validação é mais barata: no firmware, na ponte ou no consumer?
