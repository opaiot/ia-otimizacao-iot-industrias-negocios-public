FROM python:3.12-slim

WORKDIR /app

COPY scripts/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/mqtt_kafka_producer.py ./mqtt_kafka_producer.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "mqtt_kafka_producer.py"]
