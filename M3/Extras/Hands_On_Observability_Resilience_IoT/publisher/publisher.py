"""Publisher de telemetria simulada para o laboratório de observabilidade e
resiliência.

Publica, a uma taxa configurável, medições de um sensor simulado no tópico
MQTT ``iot/telemetry`` (QoS 1) e expõe métricas Prometheus em ``:9100``.

Variáveis de ambiente:
    MQTT_HOST      host do broker (padrão: mosquitto)
    MQTT_PORT      porta do broker (padrão: 1883)
    MQTT_TOPIC     tópico de publicação (padrão: iot/telemetry)
    DEVICE_ID      identificador do dispositivo simulado (padrão: esp32-sim-01)
    RATE           mensagens por segundo (padrão: 2)
    DURATION       se definido, publica por N segundos e encerra; caso
                   contrário publica indefinidamente (usado pelo ``make burst``
                   para injetar uma rajada sem derrubar o publisher principal)
    METRICS_PORT   porta do endpoint /metrics (padrão: 9100)
"""
import json
import os
import random
import signal
import sys
import time

import paho.mqtt.client as mqtt
from prometheus_client import Counter, Gauge, start_http_server

MQTT_HOST = os.environ.get("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "iot/telemetry")
DEVICE_ID = os.environ.get("DEVICE_ID", "esp32-sim-01")
RATE = float(os.environ.get("RATE", "2"))
DURATION = os.environ.get("DURATION")
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9100"))

iot_mqtt_connected = Gauge("iot_mqtt_connected", "1 se o publisher está conectado ao broker, 0 caso contrário")
iot_generated_total = Counter("iot_generated_total", "Total de medições geradas pelo publisher")

_running = True


def _handle_signal(signum, frame):
    global _running
    _running = False


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


def on_connect(client, userdata, flags, reason_code, properties=None):
    iot_mqtt_connected.set(1)
    print(f"[publisher:{DEVICE_ID}] conectado ao broker {MQTT_HOST}:{MQTT_PORT}", flush=True)


def on_disconnect(client, userdata, flags, reason_code=None, properties=None):
    iot_mqtt_connected.set(0)
    print(f"[publisher:{DEVICE_ID}] desconectado (reason_code={reason_code})", flush=True)


def make_payload(seq: int) -> dict:
    return {
        "device": DEVICE_ID,
        "seq": seq,
        "temperature": round(22.0 + random.uniform(-1.5, 1.5), 1),
        "timestamp": time.time(),
    }


def main():
    start_http_server(METRICS_PORT)
    print(f"[publisher:{DEVICE_ID}] métricas em :{METRICS_PORT}/metrics, taxa={RATE} msg/s, "
          f"duração={'infinita' if DURATION is None else DURATION + 's'}", flush=True)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"publisher-{DEVICE_ID}")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=10)
    for attempt in range(30):
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=10)
            break
        except OSError as exc:
            print(f"[publisher:{DEVICE_ID}] broker indisponível ({exc}); nova tentativa em 2s", flush=True)
            time.sleep(2)
    else:
        print(f"[publisher:{DEVICE_ID}] não foi possível conectar ao broker; encerrando", flush=True)
        return 1
    client.loop_start()

    seq = 0
    deadline = time.time() + float(DURATION) if DURATION else None
    interval = 1.0 / RATE if RATE > 0 else 1.0

    try:
        while _running:
            if deadline is not None and time.time() >= deadline:
                break
            payload = make_payload(seq)
            seq += 1
            client.publish(MQTT_TOPIC, json.dumps(payload), qos=1)
            # publish() enfileira localmente mesmo sem conexão; só contamos
            # como "gerada" (não necessariamente entregue) — a entrega é
            # responsabilidade do broker e do QoS, não do publisher.
            iot_generated_total.inc()
            time.sleep(interval)
    finally:
        client.loop_stop()
        client.disconnect()
        print(f"[publisher:{DEVICE_ID}] encerrado após {seq} medições geradas", flush=True)


if __name__ == "__main__":
    sys.exit(main())
