# Imagem usada pelo exportador (2-prometheus.py) e pela inspeção (1-inspect.py).
# Os scripts da prática são usados sem modificação; por isso preservamos a
# mesma estrutura de pastas da aula (scripts/ ao lado de data/), já que
# 2-prometheus.py lê o CSV pelo caminho relativo "../data/...".
FROM python:3.12-slim

WORKDIR /app

# Instala as dependências da prática (as mesmas usadas na VM).
COPY scripts/requirements.txt ./scripts/requirements.txt
RUN pip install --no-cache-dir -r scripts/requirements.txt

# Copia scripts e dataset mantendo a estrutura esperada pelos scripts.
COPY scripts/ ./scripts/
COPY data/ ./data/

# Saída sem buffer para acompanhar os logs em tempo real via docker logs.
ENV PYTHONUNBUFFERED=1

# O exportador precisa rodar de dentro de scripts/ por causa do caminho
# relativo "../data/..." usado em CSV_FILE. O comando concreto é definido
# no docker-compose.yml.
WORKDIR /app/scripts

CMD ["python", "2-prometheus.py"]
