# Scripts da Aula 1

Este diretório contém os scripts didáticos da Aula 1 de datasets:

- `1-inspect.py`: inspeciona o CSV, gera perfis das colunas, resumo numérico, eventos normalizados e schema;
- `2-prometheus.py`: simula uma transmissão de leituras do CSV e expõe métricas Prometheus em `http://localhost:8000/metrics`.

O caminho principal da prática é com Docker, descrito no [README da aula](../README.md): lá os dois scripts rodam em containers, sem instalar nada no host. Esta página explica como executá-los **diretamente com Python**, para quem quiser estudar ou modificar os scripts fora do Docker.

Os scripts usam constantes no topo do arquivo, como `CSV_FILE`, `OUTPUT_DIR`, `PORT` e `INTERVAL_SECONDS`. Para alterar caminhos, porta ou intervalo de atualização, edite essas constantes. No `2-prometheus.py`, o intervalo atual é:

```python
INTERVAL_SECONDS = 5.0
```

## 1. Preparar o ambiente

Requisitos: Python 3.10+ com `pip` e `venv`.

```bash
cd M3/Aula_1_datasets/scripts
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Executar a inspeção do dataset

Ainda dentro da pasta `scripts` (os caminhos relativos dos scripts dependem disso):

```bash
python 1-inspect.py
```

O script lê `../data/IoT_Indoor_Air_Quality_Dataset.csv` e gera os resultados em `../outputs/`. O repositório também contém `../outputs_example/`, com uma amostra versionada dos resultados esperados.

## 3. Executar o exportador Prometheus

```bash
python 2-prometheus.py
```

O terminal fica em execução contínua, publicando as métricas em `http://localhost:8000/metrics`. Para conferir, em outro terminal:

```bash
curl http://localhost:8000/metrics
```

Para encerrar, pressione `Ctrl+C`.

## 4. Apontar um Prometheus em Docker para o exportador no host

Se o exportador roda no host e o Prometheus em um container, o target não pode ser `localhost:8000`: dentro do container, `localhost` é o próprio container. Use `host.docker.internal`:

```yaml
scrape_configs:
  - job_name: "opaiot_iaq"
    scrape_interval: 5s
    static_configs:
      - targets: ["host.docker.internal:8000"]
```

No Linux, o container precisa do mapeamento `host-gateway`. Com `docker run`:

```bash
--add-host=host.docker.internal:host-gateway
```

Com `docker compose`, no serviço do Prometheus:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Teste de dentro do container:

```bash
docker exec prometheus wget -qO- http://host.docker.internal:8000/metrics | head
```

> Na stack pronta da aula ([../docker](../docker)), nada disso é necessário: exportador e Prometheus ficam na mesma rede Docker e o target é `exporter:8000`.

## 5. Observações

- Execute os arquivos como `python 1-inspect.py` e `python 2-prometheus.py`. Não use `python -m` com esses nomes: são nomes de arquivo, não de módulo.
- Se aparecer `ModuleNotFoundError`, ative o ambiente virtual e reinstale as dependências.
- Se a porta `8000` estiver em uso, edite a constante `PORT` no topo de `2-prometheus.py` e use a mesma porta no target do Prometheus.
