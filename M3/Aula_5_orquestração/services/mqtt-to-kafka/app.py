import json
import os
import time
from typing import Optional

import paho.mqtt.client as mqtt
from kafka import KafkaProducer


MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/+/telemetry")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot.telemetry")

producer: Optional[KafkaProducer] = None


def log(message: str) -> None:
    print(f"[mqtt-to-kafka] {message}", flush=True)


def create_kafka_producer() -> KafkaProducer:
    while True:
        try:
            candidate = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                key_serializer=lambda value: value.encode("utf-8") if value else None,
                value_serializer=lambda value: json.dumps(value, separators=(",", ":")).encode("utf-8"),
                retries=5,
                linger_ms=50,
                request_timeout_ms=10000,
                api_version_auto_timeout_ms=10000,
            )

            for _ in range(10):
                if candidate.bootstrap_connected():
                    log(f"connected kafka={KAFKA_BOOTSTRAP_SERVERS} topic={KAFKA_TOPIC}")
                    return candidate
                time.sleep(1)

            candidate.close()
            raise RuntimeError("bootstrap not connected yet")
        except Exception as exc:
            log(f"waiting for kafka: {exc}")
            time.sleep(5)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        log(f"connected mqtt={MQTT_HOST}:{MQTT_PORT} subscribed={MQTT_TOPIC}")
    else:
        log(f"mqtt connection failed rc={rc}")


def on_disconnect(client, userdata, rc):
    log(f"mqtt disconnected rc={rc}; client will retry")


def on_message(client, userdata, message):
    global producer

    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        log(f"invalid json mqtt_topic={message.topic}: {exc}")
        return

    if not isinstance(payload, dict):
        log(f"ignored non-object json mqtt_topic={message.topic}")
        return

    device_id = str(payload.get("device_id") or "unknown")

    if producer is None:
        producer = create_kafka_producer()

    try:
        metadata = producer.send(KAFKA_TOPIC, key=device_id, value=payload).get(timeout=10)
        log(
            "forwarded "
            f"mqtt_topic={message.topic} kafka_topic={metadata.topic} "
            f"partition={metadata.partition} offset={metadata.offset} device_id={device_id}"
        )
    except Exception as exc:
        log(f"kafka send failed device_id={device_id}: {exc}")
        try:
            producer.close(timeout=2)
        except Exception:
            pass
        producer = create_kafka_producer()


def connect_mqtt_with_retry(client: mqtt.Client) -> None:
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
            return
        except OSError as exc:
            log(f"waiting for mqtt broker: {exc}")
            time.sleep(3)


def main() -> None:
    global producer

    producer = create_kafka_producer()

    client = mqtt.Client(client_id="mqtt-to-kafka")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    connect_mqtt_with_retry(client)
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()
