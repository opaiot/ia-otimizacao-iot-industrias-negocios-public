# Execução dos scripts no Linux

Este diretório contém os scripts didáticos da Aula 1 de datasets:

- `1-inspect.py`: inspeciona o CSV, gera perfis das colunas, resumo numérico, eventos normalizados e schema.
- `2-prometheus.py`: simula uma transmissão de leituras do CSV e expõe métricas Prometheus em `http://localhost:8000/metrics`.

Os scripts usam constantes no topo do arquivo, como `CSV_FILE`, `OUTPUT_DIR`, `PORT` e `INTERVAL_SECONDS`. No script `2-prometheus.py`, o intervalo atual é de 5 segundos:

```python
INTERVAL_SECONDS = 5.0
```

Para alterar caminhos, porta ou intervalo de atualização, edite essas constantes.

## 1. Preparar o ambiente

No terminal do Linux, entre na raiz do repositório. Ajuste o caminho conforme o local onde você clonou o projeto:

```bash
cd ~/opaIOT_2026
```

Se necessário, instale Python, `pip` e suporte a ambientes virtuais:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Crie e ative um ambiente virtual para esta aula:

```bash
cd Modulo_3/Aula_1_datasets/scripts
python3 -m venv .venv
source .venv/bin/activate
```

Atualize o `pip` e instale as dependências:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Executar a inspeção do dataset

Ainda dentro da pasta `scripts`, execute:

```bash
python 1-inspect.py
```

O script lê o arquivo:

```text
../data/IoT_Indoor_Air_Quality_Dataset.csv
```

E gera os resultados em:

```text
../outputs/
```

O repositório também contém `../outputs_example/`, com uma amostra versionada dos resultados esperados.

Arquivos esperados:

- `columns_profile.csv`
- `semantic_classification.csv`
- `numeric_summary.csv`
- `normalized_events.jsonl`
- `iot_event_schema.json`
- `inspection_summary.json`

## 3. Executar o exportador Prometheus

Execute:

```bash
python 2-prometheus.py
```

O terminal ficará em execução contínua, publicando as métricas em:

```text
http://localhost:8000/metrics
```

Para conferir pelo terminal:

```bash
curl http://localhost:8000/metrics
```

Para encerrar o script, pressione `Ctrl+C`.

### Quando o Prometheus está instalado na VM

Se o Prometheus estiver instalado diretamente no Ubuntu, sem Docker, ele consegue acessar o exportador Python por `localhost:8000`.

Edite o arquivo de configuração do Prometheus. Em instalações comuns no Ubuntu, ele fica em:

```bash
sudo nano /etc/prometheus/prometheus.yml
```

Inclua um job para esta aula:

```yaml
scrape_configs:
  - job_name: "opaiot_iaq"
    scrape_interval: 5s
    static_configs:
      - targets: ["localhost:8000"]
```

Se o arquivo já tiver uma seção `scrape_configs`, adicione apenas o bloco do job `opaiot_iaq` dentro dela.

Valide a configuração:

```bash
promtool check config /etc/prometheus/prometheus.yml
```

Reinicie o Prometheus. Nesta VM, o Prometheus é iniciado manualmente, então encerre o processo atual e suba novamente com o arquivo de configuração:

```bash
pkill -f prometheus
prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/var/lib/prometheus --web.listen-address=0.0.0.0:9090
```

O comando acima mantém o Prometheus rodando no terminal. Deixe esse terminal aberto enquanto usa a interface gráfica.

Se quiser confirmar que o Prometheus voltou:

```bash
curl http://localhost:9090/-/healthy
```

Com o script `2-prometheus.py` rodando em outro terminal, teste:

```bash
curl http://localhost:8000/metrics | head
curl http://localhost:9090/-/healthy
```

Na interface do Prometheus, abra:

```text
http://localhost:9090/targets
```

O job `opaiot_iaq` deve aparecer como `UP`. Depois consulte:

```promql
opaiot_iaq_sensor_value
```

### Quando o Prometheus está em Docker

Se o Prometheus estiver em um container Docker, o target no `prometheus.yml` não deve ser `localhost:8000`, exceto se o container estiver usando rede host.

No modo bridge padrão do Docker, use:

```yaml
scrape_configs:
  - job_name: "opaiot_iaq"
    scrape_interval: 5s
    static_configs:
      - targets: ["host.docker.internal:8000"]
```

No Linux, o container precisa ser criado com:

```bash
--add-host=host.docker.internal:host-gateway
```

Em `docker compose`, use:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Teste de dentro do container:

```bash
docker exec prometheus wget -qO- http://host.docker.internal:8000/metrics | head
```

## 4. Observações importantes

Execute os arquivos diretamente com `python nome_do_script.py`. Não use `python -m`, pois os nomes `1-inspect.py` e `2-prometheus.py` são nomes de arquivo, não nomes de módulo Python.

Se a porta `8000` já estiver em uso, edite a constante no topo de `2-prometheus.py`:

```python
PORT = 8000
```

Se o CSV mudar de nome ou local, edite a constante `CSV_FILE` no topo dos scripts.
