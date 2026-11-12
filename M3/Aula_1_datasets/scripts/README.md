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

No terminal do Linux, entre na raiz do repositório. Ajuste o caminho conforme o local onde você clonou o projeto (na VM do curso, clone dentro de `~/workspace`, a pasta preservada pelo ambiente):

```bash
cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public
```

Se necessário, instale Python, `pip` e suporte a ambientes virtuais (na VM do curso eles já vêm instalados):

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Crie e ative um ambiente virtual para esta aula:

```bash
cd M3/Aula_1_datasets/scripts
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

Na VM do curso, o Prometheus já está instalado e em execução: o próprio ambiente o iniciou, como `root`, sem Docker e sem `systemd`. Ele consegue acessar o exportador Python por `localhost:8000`.

Edite o arquivo de configuração do Prometheus:

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

Se o arquivo já tiver uma seção `scrape_configs` (na VM, ele traz o job `prometheus`), adicione apenas o bloco do job `opaiot_iaq` dentro dela, com a mesma indentação dos outros jobs.

Valide a configuração:

```bash
promtool check config /etc/prometheus/prometheus.yml
```

Recarregue a configuração **sem reiniciar** o Prometheus, enviando o sinal `SIGHUP` ao processo:

```bash
sudo pkill -HUP -x prometheus
```

Para incluir um job, recarregar basta; não é preciso reiniciar. O processo pertence ao `root`, então `pkill` e o comando de inicialização exigem `sudo`: sem ele, o `pkill` responde `Operation not permitted` e um novo Prometheus falha com `permission denied`. Se precisar reiniciar mesmo assim, use `sudo` e veja a [seção 4.3 do guia da VM](../../ambiente_vm.md#43-reiniciar-o-prometheus-ou-o-grafana-quando-for-realmente-necessário). Atenção: `pkill -f prometheus` também encerraria o `2-prometheus.py` (o nome do arquivo contém "prometheus"); prefira `pkill -x prometheus`.

Com o script `2-prometheus.py` rodando em outro terminal, teste:

```bash
curl http://localhost:8000/metrics | head
curl http://localhost:9090/-/healthy
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job)\t\(.health)"'
```

O job `opaiot_iaq` deve aparecer como `up`. Depois consulte a métrica pela API do Prometheus. A interface web do Prometheus abre no seu navegador em `http://andromeda.lasdpc.icmc.usp.br:19XXX` (`XXX` = os três dígitos do seu usuário `opaiotXXX`; veja o [guia da VM](../../ambiente_vm.md#5-interface-web-do-prometheus-e-do-grafana)):

```bash
curl -s 'http://localhost:9090/api/v1/query?query=opaiot_iaq_sensor_value' | jq '.data.result | length'
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
