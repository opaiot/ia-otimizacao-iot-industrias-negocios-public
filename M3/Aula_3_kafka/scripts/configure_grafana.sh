#!/usr/bin/env bash
set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
GRAFANA_API_TOKEN="${GRAFANA_API_TOKEN:-}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
DATASOURCE_NAME="${GRAFANA_DATASOURCE_NAME:-Prometheus - Kafka IoT}"
DATASOURCE_UID="${GRAFANA_DATASOURCE_UID:-prometheus-kafka-iot}"
FOLDER_UID="${GRAFANA_FOLDER_UID:-opaiot}"
FOLDER_TITLE="${GRAFANA_FOLDER_TITLE:-OpAIoT}"
DASHBOARD_UID="${GRAFANA_DASHBOARD_UID:-iot-kafka-telemetry}"
DASHBOARD_TITLE="${GRAFANA_DASHBOARD_TITLE:-Kafka IoT - Telemetria Observavel}"

usage() {
  cat <<EOF
Usage:
  ./configure_grafana.sh [options]

Options:
  --grafana-url URL          Grafana URL. Default: http://localhost:3000
  --prometheus-url URL       Prometheus URL used by Grafana. Default: http://localhost:9090
  --user USER                Grafana user. Default: admin
  --password PASSWORD        Grafana password. Default: admin
  --api-token TOKEN          Grafana service account/API token
  --datasource-name NAME     Data source name. Default: Prometheus - Kafka IoT
  --datasource-uid UID       Data source UID. Default: prometheus-kafka-iot
  --folder-uid UID           Folder UID. Default: opaiot
  --folder-title TITLE       Folder title. Default: OpAIoT
  --dashboard-uid UID        Dashboard UID. Default: iot-kafka-telemetry
  --dashboard-title TITLE    Dashboard title
  -h, --help                 Show this help

Examples:
  ./configure_grafana.sh
  ./configure_grafana.sh --grafana-url http://localhost:3000 --prometheus-url http://localhost:9090
  GRAFANA_USER=admin GRAFANA_PASSWORD=admin bash scripts/configure_grafana.sh
  GRAFANA_API_TOKEN=... bash scripts/configure_grafana.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --grafana-url)
      GRAFANA_URL="$2"
      shift 2
      ;;
    --prometheus-url)
      PROMETHEUS_URL="$2"
      shift 2
      ;;
    --user)
      GRAFANA_USER="$2"
      shift 2
      ;;
    --password)
      GRAFANA_PASSWORD="$2"
      shift 2
      ;;
    --api-token)
      GRAFANA_API_TOKEN="$2"
      shift 2
      ;;
    --datasource-name)
      DATASOURCE_NAME="$2"
      shift 2
      ;;
    --datasource-uid)
      DATASOURCE_UID="$2"
      shift 2
      ;;
    --folder-uid)
      FOLDER_UID="$2"
      shift 2
      ;;
    --folder-title)
      FOLDER_TITLE="$2"
      shift 2
      ;;
    --dashboard-uid)
      DASHBOARD_UID="$2"
      shift 2
      ;;
    --dashboard-title)
      DASHBOARD_TITLE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      echo "Unexpected argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required. Install it with: sudo apt install -y curl" >&2
  exit 1
fi

CURL_AUTH_ARGS=()
if [[ -n "$GRAFANA_API_TOKEN" ]]; then
  CURL_AUTH_ARGS=(-H "Authorization: Bearer ${GRAFANA_API_TOKEN}")
else
  CURL_AUTH_ARGS=(-u "${GRAFANA_USER}:${GRAFANA_PASSWORD}")
fi

api_request() {
  local method="$1"
  local path="$2"
  local data_file="${3:-}"

  if [[ -n "$data_file" ]]; then
    curl -fsS \
      "${CURL_AUTH_ARGS[@]}" \
      -H "Content-Type: application/json" \
      -X "$method" \
      --data-binary "@${data_file}" \
      "${GRAFANA_URL}${path}"
  else
    curl -fsS \
      "${CURL_AUTH_ARGS[@]}" \
      -H "Content-Type: application/json" \
      -X "$method" \
      "${GRAFANA_URL}${path}"
  fi
}

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

DATASOURCE_PAYLOAD="${TMP_DIR}/datasource.json"
FOLDER_PAYLOAD="${TMP_DIR}/folder.json"
DASHBOARD_PAYLOAD="${TMP_DIR}/dashboard.json"

echo "Checking Grafana at ${GRAFANA_URL}"
api_request GET "/api/health" >/dev/null

cat > "$DATASOURCE_PAYLOAD" <<EOF
{
  "name": "${DATASOURCE_NAME}",
  "uid": "${DATASOURCE_UID}",
  "type": "prometheus",
  "access": "proxy",
  "url": "${PROMETHEUS_URL}",
  "isDefault": false,
  "basicAuth": false,
  "jsonData": {
    "timeInterval": "5s",
    "httpMethod": "GET"
  }
}
EOF

if api_request GET "/api/datasources/uid/${DATASOURCE_UID}" >/dev/null 2>&1; then
  echo "Updating Grafana data source: ${DATASOURCE_NAME}"
  api_request PUT "/api/datasources/uid/${DATASOURCE_UID}" "$DATASOURCE_PAYLOAD" >/dev/null
else
  echo "Creating Grafana data source: ${DATASOURCE_NAME}"
  api_request POST "/api/datasources" "$DATASOURCE_PAYLOAD" >/dev/null
fi

cat > "$FOLDER_PAYLOAD" <<EOF
{
  "uid": "${FOLDER_UID}",
  "title": "${FOLDER_TITLE}"
}
EOF

if api_request GET "/api/folders/${FOLDER_UID}" >/dev/null 2>&1; then
  echo "Grafana folder already exists: ${FOLDER_TITLE}"
else
  echo "Creating Grafana folder: ${FOLDER_TITLE}"
  api_request POST "/api/folders" "$FOLDER_PAYLOAD" >/dev/null
fi

cat > "$DASHBOARD_PAYLOAD" <<EOF
{
  "folderUid": "${FOLDER_UID}",
  "overwrite": true,
  "dashboard": {
    "id": null,
    "uid": "${DASHBOARD_UID}",
    "title": "${DASHBOARD_TITLE}",
    "tags": ["opaiot", "kafka", "iot"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "5s",
    "time": {
      "from": "now-15m",
      "to": "now"
    },
    "templating": {
      "list": []
    },
    "panels": [
      {
        "id": 1,
        "type": "timeseries",
        "title": "Temperatura por sensor",
        "datasource": { "type": "prometheus", "uid": "${DATASOURCE_UID}" },
        "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
        "fieldConfig": {
          "defaults": { "unit": "celsius" },
          "overrides": []
        },
        "targets": [
          {
            "refId": "A",
            "expr": "iot_temperature_celsius",
            "legendFormat": "{{room}} / {{sensor_id}}"
          }
        ]
      },
      {
        "id": 2,
        "type": "timeseries",
        "title": "Umidade por sensor",
        "datasource": { "type": "prometheus", "uid": "${DATASOURCE_UID}" },
        "gridPos": { "h": 8, "w": 8, "x": 8, "y": 0 },
        "fieldConfig": {
          "defaults": { "unit": "percent" },
          "overrides": []
        },
        "targets": [
          {
            "refId": "A",
            "expr": "iot_humidity_percent",
            "legendFormat": "{{room}} / {{sensor_id}}"
          }
        ]
      },
      {
        "id": 3,
        "type": "timeseries",
        "title": "CO2 por sensor",
        "datasource": { "type": "prometheus", "uid": "${DATASOURCE_UID}" },
        "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
        "fieldConfig": {
          "defaults": { "unit": "ppm" },
          "overrides": []
        },
        "targets": [
          {
            "refId": "A",
            "expr": "iot_co2_ppm",
            "legendFormat": "{{room}} / {{sensor_id}}"
          }
        ]
      },
      {
        "id": 4,
        "type": "timeseries",
        "title": "Taxa de eventos consumidos",
        "datasource": { "type": "prometheus", "uid": "${DATASOURCE_UID}" },
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "fieldConfig": {
          "defaults": { "unit": "ops" },
          "overrides": []
        },
        "targets": [
          {
            "refId": "A",
            "expr": "rate(iot_events_consumed_total[1m])",
            "legendFormat": "{{consumer_id}} / {{room}} / {{sensor_id}}"
          }
        ]
      },
      {
        "id": 5,
        "type": "timeseries",
        "title": "Eventos por partition",
        "datasource": { "type": "prometheus", "uid": "${DATASOURCE_UID}" },
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
        "fieldConfig": {
          "defaults": { "unit": "short" },
          "overrides": []
        },
        "targets": [
          {
            "refId": "A",
            "expr": "iot_events_by_partition_total",
            "legendFormat": "consumer={{consumer_id}} partition={{partition}}"
          }
        ]
      },
      {
        "id": 6,
        "type": "timeseries",
        "title": "Ultimo offset consumido",
        "datasource": { "type": "prometheus", "uid": "${DATASOURCE_UID}" },
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 16 },
        "fieldConfig": {
          "defaults": { "unit": "short" },
          "overrides": []
        },
        "targets": [
          {
            "refId": "A",
            "expr": "iot_kafka_last_offset",
            "legendFormat": "consumer={{consumer_id}} partition={{partition}}"
          }
        ]
      },
      {
        "id": 7,
        "type": "stat",
        "title": "Total de eventos consumidos",
        "datasource": { "type": "prometheus", "uid": "${DATASOURCE_UID}" },
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 16 },
        "fieldConfig": {
          "defaults": { "unit": "short" },
          "overrides": []
        },
        "options": {
          "reduceOptions": {
            "values": false,
            "calcs": ["sum"],
            "fields": ""
          },
          "orientation": "auto",
          "textMode": "auto",
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto"
        },
        "targets": [
          {
            "refId": "A",
            "expr": "sum(iot_events_consumed_total)",
            "legendFormat": "eventos"
          }
        ]
      }
    ]
  }
}
EOF

echo "Importing Grafana dashboard: ${DASHBOARD_TITLE}"
api_request POST "/api/dashboards/db" "$DASHBOARD_PAYLOAD" >/dev/null

echo
echo "Grafana configured successfully."
echo "Data source: ${DATASOURCE_NAME} (${DATASOURCE_UID})"
echo "Dashboard: ${GRAFANA_URL}/d/${DASHBOARD_UID}"
