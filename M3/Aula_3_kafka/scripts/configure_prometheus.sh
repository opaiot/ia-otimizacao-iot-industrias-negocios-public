#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${PROMETHEUS_CONFIG:-/etc/prometheus/prometheus.yml}"
JOB_NAME="${PROMETHEUS_JOB_NAME:-iot-kafka-consumers}"
SCRAPE_INTERVAL="${PROMETHEUS_SCRAPE_INTERVAL:-5s}"
PROMETHEUS_STORAGE="${PROMETHEUS_STORAGE:-/var/lib/prometheus}"
PROMETHEUS_LISTEN_ADDRESS="${PROMETHEUS_LISTEN_ADDRESS:-0.0.0.0:9090}"
PROMETHEUS_LOG="${PROMETHEUS_LOG:-prometheus.log}"
RESTART_PROMETHEUS=1
BACKGROUND_PROMETHEUS=0

TARGETS=()

usage() {
  cat <<EOF
Usage:
  ./configure_prometheus.sh [options] [target ...]

Options:
  --config PATH             Prometheus config file. Default: /etc/prometheus/prometheus.yml
  --job-name NAME           Scrape job name. Default: iot-kafka-consumers
  --scrape-interval VALUE   Scrape interval. Default: 5s
  --targets LIST            Comma-separated targets, e.g. localhost:8000,localhost:8001
  --no-restart              Update and validate config, but do not restart Prometheus
  --background              Restart Prometheus with nohup in the background
  -h, --help                Show this help

Examples:
  ./configure_prometheus.sh
  ./configure_prometheus.sh localhost:8000
  ./configure_prometheus.sh --targets localhost:8001,localhost:8002,localhost:8003
  ./configure_prometheus.sh --background

Environment variables:
  PROMETHEUS_CONFIG
  PROMETHEUS_JOB_NAME
  PROMETHEUS_SCRAPE_INTERVAL
  PROMETHEUS_TARGETS
  PROMETHEUS_STORAGE
  PROMETHEUS_LISTEN_ADDRESS
  PROMETHEUS_LOG
EOF
}

add_targets_from_csv() {
  local csv="$1"
  local item

  IFS=',' read -r -a parsed_targets <<< "$csv"
  for item in "${parsed_targets[@]}"; do
    item="${item#"${item%%[![:space:]]*}"}"
    item="${item%"${item##*[![:space:]]}"}"
    if [[ -n "$item" ]]; then
      TARGETS+=("$item")
    fi
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    --job-name)
      JOB_NAME="$2"
      shift 2
      ;;
    --scrape-interval)
      SCRAPE_INTERVAL="$2"
      shift 2
      ;;
    --targets)
      add_targets_from_csv "$2"
      shift 2
      ;;
    --no-restart)
      RESTART_PROMETHEUS=0
      shift
      ;;
    --background)
      BACKGROUND_PROMETHEUS=1
      shift
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
      TARGETS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#TARGETS[@]} -eq 0 && -n "${PROMETHEUS_TARGETS:-}" ]]; then
  add_targets_from_csv "$PROMETHEUS_TARGETS"
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("localhost:8000")
fi

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
else
  SUDO=(sudo)
fi

CONFIG_DIR="$(dirname "$CONFIG_FILE")"
TMP_CONFIG="$(mktemp)"
JOB_BLOCK="$(mktemp)"

cleanup() {
  rm -f "$TMP_CONFIG" "$JOB_BLOCK"
}
trap cleanup EXIT

{
  echo "  - job_name: \"${JOB_NAME}\""
  echo "    scrape_interval: ${SCRAPE_INTERVAL}"
  echo "    static_configs:"
  echo "      - targets:"
  for target in "${TARGETS[@]}"; do
    echo "          - \"${target}\""
  done
} > "$JOB_BLOCK"

"${SUDO[@]}" mkdir -p "$CONFIG_DIR"

if [[ -f "$CONFIG_FILE" ]]; then
  BACKUP_FILE="${CONFIG_FILE}.bak.$(date +%Y%m%d%H%M%S)"
  "${SUDO[@]}" cp "$CONFIG_FILE" "$BACKUP_FILE"
  echo "Backup created: $BACKUP_FILE"

  awk -v job="$JOB_NAME" -v block_file="$JOB_BLOCK" '
    function print_block() {
      while ((getline line < block_file) > 0) {
        print line
      }
      close(block_file)
    }

    function is_top_level(line) {
      return line ~ /^[A-Za-z_][A-Za-z0-9_]*:[[:space:]]*$/
    }

    function is_target_job(line) {
      pattern = "^[[:space:]]*-[[:space:]]+job_name:[[:space:]]*\"?" job "\"?[[:space:]]*$"
      return line ~ pattern
    }

    BEGIN {
      inserted = 0
      skipping = 0
    }

    {
      if (skipping) {
        if ($0 ~ /^[[:space:]]*-[[:space:]]+job_name:/ || is_top_level($0)) {
          skipping = 0
        } else {
          next
        }
      }

      if (!skipping && is_target_job($0)) {
        skipping = 1
        next
      }

      print

      if ($0 ~ /^scrape_configs:[[:space:]]*$/ && !inserted) {
        print_block()
        inserted = 1
      }
    }

    END {
      if (!inserted) {
        print ""
        print "scrape_configs:"
        print_block()
      }
    }
  ' "$CONFIG_FILE" > "$TMP_CONFIG"
else
  cat > "$TMP_CONFIG" <<EOF
global:
  scrape_interval: ${SCRAPE_INTERVAL}

scrape_configs:
EOF
  cat "$JOB_BLOCK" >> "$TMP_CONFIG"
fi

"${SUDO[@]}" cp "$TMP_CONFIG" "$CONFIG_FILE"
echo "Prometheus config updated: $CONFIG_FILE"
echo "Configured job: $JOB_NAME"
echo "Configured targets:"
printf '  - %s\n' "${TARGETS[@]}"

if command -v promtool >/dev/null 2>&1; then
  promtool check config "$CONFIG_FILE"
else
  echo "promtool not found; skipping config validation."
fi

if [[ "$RESTART_PROMETHEUS" -eq 0 ]]; then
  echo "Skipping Prometheus restart because --no-restart was used."
  exit 0
fi

if ! command -v prometheus >/dev/null 2>&1; then
  echo "prometheus command not found."
  echo "Restart it manually using the Aula 1 procedure:"
  echo
  echo "pkill -f prometheus"
  echo "prometheus --config.file=${CONFIG_FILE} --storage.tsdb.path=${PROMETHEUS_STORAGE} --web.listen-address=${PROMETHEUS_LISTEN_ADDRESS}"
  exit 1
fi

PROMETHEUS_CMD=(
  prometheus
  "--config.file=${CONFIG_FILE}"
  "--storage.tsdb.path=${PROMETHEUS_STORAGE}"
  "--web.listen-address=${PROMETHEUS_LISTEN_ADDRESS}"
)

echo
echo "Restarting Prometheus with the Aula 1 procedure."
echo "Stopping current Prometheus process with pkill..."
# The safer pattern avoids killing this script, whose filename also contains "prometheus".
pkill -f '(^|/)prometheus([[:space:]]|$)' || true
sleep 1

if [[ "$BACKGROUND_PROMETHEUS" -eq 1 ]]; then
  echo "Starting Prometheus in background:"
  printf '  %q' "${PROMETHEUS_CMD[@]}"
  echo
  nohup "${PROMETHEUS_CMD[@]}" > "$PROMETHEUS_LOG" 2>&1 &
  echo "Prometheus PID: $!"
  echo "Log file: $PROMETHEUS_LOG"
  echo
  echo "Check targets at: http://localhost:9090/targets"
else
  echo "Starting Prometheus in foreground, as in Aula 1."
  echo "Keep this terminal open while using Prometheus."
  echo "Targets page: http://localhost:9090/targets"
  echo
  printf 'Running:'
  printf ' %q' "${PROMETHEUS_CMD[@]}"
  echo
  "${PROMETHEUS_CMD[@]}"
fi
