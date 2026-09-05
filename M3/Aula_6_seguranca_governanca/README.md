# OPAIoT - Grafana + Mosquitto MQTT

Este pacote contém um ambiente Docker simples para aula de segurança e governança usando MQTT e Grafana.

## Serviços

- Mosquitto MQTT
  - Porta MQTT: 1883
  - Porta WebSocket: 9001

- Grafana
  - URL: http://localhost:3000
  - Usuário: admin
  - Senha: admin123

## Subir o ambiente

```bash
docker compose up -d
```

## Ver logs

```bash
docker logs -f opaiot-mosquitto
docker logs -f opaiot-grafana
```

## Teste MQTT sem autenticação

Subscriber:

```bash
docker exec -it opaiot-mosquitto mosquitto_sub -h localhost -t "opaiot/#"
```

Publisher:

```bash
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost -t "opaiot/temperature" -m "25.5"
```

## Ativar segurança

O arquivo padrão `mosquitto/config/mosquitto.conf` está configurado com `allow_anonymous true`.

Para ativar autenticação e ACL:

1. Suba o ambiente:

```bash
docker compose up -d
```

2. Crie usuários:

```bash
docker exec -it opaiot-mosquitto mosquitto_passwd -c /mosquitto/config/passwd esp32_pub
docker exec -it opaiot-mosquitto mosquitto_passwd /mosquitto/config/passwd grafana_reader
docker exec -it opaiot-mosquitto mosquitto_passwd /mosquitto/config/passwd admin
```

3. Substitua o conteúdo de:

```text
mosquitto/config/mosquitto.conf
```

pelo conteúdo de:

```text
mosquitto/config/mosquitto-secure.conf
```

4. Reinicie o Mosquitto:

```bash
docker compose restart mosquitto
```

## Teste MQTT com autenticação

Publicação permitida:

```bash
docker exec -it opaiot-mosquitto mosquitto_pub \
  -h localhost \
  -u esp32_pub \
  -P sua_senha \
  -t "opaiot/lab-01/sensor-01/telemetry/temperature" \
  -m "25.5"
```

Leitura permitida:

```bash
docker exec -it opaiot-mosquitto mosquitto_sub \
  -h localhost \
  -u grafana_reader \
  -P sua_senha \
  -t "opaiot/#"
```

Publicação bloqueada para `esp32_pub`:

```bash
docker exec -it opaiot-mosquitto mosquitto_pub \
  -h localhost \
  -u esp32_pub \
  -P sua_senha \
  -t "opaiot/lab-01/ac-01/command/setpoint" \
  -m "18"
```

## Observação

O Grafana não consome MQTT diretamente como fonte nativa principal. Para gráficos reais, use uma camada intermediária, por exemplo:

- MQTT -> Telegraf -> InfluxDB -> Grafana
- MQTT -> Python Bridge -> Prometheus -> Grafana
- MQTT -> Node-RED -> InfluxDB/Prometheus -> Grafana

Este pacote é focado em demonstrar:

- autenticação MQTT;
- ACL por tópico;
- organização de tópicos;
- uso do Grafana como camada visual e de governança.
