# Prática 4 - MQTT para Kafka

Esta aula conecta telemetria MQTT ao tópico Kafka `iot.air_quality` da [Aula 3](../Aula_3_kafka/README.md), mantendo o mesmo formato de evento usado pelo `producer.py` da prática anterior. Toda a prática roda localmente com Docker; o dispositivo pode ser um ESP32 real, o simulador Wokwi ou uma publicação manual de teste.

## 1. Objetivo da prática

Ao final da prática, você deve conseguir:

- explicar por que dispositivos IoT publicam em MQTT e por que o backend consome de Kafka, e o papel de uma **ponte** entre os dois;
- subir um broker Mosquitto e a ponte MQTT → Kafka com Docker Compose, conectando-a ao Kafka da Aula 3;
- normalizar payloads MQTT heterogêneos para o schema de evento da Aula 3;
- validar o caminho completo dispositivo → MQTT → Kafka → consumer.

## 2. Conceitos da prática

**MQTT na borda, Kafka no backend.** MQTT é leve, tolera conexões instáveis e funciona bem em microcontroladores; Kafka dá durabilidade, particionamento, consumo paralelo e retenção para os sistemas que processam os dados. A ponte (`scripts/mqtt_kafka_producer.py`) assina um tópico MQTT, normaliza o payload e publica no Kafka com `sensor_id` como **chave** — exatamente como o producer da Aula 3, preservando a ordem por sensor.

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

## 3. Prática passo a passo

Pré-requisitos: Docker com Docker Compose v2. Para o dispositivo real: ESP32 com DHT22 e MQ-7, ou um projeto Wokwi.

### 3.1. Subir o Kafka da Aula 3

```bash
cd M3/Aula_3_kafka/docker
docker compose up --build -d
```

Isso sobe o broker, o tópico `iot.air_quality`, o consumer e a observabilidade da Aula 3, além de criar a rede Docker que a ponte desta aula vai usar. Se este passo for pulado, o compose do passo seguinte falha com `network opaiot-aula3_kafka-iot not found`.

### 3.2. Subir o Mosquitto e a ponte

```bash
cd ../../Aula_4_esp32_mqtt_kafka
cp .env.example .env     # opcional; só é preciso se quiser alterar os padrões
docker compose up --build -d
```

Acompanhe os logs:

```bash
docker compose logs -f --tail=20 mosquitto mqtt-kafka-producer
```

A ponte deve registrar a conexão ao MQTT (`subscribed=opaiot/air_quality`) e ao Kafka.

### 3.3. Publicar uma mensagem de teste

Antes de envolver hardware, valide o caminho com uma publicação manual:

```bash
docker compose exec mosquitto mosquitto_pub \
  -h localhost \
  -t 'opaiot/air_quality' \
  -m '{"sensor_id":"sensor-99","room":"lab-99","temperature":28.4,"humidity":61.0,"co2":900}'
```

Nos logs da ponte devem aparecer duas linhas: `forwarded mqtt payload=...` (a normalização) e `sent topic=iot.air_quality partition=... offset=... key=sensor-99` (a publicação no Kafka).

Confirme que o evento chegou ao outro lado do pipeline, no consumer da Aula 3:

```bash
docker compose -f ../Aula_3_kafka/docker/docker-compose.yml logs consumer | grep sensor-99
```

A linha mostra `key=sensor-99` e o payload completo — o caminho MQTT → ponte → Kafka → consumer está fechado. Para ler direto do tópico, use a partition indicada no log da ponte:

```bash
docker compose -f ../Aula_3_kafka/docker/docker-compose.yml exec kafka \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.air_quality \
  --property print.key=true \
  --partition 0 --from-beginning --max-messages 2
```

> Sem `--partition`, o consumidor lê as três partitions desde o início e a saída vem dominada pelos sensores simulados da Aula 3.

### 3.4. Testar a normalização

Publique um payload no formato "de dispositivo", sem `sensor_id` nem `co2`:

```bash
docker compose exec mosquitto mosquitto_pub \
  -h localhost \
  -t 'opaiot/air_quality' \
  -m '{"temperature":25.4,"humidity":58.2,"deviceId":"esp32-dht22","location":"sala"}'
```

Verifique nos logs da ponte como os campos foram mapeados:

```bash
docker compose logs --tail=4 mqtt-kafka-producer
```

A linha `forwarded mqtt payload=` mostra o evento já normalizado: `deviceId` virou `sensor_id`, `location` virou `room`, e `co2` (800) e `timestamp` foram preenchidos com os padrões.

### 3.5. Conectar o ESP32 (real ou Wokwi)

1. Abra [firmware/esp32_mq7_mqtt.ino](firmware/esp32_mq7_mqtt.ino) e configure o Wi-Fi e `MQTT_SERVER` com o **IP da sua máquina** na rede local (`ipconfig` no Windows, `ip a` no Linux) — o broker está publicado na porta `1883` do host.
2. Grave na placa (ou monte no Wokwi, conforme [firmware/README.md](firmware/README.md)).
3. Acompanhe `docker compose logs -f mqtt-kafka-producer` e o dashboard da Aula 3 em <http://localhost:3000/d/iot-kafka-telemetry>: as leituras do ESP32 entram no mesmo pipeline dos sensores simulados.

Sem hardware e sem Wokwi, repita o passo 3.3 em um laço para simular um dispositivo.

### 3.6. Encerrar

```bash
docker compose down                                              # stack desta aula
docker compose -f ../Aula_3_kafka/docker/docker-compose.yml down # stack da Aula 3
```

### Problemas comuns

- Ponte com erro de conexão ao Kafka: a stack da Aula 3 precisa estar no ar **antes** (passo 3.1); confira `docker compose ps` lá.
- ESP32 não conecta ao broker: confirme que `MQTT_SERVER` é o IP do host (não `localhost`) e que o firewall libera a porta `1883`.
- Mensagem publicada mas nada no Kafka: veja os logs da ponte; payloads que não são JSON válido são descartados com aviso.

## 4. Sugestão de exercícios sobre a prática

1. **Wildcard MQTT.** Altere `MQTT_TOPIC` no `.env` para `opaiot/+/air_quality` e faça dispositivos publicarem em `opaiot/<sala>/air_quality`. O que o `+` captura? Como a ponte poderia usar o segmento do tópico como `room`?
2. **Chave e partição.** Publique eventos com três `sensor_id` diferentes pelo passo 3.3 e, no `kafka-console-consumer.sh` com `--property print.partition=true`, confirme que cada sensor cai sempre na mesma partition.
3. **Resiliência da ponte.** Derrube o Kafka da Aula 3 (`docker compose stop kafka`) com a ponte rodando, publique algumas mensagens MQTT e religue o Kafka. O que os logs da ponte mostram? As mensagens publicadas durante a queda chegaram? Relacione com QoS do MQTT e entrega do producer Kafka.
4. **Dois dispositivos, um tópico.** Rode o firmware no Wokwi e, ao mesmo tempo, o laço de `mosquitto_pub` com outro `sensor_id`. Acompanhe no dashboard da Aula 3 os dois sensores lado a lado.
5. **Desafio.** Edite a ponte para rejeitar leituras fora de faixa física (por exemplo, temperatura fora de -40 a 85 °C) e contar as rejeições em um log próprio. Em que ponto do pipeline essa validação é mais barata: no firmware, na ponte ou no consumer?
