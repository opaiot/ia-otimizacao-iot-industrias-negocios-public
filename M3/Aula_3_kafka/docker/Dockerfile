# Imagem base usada tanto pelo producer quanto pelo consumer da prática.
# O confluent-kafka publica wheels com librdkafka embutido, então a imagem
# slim do Python é suficiente e não precisamos compilar nada.
FROM python:3.12-slim

WORKDIR /app

# Instala as dependências da prática (as mesmas usadas na VM).
COPY scripts/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia os scripts da prática sem modificá-los. O comando concreto
# (producer.py ou consumer_metrics.py) é definido no docker-compose.yml.
COPY scripts/ ./scripts/

# Saída sem buffer para acompanhar os logs em tempo real via docker logs.
ENV PYTHONUNBUFFERED=1

CMD ["python", "scripts/consumer_metrics.py"]
