import json
import os
import time
from typing import Any, Optional

from kafka import KafkaConsumer
from prometheus_client import Counter, Gauge, start_http_server


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot.telemetry")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "iot-processor")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))

MESSAGES_TOTAL = Counter("iot_messages_total", "Total de mensagens IoT consumidas do Kafka")
TEMPERATURE = Gauge("iot_temperature_celsius", "Última temperatura recebida em Celsius")
HUMIDITY = Gauge("iot_humidity_percent", "Última umidade recebida em percentual")
VIBRATION = Gauge("iot_vibration_level", "Último nível de vibração recebido")


def log(message: str) -> None:
    print(f"[iot-processor] {message}", flush=True)


def decode_json(raw: bytes) -> Optional[dict[str, Any]]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def create_consumer() -> KafkaConsumer:
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=decode_json,
                api_version_auto_timeout_ms=10000,
            )
            log(
                f"connected kafka={KAFKA_BOOTSTRAP_SERVERS} "
                f"topic={KAFKA_TOPIC} group_id={KAFKA_GROUP_ID}"
            )
            return consumer
        except Exception as exc:
            log(f"waiting for kafka: {exc}")
            time.sleep(5)


def update_metric(metric: Gauge, payload: dict[str, Any], field: str) -> None:
    value = payload.get(field)
    if value is None:
        return

    try:
        metric.set(float(value))
    except (TypeError, ValueError):
        log(f"ignored invalid {field}={value!r}")


def consume_forever() -> None:
    while True:
        consumer = create_consumer()
        try:
            for message in consumer:
                payload = message.value
                if payload is None:
                    log(f"invalid json at offset={message.offset}")
                    continue

                MESSAGES_TOTAL.inc()
                update_metric(TEMPERATURE, payload, "temperature")
                update_metric(HUMIDITY, payload, "humidity")
                update_metric(VIBRATION, payload, "vibration")

                log(
                    "processed "
                    f"topic={message.topic} partition={message.partition} offset={message.offset} "
                    f"device_id={payload.get('device_id', 'unknown')} "
                    f"temperature={payload.get('temperature')} humidity={payload.get('humidity')} "
                    f"vibration={payload.get('vibration')}"
                )
        except Exception as exc:
            log(f"consumer error: {exc}; reconnecting")
            try:
                consumer.close()
            except Exception:
                pass
            time.sleep(5)


def main() -> None:
    start_http_server(METRICS_PORT)
    log(f"metrics listening on :{METRICS_PORT}/metrics")
    consume_forever()


if __name__ == "__main__":
    main()
