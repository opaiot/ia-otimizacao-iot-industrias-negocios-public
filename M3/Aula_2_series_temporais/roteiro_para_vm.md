# Aula 2 - Séries Temporais com Grafana na VM

Esta prática configura o Grafana da VM para consultar séries temporais armazenadas no Prometheus. O roteiro é feito por linha de comando e assume que os serviços já estão disponíveis na VM do curso.

Este passo a passo **não usa Docker**.

## 1. Acessar a VM pelo Windows

No PowerShell, defina o usuário e o endereço da VM:

```powershell
$VM_USER = "ubuntu"
$VM_HOST = "192.168.0.10"
```

Acesse:

```powershell
ssh "${VM_USER}@${VM_HOST}"
```

Se a VM usa chave SSH:

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" "${VM_USER}@${VM_HOST}"
```

## 2. Entrar no diretório da prática

Na VM:

```bash
cd ~/opaIOT_2026/Modulo_3/Aula_2_series_temporais
```

Se o repositório ainda não estiver na VM:

```bash
cd ~
git clone https://github.com/Smart-LaSDPC/opaIOT_2026.git
cd ~/opaIOT_2026/Modulo_3/Aula_2_series_temporais
```

## 3. Verificar o Prometheus

Confirme que o comando está disponível:

```bash
prometheus --version
```

Teste se o Prometheus já está respondendo:

```bash
curl http://localhost:9090/-/healthy
```

Consulte os targets:

```bash
curl "http://localhost:9090/api/v1/query?query=up"
```

No navegador, a página de targets será:

```text
http://localhost:9090/targets
```

Se o Prometheus estiver instalado, mas não estiver rodando, inicie manualmente:

```bash
pkill -f '(^|/)prometheus([[:space:]]|$)' || true
nohup prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --web.listen-address=0.0.0.0:9090 \
  > prometheus.log 2>&1 &
```

Teste novamente:

```bash
curl http://localhost:9090/-/healthy
```

## 4. Configurar o datasource do Grafana

Crie o arquivo de provisioning:

```bash
sudo mkdir -p /etc/grafana/provisioning/datasources
```

Se já existir uma configuração anterior da prática, faça backup:

```bash
if [ -f /etc/grafana/provisioning/datasources/opaiot-aula2-prometheus.yml ]; then
  sudo cp /etc/grafana/provisioning/datasources/opaiot-aula2-prometheus.yml \
    "/etc/grafana/provisioning/datasources/opaiot-aula2-prometheus.yml.bak.$(date +%Y%m%d%H%M%S)"
fi
```

Grave o datasource apontando para o Prometheus da própria VM:

```bash
sudo tee /etc/grafana/provisioning/datasources/opaiot-aula2-prometheus.yml >/dev/null <<'EOF'
apiVersion: 1

datasources:
  - name: Prometheus - Aula 2
    uid: prometheus-aula2
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: true
    jsonData:
      httpMethod: GET
EOF
```

Confira:

```bash
sudo cat /etc/grafana/provisioning/datasources/opaiot-aula2-prometheus.yml
```

## 5. Iniciar ou reiniciar o Grafana

Tente primeiro com `systemd`:

```bash
sudo systemctl restart grafana-server
sudo systemctl status grafana-server --no-pager
```

Se a VM não usa `systemd` para o Grafana, inicie manualmente:

```bash
pkill -f grafana-server || true
nohup grafana-server \
  --homepath=/usr/share/grafana \
  --config=/etc/grafana/grafana.ini \
  > grafana.log 2>&1 &
```

Verifique a API do Grafana:

```bash
curl http://localhost:3000/api/health
```

## 6. Criar um dashboard básico pela API

Use as credenciais padrão do Grafana:

```bash
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

Crie o arquivo do dashboard:

```bash
cat > /tmp/aula2-series-temporais-dashboard.json <<'EOF'
{
  "dashboard": {
    "uid": "opaiot-aula2-series",
    "title": "Aula 2 - Séries Temporais",
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "5s",
    "time": {
      "from": "now-15m",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "type": "timeseries",
        "title": "Targets UP",
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus-aula2"
        },
        "targets": [
          {
            "expr": "up",
            "legendFormat": "{{job}} {{instance}}",
            "refId": "A"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "type": "timeseries",
        "title": "Séries Ativas no Prometheus",
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus-aula2"
        },
        "targets": [
          {
            "expr": "prometheus_tsdb_head_series",
            "legendFormat": "head_series",
            "refId": "A"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "type": "timeseries",
        "title": "Amostras Coletadas por Scrape",
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus-aula2"
        },
        "targets": [
          {
            "expr": "scrape_samples_scraped",
            "legendFormat": "{{job}} {{instance}}",
            "refId": "A"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 8
        }
      },
      {
        "id": 4,
        "type": "timeseries",
        "title": "Requisições HTTP do Prometheus",
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus-aula2"
        },
        "targets": [
          {
            "expr": "rate(prometheus_http_requests_total[5m])",
            "legendFormat": "{{handler}}",
            "refId": "A"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 8
        }
      }
    ]
  },
  "overwrite": true
}
EOF
```

Importe o dashboard:

```bash
curl -fsS \
  -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -X POST \
  --data-binary @/tmp/aula2-series-temporais-dashboard.json \
  http://localhost:3000/api/dashboards/db
```

O dashboard ficará em:

```text
http://localhost:3000/d/opaiot-aula2-series
```

## 7. Acessar Grafana e Prometheus pelo Windows

Abra outro PowerShell e mantenha o túnel SSH ativo:

```powershell
ssh -L 3000:localhost:3000 -L 9090:localhost:9090 "${VM_USER}@${VM_HOST}"
```

Depois acesse:

```text
Grafana:    http://localhost:3000
Prometheus: http://localhost:9090
Dashboard:  http://localhost:3000/d/opaiot-aula2-series
```

Credenciais padrão do Grafana:

```text
usuário: admin
senha: admin
```

## 8. Consultas PromQL para testar

No Grafana, abra `Explore`, selecione `Prometheus - Aula 2` e teste:

```promql
up
prometheus_tsdb_head_series
scrape_samples_scraped
rate(prometheus_http_requests_total[5m])
process_resident_memory_bytes
```

## 9. Encerrar processos iniciados manualmente

Se você iniciou Prometheus ou Grafana manualmente com `nohup`, encerre com:

```bash
pkill -f '(^|/)prometheus([[:space:]]|$)' || true
pkill -f grafana-server || true
```

Se o Grafana já estava rodando como serviço da VM, não é necessário pará-lo ao final da prática.

## 10. Problemas comuns

Se `curl http://localhost:9090/-/healthy` falhar, o Prometheus não está rodando ou está usando outra porta.

Se `curl http://localhost:3000/api/health` falhar, o Grafana não está rodando ou está usando outra porta.

Se o Grafana abrir, mas o datasource não aparecer, reinicie o Grafana depois de criar o arquivo em `/etc/grafana/provisioning/datasources/`.

Se o login `admin/admin` não funcionar, a senha já foi alterada na VM. Use a senha definida anteriormente ou redefina conforme a política do ambiente.
