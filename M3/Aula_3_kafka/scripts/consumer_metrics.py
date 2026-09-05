import json
import os
import socket

from confluent_kafka import Consumer
from prometheus_client import Counter, Gauge, start_http_server


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "iot.air_quality")
GROUP_ID = os.getenv("GROUP_ID", "air-quality-processors")
AUTO_OFFSET_RESET = os.getenv("AUTO_OFFSET_RESET", "earliest")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))
CONSUMER_ID = os.getenv("CONSUMER_ID", f"{socket.gethostname()}:{METRICS_PORT}")


events_consumed_total = Counter(
    "iot_events_consumed_total",
    "Total IoT events consumed",
    ["consumer_id", "room", "sensor_id"],
)

temperature_gauge = Gauge(
    "iot_temperature_celsius",
    "Last temperature registered by sensor",
    ["room", "sensor_id"],
)

humidity_gauge = Gauge(
    "iot_humidity_percent",
    "Last humidity registered by sensor",
    ["room", "sensor_id"],
)

co2_gauge = Gauge(
    "iot_co2_ppm",
    "Last CO2 measurement registered by sensor",
    ["room", "sensor_id"],
)

events_by_partition_total = Counter(
    "iot_events_by_partition_total",
    "Total IoT events consumed by Kafka partition",
    ["consumer_id", "partition"],
)

last_offset_gauge = Gauge(
    "iot_kafka_last_offset",
    "Last Kafka offset consumed by partition",
    ["consumer_id", "partition"],
)


def build_consumer():
    return Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": GROUP_ID,
            "client.id": CONSUMER_ID,
            "auto.offset.reset": AUTO_OFFSET_RESET,
            "enable.auto.commit": True,
        }
    )


def update_metrics(event, msg):
    sensor_id = event["sensor_id"]
    room = event["room"]
    partition = str(msg.partition())

    events_consumed_total.labels(
        consumer_id=CONSUMER_ID,
        room=room,
        sensor_id=sensor_id,
    ).inc()

    events_by_partition_total.labels(
        consumer_id=CONSUMER_ID,
        partition=partition,
    ).inc()

    temperature_gauge.labels(room=room, sensor_id=sensor_id).set(event["temperature"])
    humidity_gauge.labels(room=room, sensor_id=sensor_id).set(event["humidity"])
    co2_gauge.labels(room=room, sensor_id=sensor_id).set(event["co2"])
    last_offset_gauge.labels(consumer_id=CONSUMER_ID, partition=partition).set(
        msg.offset()
    )


def main():
    consumer = build_consumer()
    consumer.subscribe([TOPIC])
    start_http_server(METRICS_PORT)

    print("Starting Kafka consumer with metrics")
    print(f"Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic: {TOPIC}")
    print(f"Group ID: {GROUP_ID}")
    print(f"Consumer ID: {CONSUMER_ID}")
    print(f"Metrics: http://localhost:{METRICS_PORT}/metrics")
    print("Press Ctrl+C to stop")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(f"[ERROR] {msg.error()}")
                continue

            event = json.loads(msg.value().decode("utf-8"))
            update_metrics(event, msg)

            key = msg.key().decode("utf-8") if msg.key() else ""
            print(
                f"[CONSUMER] partition={msg.partition()} "
                f"offset={msg.offset()} "
                f"key={key} "
                f"value={event}"
            )

    except KeyboardInterrupt:
        print("\nStopping consumer")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
