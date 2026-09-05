import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/device-001/telemetry")
DEVICE_ID = os.getenv("DEVICE_ID", "device-001")
PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "2"))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_payload() -> dict:
    base_temperature = 25.0 + random.uniform(-2.5, 2.5)
    base_humidity = 60.0 + random.uniform(-8.0, 8.0)
    vibration = max(0.0, random.gauss(0.08, 0.03))

    return {
        "device_id": DEVICE_ID,
        "timestamp": utc_now(),
        "temperature": round(base_temperature, 2),
        "humidity": round(min(max(base_humidity, 20.0), 95.0), 2),
        "vibration": round(min(vibration, 1.0), 4),
    }


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[sensor] connected mqtt={MQTT_HOST}:{MQTT_PORT} topic={MQTT_TOPIC}", flush=True)
    else:
        print(f"[sensor] mqtt connection failed rc={rc}", flush=True)


def on_disconnect(client, userdata, rc):
    print(f"[sensor] disconnected rc={rc}; paho will retry", flush=True)


def connect_with_retry(client: mqtt.Client) -> None:
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
            return
        except OSError as exc:
            print(f"[sensor] waiting for mqtt broker: {exc}", flush=True)
            time.sleep(3)


def main() -> None:
    client_id = f"sensor-{DEVICE_ID}-{random.randint(1000, 9999)}"
    client = mqtt.Client(client_id=client_id)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    connect_with_retry(client)
    client.loop_start()

    while True:
        payload = make_payload()
        try:
            result = client.publish(MQTT_TOPIC, json.dumps(payload), qos=0)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[sensor] published device_id={DEVICE_ID} payload={payload}", flush=True)
            else:
                print(f"[sensor] publish returned rc={result.rc}", flush=True)
        except Exception as exc:
            print(f"[sensor] publish error: {exc}", flush=True)

        time.sleep(PUBLISH_INTERVAL)


if __name__ == "__main__":
    main()
