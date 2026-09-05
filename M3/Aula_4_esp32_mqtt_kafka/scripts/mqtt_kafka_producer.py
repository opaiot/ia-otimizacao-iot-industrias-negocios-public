import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

import paho.mqtt.client as mqtt
from confluent_kafka import Producer


MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "20202"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "opaiot/air_quality")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS") or os.getenv(
    "KAFKA_EXTERNAL_BOOTSTRAP",
    "localhost:29092",
)
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot.air_quality")

DEFAULT_SENSOR_ID = os.getenv("DEFAULT_SENSOR_ID", "sensor-01")
DEFAULT_ROOM = os.getenv("DEFAULT_ROOM", "lab-01")
DEFAULT_CO2 = int(os.getenv("DEFAULT_CO2", "800"))

producer: Optional[Producer] = None


def log(message: str) -> None:
    print(f"[mqtt-kafka-producer] {message}", flush=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_timestamp(value: Any) -> str:
    if not value:
        return utc_now_iso()

    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return utc_now_iso()

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc).isoformat()


def sensor_id_from_topic(topic: str) -> Optional[str]:
    parts = topic.split("/")
    if len(parts) >= 3 and parts[0] == "iot" and parts[-1] == "telemetry":
        return parts[1]
    return None


def to_air_quality_event(payload: dict[str, Any], mqtt_topic: str) -> Optional[dict[str, Any]]:
    sensor_id = (
        payload.get("sensor_id")
        or payload.get("device_id")
        or payload.get("deviceId")
        or sensor_id_from_topic(mqtt_topic)
        or DEFAULT_SENSOR_ID
    )

    room = payload.get("room") or payload.get("location") or DEFAULT_ROOM

    temperature = payload.get("temperature")
    humidity = payload.get("humidity")
    if temperature is None or humidity is None:
        return None

    try:
        temperature_value = round(float(temperature), 2)
        humidity_value = round(float(humidity), 2)
        co2_value = int(payload.get("co2", DEFAULT_CO2))
    except (TypeError, ValueError):
        return None

    return {
        "sensor_id": str(sensor_id),
        "room": str(room),
        "temperature": temperature_value,
        "humidity": humidity_value,
        "co2": co2_value,
        "timestamp": normalize_timestamp(payload.get("timestamp")),
    }


def delivery_report(err, msg) -> None:
    if err is not None:
        log(f"kafka delivery failed: {err}")
        return

    key = msg.key().decode("utf-8") if msg.key() else ""
    log(
        f"sent topic={msg.topic()} partition={msg.partition()} "
        f"offset={msg.offset()} key={key}"
    )


def create_kafka_producer() -> Producer:
    return Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})


def publish_event(event: dict[str, Any]) -> None:
    global producer

    if producer is None:
        producer = create_kafka_producer()

    key = event["sensor_id"]
    value = json.dumps(event, separators=(",", ":"))

    producer.produce(
        topic=KAFKA_TOPIC,
        key=key,
        value=value,
        callback=delivery_report,
    )
    producer.poll(0)
    log(f"forwarded mqtt payload={value}")


def on_connect(client, userdata, flags, rc) -> None:
    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        log(f"connected mqtt={MQTT_HOST}:{MQTT_PORT} subscribed={MQTT_TOPIC}")
    else:
        log(f"mqtt connection failed rc={rc}")


def on_disconnect(client, userdata, rc) -> None:
    log(f"mqtt disconnected rc={rc}; client will retry")


def on_message(client, userdata, message) -> None:
    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        log(f"invalid json mqtt_topic={message.topic}: {exc}")
        return

    if not isinstance(payload, dict):
        log(f"ignored non-object json mqtt_topic={message.topic}")
        return

    event = to_air_quality_event(payload, message.topic)
    if event is None:
        log(f"ignored unsupported payload mqtt_topic={message.topic} payload={payload}")
        return

    try:
        publish_event(event)
    except Exception as exc:
        log(f"kafka publish error: {exc}")
        global producer
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

    log("starting mqtt -> kafka bridge")
    log(f"kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
    log(f"kafka topic: {KAFKA_TOPIC}")
    log("press Ctrl+C to stop")

    client = mqtt.Client(client_id="mqtt-kafka-producer")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    connect_mqtt_with_retry(client)

    try:
        client.loop_forever(retry_first_connection=True)
    except KeyboardInterrupt:
        log("stopping")
    finally:
        if producer is not None:
            producer.flush(10)


if __name__ == "__main__":
    main()
