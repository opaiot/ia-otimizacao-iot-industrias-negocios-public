# Prática 2 - Séries Temporais com Grafana

Esta aula usa o Grafana para explorar e visualizar séries temporais armazenadas em um Prometheus. A stack inteira roda localmente com Docker: o Prometheus coleta as próprias métricas, que servem de fonte de dados para a prática.

## 1. Objetivo da prática

Ao final da prática, você deve conseguir:

- explicar o que é uma série temporal no modelo do Prometheus (métrica + labels + amostras no tempo);
- distinguir consultas instantâneas de consultas de intervalo e usar `rate()` sobre contadores;
- conectar o Grafana a um Prometheus por meio de um datasource (provisionado por arquivo);
- criar um dashboard de quatro painéis pela API do Grafana e explorar os mesmos dados pelo `Explore`.

## 2. Conceitos da prática

**Série temporal.** No Prometheus, cada combinação de nome de métrica e conjunto de labels identifica uma série: uma sequência de pares (timestamp, valor) coletados a cada *scrape*. `prometheus_http_requests_total{handler="/api/v1/query"}` é uma série; mudar o `handler` muda a série.

**Tipos de métrica.** Um **gauge** (como `prometheus_tsdb_head_series`) sobe e desce e pode ser lido diretamente. Um **counter** (como `prometheus_http_requests_total`) só cresce; o valor absoluto diz pouco, e o interessante é a taxa de variação: `rate(contador[5m])`.

**Fonte de dados da prática.** Não há exportador externo: o Prometheus coleta a si mesmo (job `prometheus`, configurado em [prometheus/prometheus.yml](prometheus/prometheus.yml)). As métricas internas dele — targets no ar, séries ativas, amostras por scrape, requisições HTTP — são séries temporais reais que se movimentam sozinhas, o que basta para estudar visualização.

**Datasource e provisioning.** O Grafana não armazena as séries: a cada consulta ele pergunta ao Prometheus. A conexão é um *datasource*, que nesta aula vem **provisionado por arquivo** ([grafana/provisioning/datasources/prometheus.yml](grafana/provisioning/datasources/prometheus.yml)): configuração declarada em arquivo versionado, em vez de criada à mão na interface. Como Grafana e Prometheus estão na mesma rede Docker, a URL do datasource é `http://prometheus:9090` — o nome do serviço, não `localhost`.

**Dashboard pela API.** Um dashboard do Grafana é um documento JSON (painéis, consultas, posições). A prática importa [dashboard/aula2-series-temporais-dashboard.json](dashboard/aula2-series-temporais-dashboard.json) pela API HTTP, o mesmo mecanismo que ferramentas de automação usam.

## 3. Prática passo a passo

Pré-requisitos: Docker com Docker Compose v2 e Git. As portas `9090` e `3000` precisam estar livres (pare outras práticas do módulo antes).

### 3.1. Subir a stack

```bash
cd M3/Aula_2_series_temporais
docker compose up -d
docker compose ps
```

Os serviços `aula2_prometheus` e `aula2_grafana` devem aparecer como `running`.

### 3.2. Verificar o Prometheus

```bash
curl http://localhost:9090/-/healthy
```

A resposta esperada é `Prometheus Server is Healthy.`. Veja os targets e o estado deles:

```bash
curl -s "http://localhost:9090/api/v1/query?query=up" | jq -c '.data.result[] | {job: .metric.job, valor: .value[1]}'
```

O job `prometheus` deve aparecer com valor `"1"`. No navegador, abra <http://localhost:9090/targets> e depois <http://localhost:9090/graph>, onde você pode executar as consultas da seção 3.6.

> Sem `jq` instalado, remova o `| jq ...` dos comandos: a resposta vem em JSON puro.

### 3.3. Verificar o datasource do Grafana

O datasource `Prometheus - Aula 2` já foi provisionado pelo arquivo em `grafana/provisioning/datasources/`. Confirme pela API:

```bash
curl http://localhost:3000/api/health
curl -s -u admin:admin http://localhost:3000/api/datasources | jq -c '.[] | {name, uid, type, url, isDefault}'
curl -s -u admin:admin http://localhost:3000/api/datasources/uid/prometheus-aula2/health | jq -c .
```

O último comando deve responder `"status":"OK"` com a mensagem `Successfully queried the Prometheus API.`.

### 3.4. Criar o dashboard pela API

Importe o JSON versionado na pasta `dashboard/`:

```bash
curl -fsS -u admin:admin \
  -H "Content-Type: application/json" \
  -X POST \
  --data-binary @dashboard/aula2-series-temporais-dashboard.json \
  http://localhost:3000/api/dashboards/db
```

A resposta traz `"status":"success"`. Confira que o dashboard existe e tem 4 painéis:

```bash
curl -s -u admin:admin http://localhost:3000/api/dashboards/uid/opaiot-aula2-series | jq -c '{titulo: .dashboard.title, paineis: (.dashboard.panels | length)}'
```

### 3.5. Explorar o dashboard no navegador

Abra <http://localhost:3000/d/opaiot-aula2-series> (usuário `admin`, senha `admin`; se o Grafana pedir para trocar a senha, pode clicar em **Skip**).

Observe os quatro painéis e identifique em cada um:

- **Targets UP**: uma série constante em 1 — o que aconteceria se o Prometheus caísse?
- **Séries Ativas no Prometheus**: um gauge; repare que ele cresce um pouco conforme o próprio Prometheus cria séries novas;
- **Amostras Coletadas por Scrape**: quantas séries cada coleta traz;
- **Requisições HTTP do Prometheus**: um `rate()` sobre counter — cada consulta sua pela API ou pelo navegador movimenta este painel.

Mude o intervalo de tempo (canto superior direito) de 15 minutos para 1 hora e observe o efeito na resolução dos gráficos.

### 3.6. Consultas no Explore

Abra **Explore** no menu lateral, selecione `Prometheus - Aula 2` e teste:

```promql
up
prometheus_tsdb_head_series
scrape_samples_scraped
rate(prometheus_http_requests_total[5m])
process_resident_memory_bytes
```

Compare `prometheus_http_requests_total` (counter cru, só cresce) com a versão em `rate()`. As mesmas consultas funcionam pela API, passando pelo datasource do Grafana — o que confirma o caminho Grafana → Prometheus:

```bash
curl -s -G -u admin:admin \
  --data-urlencode 'query=rate(prometheus_http_requests_total[5m])' \
  http://localhost:3000/api/datasources/proxy/uid/prometheus-aula2/api/v1/query \
  | jq -c '.data.result[] | {handler: .metric.handler, taxa: .value[1]}'
```

### 3.7. Encerrar

```bash
docker compose down        # para os containers
docker compose down -v     # remove também os volumes (histórico do Prometheus e ajustes do Grafana)
```

### Problemas comuns

- `curl http://localhost:9090/-/healthy` falha: o container não subiu; veja `docker compose logs prometheus`.
- O datasource não aparece: confira `docker compose logs grafana` e se o arquivo em `grafana/provisioning/datasources/` está com a indentação correta.
- Comandos `curl` com `401`: a senha do `admin` foi trocada; use `-u admin:<nova-senha>`.
- Porta `9090` ou `3000` ocupada: pare a outra prática que estiver usando a porta ou ajuste o mapeamento no [docker-compose.yml](docker-compose.yml).

## 4. Sugestão de exercícios sobre a prática

1. **Instantâneo x intervalo.** No Explore, execute `prometheus_http_requests_total` e depois `prometheus_http_requests_total[1m]` (modo *Instant*). O que cada resultado representa? Por que a segunda forma não pode ser plotada diretamente como gráfico?
2. **Janela do `rate()`.** Duplique o painel "Requisições HTTP do Prometheus" e troque `[5m]` por `[30s]` e por `[15m]`. Compare a suavidade e o atraso das três curvas. Que relação a janela precisa ter com o `scrape_interval` de 5s?
3. **Painel novo.** Adicione ao dashboard um painel com o consumo de memória do Prometheus (`process_resident_memory_bytes`), com a unidade configurada para *bytes (IEC)*. Faça pela interface e depois exporte o JSON do dashboard (menu **Share > Export**) para comparar com o arquivo da pasta `dashboard/`.
4. **Gerar carga.** Rode em um terminal `while true; do curl -s http://localhost:9090/api/v1/query?query=up > /dev/null; sleep 0.2; done` por um minuto e observe o efeito no painel de requisições HTTP. Interrompa com `Ctrl+C` e veja quanto tempo a curva demora para voltar ao normal.
5. **Fonte externa.** Suba também a stack da [Aula 1](../Aula_1_datasets/README.md) e acrescente ao Prometheus desta aula um job que colete `host.docker.internal:8000` (veja `extra_hosts`/`host-gateway` em [../Aula_1_datasets/scripts/README.md](../Aula_1_datasets/scripts/README.md)). Crie um painel com `opaiot_iaq_sensor_value`.

## Arquivos da aula

| Arquivo | Descrição |
| --- | --- |
| [docker-compose.yml](docker-compose.yml) | Sobe Prometheus e Grafana locais em containers. |
| [prometheus/prometheus.yml](prometheus/prometheus.yml) | Prometheus coletando as próprias métricas (job `prometheus`). |
| [grafana/provisioning/datasources/prometheus.yml](grafana/provisioning/datasources/prometheus.yml) | Datasource provisionado apontando para `http://prometheus:9090`. |
| [dashboard/aula2-series-temporais-dashboard.json](dashboard/aula2-series-temporais-dashboard.json) | Dashboard de 4 painéis importado pela API na prática. |
