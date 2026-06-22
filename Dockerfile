FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-pratica1.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-pratica1.txt

# Inclui os pesos na imagem para o container não depender de download ao iniciar.
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

RUN groupadd --system app \
    && useradd --system --gid app --create-home app \
    && chown --recursive app:app /app

COPY --chown=app:app servico_patio.py .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "servico_patio:app", "--host", "0.0.0.0", "--port", "8000"]
