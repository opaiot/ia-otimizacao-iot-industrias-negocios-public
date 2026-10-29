"""Consumer do laboratório de observabilidade e resiliência.

Separa o *callback* MQTT (``on_message``) do processamento real: mensagens
recebidas vão para uma fila interna limitada; um *worker* em outra thread as
retira e processa numa taxa fixa. Se a fila estiver cheia, a mensagem é
descartada e contabilizada — o recebimento/ACK MQTT e o processamento da
aplicação são eventos diferentes.

Variáveis de ambiente:
    MQTT_HOST       host do broker (padrão: mosquitto)
    MQTT_PORT       porta do broker (padrão: 1883)
    MQTT_TOPIC      tópico assinado (padrão: iot/telemetry)
    QUEUE_SIZE      posições da fila interna (padrão: 100)
    PROCESS_RATE    mensagens por segundo que o worker processa (padrão: 10)
    METRICS_PORT    porta do endpoint /metrics (padrão: 9100)
"""
import json
import os
import queue
import threading
import time

import paho.mqtt.client as mqtt
from prometheus_client import Counter, Gauge, Histogram, start_http_server

MQTT_HOST = os.environ.get("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "iot/telemetry")
QUEUE_SIZE = int(os.environ.get("QUEUE_SIZE", "100"))
PROCESS_RATE = float(os.environ.get("PROCESS_RATE", "10"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9100"))

iot_mqtt_connected = Gauge("iot_mqtt_connected", "1 se o consumer está conectado ao broker, 0 caso contrário")
iot_received_total = Counter("iot_received_total", "Total de mensagens recebidas do broker (callback MQTT)")
iot_processed_total = Counter("iot_processed_total", "Total de mensagens efetivamente processadas pelo worker")
iot_dropped_total = Counter("iot_dropped_total", "Total de mensagens descartadas por fila interna cheia")
iot_queue_depth = Gauge("iot_queue_depth", "Tarefas aguardando na fila interna do consumer")
iot_end_to_end_latency_seconds = Histogram(
    "iot_end_to_end_latency_seconds",
    "Tempo entre a geração da medição (timestamp do payload) e o fim do processamento",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)

_q: "queue.Queue[dict]" = queue.Queue(maxsize=QUEUE_SIZE)


def on_connect(client, userdata, flags, reason_code, properties=None):
    iot_mqtt_connected.set(1)
    client.subscribe(MQTT_TOPIC, qos=1)
    print(f"[consumer] conectado ao broker {MQTT_HOST}:{MQTT_PORT}, assinando {MQTT_TOPIC}", flush=True)


def on_disconnect(client, userdata, flags, reason_code=None, properties=None):
    iot_mqtt_connected.set(0)
    print(f"[consumer] desconectado (reason_code={reason_code})", flush=True)


def on_message(client, userdata, msg):
    iot_received_total.inc()
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return
    try:
        _q.put_nowait(payload)
    except queue.Full:
        iot_dropped_total.inc()
    iot_queue_depth.set(_q.qsize())


def worker():
    interval = 1.0 / PROCESS_RATE if PROCESS_RATE > 0 else 0.1
    while True:
        payload = _q.get()
        iot_queue_depth.set(_q.qsize())
        time.sleep(interval)  # simula o custo de processar a medição
        generated_at = payload.get("timestamp")
        if generated_at is not None:
            iot_end_to_end_latency_seconds.observe(max(0.0, time.time() - generated_at))
        iot_processed_total.inc()
        _q.task_done()


def main():
    start_http_server(METRICS_PORT)
    print(f"[consumer] métricas em :{METRICS_PORT}/metrics, fila={QUEUE_SIZE}, "
          f"capacidade={PROCESS_RATE} msg/s", flush=True)

    threading.Thread(target=worker, daemon=True).start()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="consumer")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    for attempt in range(30):
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=10)
            break
        except OSError as exc:
            print(f"[consumer] broker indisponível ({exc}); nova tentativa em 2s", flush=True)
            time.sleep(2)
    else:
        print("[consumer] não foi possível conectar ao broker; encerrando", flush=True)
        return 1

    client.loop_forever()


if __name__ == "__main__":
    main()
