# Scripts da prática Kafka IoT

Este diretório contém os scripts da prática **Kafka para telemetria IoT observável**.

O cenário simula sensores ambientais publicando eventos no tópico Kafka `iot.air_quality`. Um consumer Python lê esses eventos, atualiza métricas e expõe um endpoint `/metrics` para coleta pelo Prometheus e visualização no Grafana.

## Arquivos

```text
scripts/
├── producer.py
├── consumer_metrics.py
├── configure_prometheus.sh
├── configure_grafana.sh
├── requirements.txt
└── README.md
```

- `producer.py`: simula sensores IoT e publica eventos no Kafka.
- `consumer_metrics.py`: consome eventos Kafka e expõe métricas Prometheus.
- `configure_prometheus.sh`: configura o Prometheus para coletar o endpoint `/metrics` da prática.
- `configure_grafana.sh`: configura o data source Prometheus no Grafana e importa um dashboard da prática.
- `requirements.txt`: dependências Python da prática.

## 1. Pré-requisitos

Execute a prática em uma VM Ubuntu com:

- Kafka em execução em `localhost:9092`;
- Python 3, `venv` e `pip`;
- `curl`, usado pelos scripts de configuração;
- Prometheus e Grafana instalados, para a parte de observabilidade.

Se ainda não instalou o Kafka, siga antes o roteiro:

```text
../instalando_kafka_vm.md
```

## 2. Preparar o ambiente Python

A partir do diretório da aula:

```bash
cd Modulo_3/Aula_3_kafka
```

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r scripts/requirements.txt
```

## 3. Verificar se o Kafka está rodando

Se o Kafka foi instalado em `/opt/kafka`, em um terminal separado:

```bash
cd /opt/kafka
bin/kafka-server-start.sh config/server.properties
```

Em outro terminal, teste:

```bash
kafka-topics.sh --list --bootstrap-server localhost:9092
```

Se `kafka-topics.sh` não estiver no `PATH`, use:

```bash
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

## 4. Criar o tópico da prática

Crie o tópico com 3 partitions:

```bash
kafka-topics.sh \
  --create \
  --if-not-exists \
  --topic iot.air_quality \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

Verifique a configuração:

```bash
kafka-topics.sh \
  --describe \
  --topic iot.air_quality \
  --bootstrap-server localhost:9092
```

A saída deve indicar:

```text
PartitionCount: 3
ReplicationFactor: 1
```

## 5. Executar o producer

Em um terminal com o ambiente virtual ativo:

```bash
python scripts/producer.py
```

O producer envia um evento por segundo. Cada evento tem este formato lógico:

```json
{
  "sensor_id": "sensor-01",
  "room": "lab-01",
  "temperature": 25.4,
  "humidity": 61.2,
  "co2": 720,
  "timestamp": "2026-06-03T10:15:00+00:00"
}
```

O ponto didático principal é que o script usa `sensor_id` como key da mensagem. Assim, eventos do mesmo sensor tendem a cair na mesma partition.

## 6. Executar um consumer com métricas

Em outro terminal, também com o ambiente virtual ativo:

```bash
python scripts/consumer_metrics.py
```

O consumer usa por padrão:

```text
GROUP_ID=air-quality-processors
METRICS_PORT=8000
```

Verifique as métricas:

```bash
curl http://localhost:8000/metrics
```

Procure métricas como:

```text
iot_events_consumed_total
iot_temperature_celsius
iot_humidity_percent
iot_co2_ppm
iot_events_by_partition_total
iot_kafka_last_offset
```

## 7. Experimento: observar partitions

Com o producer e o consumer rodando, observe no log do consumer:

```text
partition=0 offset=... key=sensor-01
partition=1 offset=... key=sensor-02
partition=2 offset=... key=sensor-03
```

Depois descreva o tópico:

```bash
kafka-topics.sh \
  --describe \
  --topic iot.air_quality \
  --bootstrap-server localhost:9092
```

Discussão esperada:

```text
Kafka distribui eventos entre partitions. Como a key é sensor_id,
leituras do mesmo sensor tendem a permanecer na mesma partition.
```

## 8. Experimento: vários consumers no mesmo grupo

Para rodar vários consumers na mesma máquina, cada processo precisa usar uma porta de métricas diferente.

Terminal 1:

```bash
METRICS_PORT=8001 CONSUMER_ID=consumer-1 python scripts/consumer_metrics.py
```

Terminal 2:

```bash
METRICS_PORT=8002 CONSUMER_ID=consumer-2 python scripts/consumer_metrics.py
```

Terminal 3:

```bash
METRICS_PORT=8003 CONSUMER_ID=consumer-3 python scripts/consumer_metrics.py
```

Todos usam o mesmo grupo padrão:

```text
air-quality-processors
```

Com 3 partitions e 3 consumers, a tendência é cada consumer receber uma partition.

## 9. Experimento: grupos diferentes

Agora execute consumers com grupos diferentes:

```bash
GROUP_ID=air-quality-processors METRICS_PORT=8011 CONSUMER_ID=processors-1 python scripts/consumer_metrics.py
```

```bash
GROUP_ID=air-quality-dashboard METRICS_PORT=8012 CONSUMER_ID=dashboard-1 python scripts/consumer_metrics.py
```

Discussão esperada:

```text
Consumers em grupos diferentes leem o mesmo tópico de forma independente.
Cada grupo mantém seus próprios offsets.
```

## 10. Experimento: parar consumer e observar offset

1. Deixe o producer rodando.
2. Pare o consumer com `Ctrl+C`.
3. Aguarde alguns segundos.
4. Inicie o consumer novamente com o mesmo `GROUP_ID`.

O consumer deve continuar a partir do offset salvo pelo grupo.

Inspecione o grupo:

```bash
kafka-consumer-groups.sh \
  --describe \
  --group air-quality-processors \
  --bootstrap-server localhost:9092
```

Observe especialmente:

```text
CURRENT-OFFSET
LOG-END-OFFSET
LAG
```

## 11. Configurar Prometheus

O procedimento segue a lógica usada na Aula 1: configurar o target no `prometheus.yml`, validar com `promtool check config` e reiniciar o Prometheus.

Para configurar automaticamente o target padrão `localhost:8000`, execute:

```bash
bash scripts/configure_prometheus.sh
```

Execute esse comando na VM Ubuntu onde o Prometheus está instalado, a partir do diretório `Modulo_3/Aula_3_kafka`.

O script faz backup do arquivo atual antes de alterar:

```text
/etc/prometheus/prometheus.yml.bak.<timestamp>
```

Ele adiciona ou atualiza este job:

```yaml
scrape_configs:
  - job_name: "iot-kafka-consumers"
    scrape_interval: 5s
    static_configs:
      - targets:
          - "localhost:8000"
```

Se estiver rodando vários consumers, informe os targets:

```bash
bash scripts/configure_prometheus.sh \
  --targets localhost:8001,localhost:8002,localhost:8003
```

Ou passe os targets como argumentos:

```bash
bash scripts/configure_prometheus.sh localhost:8001 localhost:8002 localhost:8003
```

O resultado esperado no `prometheus.yml` é:

```yaml
scrape_configs:
  - job_name: "iot-kafka-consumers"
    scrape_interval: 5s
    static_configs:
      - targets:
          - "localhost:8001"
          - "localhost:8002"
          - "localhost:8003"
```

Se quiser apenas atualizar e validar a configuração, sem reiniciar o Prometheus:

```bash
bash scripts/configure_prometheus.sh --no-restart
```

Por padrão, depois de validar a configuração, o script reinicia o Prometheus com o procedimento usado na Aula 1:

```bash
pkill -f prometheus
prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/var/lib/prometheus --web.listen-address=0.0.0.0:9090
```

O Prometheus fica rodando em primeiro plano. Deixe esse terminal aberto enquanto usa a interface.

Se quiser iniciar em segundo plano, use:

```bash
bash scripts/configure_prometheus.sh --background
```

Depois confira:

```bash
curl http://localhost:9090/-/healthy
```

Na interface do Prometheus, abra:

```text
http://localhost:9090/targets
```

## 12. Configurar Grafana

Com o Prometheus configurado e o Grafana já instalado na VM, execute:

```bash
bash scripts/configure_grafana.sh
```

Por padrão, o script usa:

```text
Grafana: http://localhost:3000
Usuário: admin
Senha: admin
Prometheus: http://localhost:9090
```

Se sua senha do Grafana já foi alterada:

```bash
GRAFANA_USER=admin \
GRAFANA_PASSWORD='sua-senha' \
bash scripts/configure_grafana.sh
```

Se o Grafana estiver em outra porta:

```bash
bash scripts/configure_grafana.sh --grafana-url http://localhost:3001
```

Se o Grafana precisar acessar o Prometheus por outro endereço:

```bash
bash scripts/configure_grafana.sh --prometheus-url http://localhost:9090
```

O script cria ou atualiza:

- data source `Prometheus - Kafka IoT`;
- pasta `OpAIoT`;
- dashboard `Kafka IoT - Telemetria Observavel`.

Depois acesse:

```text
http://localhost:3000/d/iot-kafka-telemetry
```

Se usar token de API ou service account:

```bash
GRAFANA_API_TOKEN='seu-token' bash scripts/configure_grafana.sh
```

## 13. Consultas PromQL úteis

Total de eventos consumidos:

```promql
iot_events_consumed_total
```

Temperatura por sensor:

```promql
iot_temperature_celsius
```

Umidade por sensor:

```promql
iot_humidity_percent
```

CO2 por sensor:

```promql
iot_co2_ppm
```

Taxa de eventos processados:

```promql
rate(iot_events_consumed_total[1m])
```

Eventos por partition:

```promql
iot_events_by_partition_total
```

Último offset consumido por partition:

```promql
iot_kafka_last_offset
```

## 14. Painéis criados no Grafana

O script `configure_grafana.sh` cria um dashboard com estes painéis:

- temperatura por sensor: `iot_temperature_celsius`;
- umidade por sensor: `iot_humidity_percent`;
- CO2 por sensor: `iot_co2_ppm`;
- taxa de eventos: `rate(iot_events_consumed_total[1m])`;
- eventos por partition: `iot_events_by_partition_total`;
- último offset consumido: `iot_kafka_last_offset`;
- total de eventos consumidos: `sum(iot_events_consumed_total)`.

## 15. Configuração por variáveis de ambiente

Variáveis dos scripts Python:

```text
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=iot.air_quality
SEND_INTERVAL_SECONDS=1
GROUP_ID=air-quality-processors
AUTO_OFFSET_RESET=earliest
METRICS_PORT=8000
CONSUMER_ID=<hostname>:<port>
```

Variáveis do script do Grafana:

```text
GRAFANA_URL=http://localhost:3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
GRAFANA_API_TOKEN=
PROMETHEUS_URL=http://localhost:9090
GRAFANA_DATASOURCE_NAME=Prometheus - Kafka IoT
GRAFANA_DATASOURCE_UID=prometheus-kafka-iot
GRAFANA_FOLDER_UID=opaiot
GRAFANA_FOLDER_TITLE=OpAIoT
GRAFANA_DASHBOARD_UID=iot-kafka-telemetry
GRAFANA_DASHBOARD_TITLE=Kafka IoT - Telemetria Observavel
```

Exemplo:

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
KAFKA_TOPIC=iot.air_quality \
SEND_INTERVAL_SECONDS=0.5 \
python scripts/producer.py
```

## 16. Problemas comuns

Se aparecer `ModuleNotFoundError: No module named 'confluent_kafka'`, ative o ambiente virtual e reinstale:

```bash
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

Se aparecer erro de porta em uso, troque a porta do consumer:

```bash
METRICS_PORT=8004 CONSUMER_ID=consumer-4 python scripts/consumer_metrics.py
```

Se o tópico já existir, use `--if-not-exists` no comando de criação ou apenas descreva o tópico existente.

Se o consumer não receber eventos, verifique:

```bash
kafka-topics.sh --list --bootstrap-server localhost:9092
kafka-consumer-groups.sh --list --bootstrap-server localhost:9092
```

E confirme que o producer está publicando no mesmo tópico usado pelo consumer.

Se o script do Grafana retornar erro de autenticação, confirme usuário e senha:

```bash
GRAFANA_USER=admin GRAFANA_PASSWORD='sua-senha' bash scripts/configure_grafana.sh
```

Se o Grafana não conseguir consultar o Prometheus, confira a URL configurada no data source. Em uma instalação direta na VM, normalmente é:

```text
http://localhost:9090
```

Se o Grafana estiver em container, `localhost` dentro do container aponta para o próprio container. Nesse caso, use um endereço acessível ao container, por exemplo `host.docker.internal:9090` quando configurado:

```bash
bash scripts/configure_grafana.sh --prometheus-url http://host.docker.internal:9090
```
