import hashlib
import hmac
import json
import os
import random
import signal
import ssl
import threading
import time

import paho.mqtt.client as mqtt

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", "8883"))
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]
HMAC_KEY = bytes.fromhex(os.environ["HMAC_KEY_HEX"])

DEVICE_COUNT = int(os.environ.get("SIM_DEVICE_COUNT", "5"))
DEVICE_PREFIX = os.environ.get("SIM_DEVICE_PREFIX", "esp32-sim")
TOPIC_PREFIX = os.environ.get("SIM_TOPIC_PREFIX", "sensors/sim")
PUBLISH_INTERVAL = float(os.environ.get("SIM_PUBLISH_INTERVAL_SECONDS", "5"))

CA_CERT_PATH = "/certs/ca.crt"

stop_event = threading.Event()


def sign(device: str, seq: int, temp: str) -> str:
    message = f"{device}|{seq}|{temp}".encode()
    return hmac.new(HMAC_KEY, message, hashlib.sha256).hexdigest()


def device_loop(client: mqtt.Client, device_id: str) -> None:
    # Cada "dispositivo" simulado assina os dados exatamente como o firmware
    # esp32/esp32.ino faria: HMAC-SHA256("<device>|<seq>|<temp>", chave_compartilhada).
    seq = 0
    base_temp = random.uniform(20.0, 28.0)
    topic = f"{TOPIC_PREFIX}/{device_id}/data"

    while not stop_event.is_set():
        seq += 1
        temp_str = f"{base_temp + random.uniform(-1.0, 1.0):.2f}"
        payload = json.dumps(
            {
                "device": device_id,
                "seq": seq,
                "temp": temp_str,
                "hmac": sign(device_id, seq, temp_str),
            }
        )
        client.publish(topic, payload)
        print(f"[{device_id}] seq={seq} temp={temp_str} -> {topic}", flush=True)
        stop_event.wait(PUBLISH_INTERVAL)


def handle_shutdown(signum, frame):
    stop_event.set()


def main():
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set(ca_certs=CA_CERT_PATH, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    print(
        f"[SIMULADOR] {DEVICE_COUNT} dispositivo(s) publicando em "
        f"{TOPIC_PREFIX}/<device>/data a cada {PUBLISH_INTERVAL}s",
        flush=True,
    )

    threads = [
        threading.Thread(
            target=device_loop,
            args=(client, f"{DEVICE_PREFIX}-{i:02d}"),
            daemon=True,
        )
        for i in range(1, DEVICE_COUNT + 1)
    ]
    for t in threads:
        t.start()

    while not stop_event.is_set():
        time.sleep(1)

    for t in threads:
        t.join(timeout=2)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
