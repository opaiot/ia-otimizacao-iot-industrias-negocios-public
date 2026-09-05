import json
import os
import random
import time
from datetime import datetime, timezone

from confluent_kafka import Producer


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "iot.air_quality")
SEND_INTERVAL_SECONDS = float(os.getenv("SEND_INTERVAL_SECONDS", "1"))

SENSORS = [
    {"sensor_id": "sensor-01", "room": "lab-01"},
    {"sensor_id": "sensor-02", "room": "lab-02"},
    {"sensor_id": "sensor-03", "room": "lab-03"},
    {"sensor_id": "sensor-04", "room": "office-01"},
    {"sensor_id": "sensor-05", "room": "office-02"},
]


def delivery_report(err, msg):
    if err is not None:
        print(f"[ERROR] Delivery failed: {err}")
        return

    key = msg.key().decode("utf-8") if msg.key() else ""
    print(
        f"[OK] topic={msg.topic()} "
        f"partition={msg.partition()} "
        f"offset={msg.offset()} "
        f"key={key}"
    )


def generate_event():
    sensor = random.choice(SENSORS)

    return {
        "sensor_id": sensor["sensor_id"],
        "room": sensor["room"],
        "temperature": round(random.uniform(20.0, 35.0), 2),
        "humidity": round(random.uniform(40.0, 85.0), 2),
        "co2": random.randint(400, 1800),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

    print("Starting IoT sensor producer")
    print(f"Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic: {TOPIC}")
    print(f"Send interval: {SEND_INTERVAL_SECONDS}s")
    print("Press Ctrl+C to stop")

    try:
        while True:
            event = generate_event()
            key = event["sensor_id"]
            value = json.dumps(event)

            producer.produce(
                topic=TOPIC,
                key=key,
                value=value,
                callback=delivery_report,
            )
            producer.poll(0)

            print(f"[PRODUCER] sent={value}")
            time.sleep(SEND_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStopping producer")

    finally:
        producer.flush(10)


if __name__ == "__main__":
    main()
