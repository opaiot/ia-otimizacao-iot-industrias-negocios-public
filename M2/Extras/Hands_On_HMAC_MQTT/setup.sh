#!/usr/bin/env bash
# Gera certificados TLS, credenciais MQTT e a chave HMAC compartilhada
# usadas pelo broker, pelo subscriber e pelo firmware do ESP32.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Uso: $0 <ip-do-host-docker>" >&2
  echo "Exemplo: $0 192.168.1.50" >&2
  exit 1
fi

HOST_IP="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CERTS_DIR="$ROOT_DIR/mosquitto/certs"
CONFIG_DIR="$ROOT_DIR/mosquitto/config"
ESP32_DIR="$ROOT_DIR/esp32"
SUBSCRIBER_DIR="$ROOT_DIR/subscriber"
SIMULATOR_DIR="$ROOT_DIR/simulator"
ATTACKER_DIR="$ROOT_DIR/attacker"
DASHBOARD_DIR="$ROOT_DIR/dashboard"

MOSQUITTO_IMAGE="eclipse-mosquitto:2.0.18"
DEVICE_ID="esp32-01"
MQTT_PUBLISHER_USER="$DEVICE_ID"
MQTT_SUBSCRIBER_USER="subscriber"
MQTT_SIMULATOR_USER="simulator"
MQTT_ATTACKER_USER="attacker"
MQTT_DASHBOARD_USER="dashboard"

HOST_UID="$(id -u)"
HOST_GID="$(id -g)"

mkdir -p "$CERTS_DIR" "$CONFIG_DIR" "$ESP32_DIR" "$SUBSCRIBER_DIR" "$SIMULATOR_DIR" "$ATTACKER_DIR" "$DASHBOARD_DIR"

echo "==> Escrevendo $ROOT_DIR/.env (UID/GID do host, nº de dispositivos e porta do painel)"
cat > "$ROOT_DIR/.env" <<EOF
UID=$HOST_UID
GID=$HOST_GID
SIM_DEVICE_COUNT=5
DASHBOARD_PORT=8080
EOF

echo "==> Gerando CA e certificado do broker para IP $HOST_IP"

openssl genrsa -out "$CERTS_DIR/ca.key" 4096
openssl req -x509 -new -nodes -key "$CERTS_DIR/ca.key" -sha256 -days 3650 \
  -subj "/CN=ESP32-MQTT-Lab-CA" -out "$CERTS_DIR/ca.crt"

openssl genrsa -out "$CERTS_DIR/server.key" 2048
openssl req -new -key "$CERTS_DIR/server.key" -subj "/CN=$HOST_IP" \
  -out "$CERTS_DIR/server.csr"

cat > "$CERTS_DIR/server.ext" <<EOF
# IP:$HOST_IP -> usado pelo ESP32 na rede local
# DNS:broker  -> usado pelo subscriber dentro da rede Docker (mqttnet)
subjectAltName = IP:$HOST_IP,DNS:broker
extendedKeyUsage = serverAuth
EOF

openssl x509 -req -in "$CERTS_DIR/server.csr" -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" \
  -CAcreateserial -out "$CERTS_DIR/server.crt" -days 825 -sha256 \
  -extfile "$CERTS_DIR/server.ext"

rm -f "$CERTS_DIR/server.csr" "$CERTS_DIR/server.ext" "$CERTS_DIR/ca.srl"
chmod 644 "$CERTS_DIR"/*.crt
chmod 600 "$CERTS_DIR"/*.key

echo "==> Gerando credenciais MQTT (usuário/senha)"

MQTT_PUBLISHER_PASS="$(openssl rand -base64 18)"
MQTT_SUBSCRIBER_PASS="$(openssl rand -base64 18)"
MQTT_SIMULATOR_PASS="$(openssl rand -base64 18)"
MQTT_ATTACKER_PASS="$(openssl rand -base64 18)"
MQTT_DASHBOARD_PASS="$(openssl rand -base64 18)"

rm -f "$CONFIG_DIR/passwd"
docker run --rm --user "$HOST_UID:$HOST_GID" -v "$CONFIG_DIR:/out" "$MOSQUITTO_IMAGE" \
  sh -c "mosquitto_passwd -b -c /out/passwd '$MQTT_PUBLISHER_USER' '$MQTT_PUBLISHER_PASS'"
docker run --rm --user "$HOST_UID:$HOST_GID" -v "$CONFIG_DIR:/out" "$MOSQUITTO_IMAGE" \
  sh -c "mosquitto_passwd -b /out/passwd '$MQTT_SUBSCRIBER_USER' '$MQTT_SUBSCRIBER_PASS'"
docker run --rm --user "$HOST_UID:$HOST_GID" -v "$CONFIG_DIR:/out" "$MOSQUITTO_IMAGE" \
  sh -c "mosquitto_passwd -b /out/passwd '$MQTT_SIMULATOR_USER' '$MQTT_SIMULATOR_PASS'"
docker run --rm --user "$HOST_UID:$HOST_GID" -v "$CONFIG_DIR:/out" "$MOSQUITTO_IMAGE" \
  sh -c "mosquitto_passwd -b /out/passwd '$MQTT_ATTACKER_USER' '$MQTT_ATTACKER_PASS'"
docker run --rm --user "$HOST_UID:$HOST_GID" -v "$CONFIG_DIR:/out" "$MOSQUITTO_IMAGE" \
  sh -c "mosquitto_passwd -b /out/passwd '$MQTT_DASHBOARD_USER' '$MQTT_DASHBOARD_PASS'"

echo "==> Gerando chave HMAC-SHA256 compartilhada (broker não a conhece)"
HMAC_KEY_HEX="$(openssl rand -hex 32)"

echo "==> Escrevendo $SUBSCRIBER_DIR/.env"
cat > "$SUBSCRIBER_DIR/.env" <<EOF
MQTT_HOST=broker
MQTT_PORT=8883
MQTT_USER=$MQTT_SUBSCRIBER_USER
MQTT_PASSWORD=$MQTT_SUBSCRIBER_PASS
MQTT_TOPIC=sensors/#
HMAC_KEY_HEX=$HMAC_KEY_HEX
EOF

echo "==> Escrevendo $SIMULATOR_DIR/.env"
cat > "$SIMULATOR_DIR/.env" <<EOF
MQTT_HOST=broker
MQTT_PORT=8883
MQTT_USER=$MQTT_SIMULATOR_USER
MQTT_PASSWORD=$MQTT_SIMULATOR_PASS
HMAC_KEY_HEX=$HMAC_KEY_HEX
SIM_DEVICE_PREFIX=esp32-sim
SIM_TOPIC_PREFIX=sensors/sim
SIM_PUBLISH_INTERVAL_SECONDS=5
EOF

echo "==> Escrevendo $ATTACKER_DIR/.env"
# Propositalmente SEM HMAC_KEY_HEX: o agente malicioso não recebe a chave
# real, só credenciais MQTT válidas (para simular um cliente comprometido).
cat > "$ATTACKER_DIR/.env" <<EOF
MQTT_HOST=broker
MQTT_PORT=8883
MQTT_USER=$MQTT_ATTACKER_USER
MQTT_PASSWORD=$MQTT_ATTACKER_PASS
ATTACKER_SNIFF_TOPIC=sensors/#
ATTACKER_REPLAY_DELAY_SECONDS=3
ATTACKER_CONTROL_TOPIC=control/attacker
EOF

echo "==> Escrevendo $DASHBOARD_DIR/.env"
cat > "$DASHBOARD_DIR/.env" <<EOF
MQTT_HOST=broker
MQTT_PORT=8883
MQTT_USER=$MQTT_DASHBOARD_USER
MQTT_PASSWORD=$MQTT_DASHBOARD_PASS
HMAC_KEY_HEX=$HMAC_KEY_HEX
SENSOR_TOPIC=sensors/#
ATTACKER_CONTROL_TOPIC=control/attacker
HTTP_PORT=8080
EOF

echo "==> Escrevendo $ESP32_DIR/secrets.h"
cat > "$ESP32_DIR/secrets.h" <<EOF
// Gerado por setup.sh em $(date -u +"%Y-%m-%dT%H:%M:%SZ") - NÃO versionar.
#pragma once

// Wi-Fi - edite com a sua rede antes de gravar o firmware
#define WIFI_SSID     "SUA_REDE_WIFI"
#define WIFI_PASSWORD "SUA_SENHA_WIFI"

// Broker MQTT
#define MQTT_HOST     "$HOST_IP"
#define MQTT_PORT     8883
#define MQTT_USER     "$MQTT_PUBLISHER_USER"
#define MQTT_PASSWORD "$MQTT_PUBLISHER_PASS"
#define DEVICE_ID     "$DEVICE_ID"
#define MQTT_TOPIC    "sensors/$DEVICE_ID/data"

// Chave HMAC-SHA256 compartilhada com o subscriber (32 bytes em hex).
// O broker MQTT nunca precisa conhecer esta chave.
#define HMAC_KEY_HEX  "$HMAC_KEY_HEX"
EOF

echo "==> Escrevendo $ESP32_DIR/ca_cert.h"
{
  echo "// Gerado por setup.sh - NÃO versionar."
  echo "#pragma once"
  echo ""
  echo "static const char CA_CERT[] PROGMEM = R\"EOF2("
  cat "$CERTS_DIR/ca.crt"
  echo ")EOF2\";"
} > "$ESP32_DIR/ca_cert.h"

echo
echo "Setup concluído."
echo "  1. Edite $ESP32_DIR/secrets.h com o SSID/senha do Wi-Fi"
echo "  2. docker compose up -d --build"
echo "  3. Abra o painel em http://localhost:8080 para monitorar e ativar o atacante"
echo "  4. Grave esp32/esp32.ino no ESP32 (Arduino IDE + biblioteca PubSubClient)"
