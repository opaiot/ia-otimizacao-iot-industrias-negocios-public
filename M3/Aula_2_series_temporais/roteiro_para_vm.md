# Aula 2 - Séries Temporais com Grafana na VM

Esta prática configura o Grafana da VM para consultar séries temporais armazenadas no Prometheus. O roteiro é feito por linha de comando e assume que o Prometheus e o Grafana já estão em execução na VM do curso: o próprio ambiente os inicia.

Este passo a passo **não usa Docker nem `systemd`**: a VM é um container Ubuntu, e os dois serviços rodam como `root` desde que o container sobe. Antes de começar, leia o [guia do ambiente da VM](../ambiente_vm.md), que explica o acesso por SSH, os limites do container e como recarregar a configuração dos serviços.

## 1. Acessar a VM pelo Windows

No PowerShell, defina o usuário e a porta (recebidos por e-mail do curso, a porta é diferente para cada aluno) e o endereço da VM:

```powershell
$VM_USER = "opaiotXXX"      # usuário do e-mail
$VM_HOST = "andromeda.lasdpc.icmc.usp.br"
$VM_PORT = "PORTA"          # porta do e-mail
```

Acesse e informe a senha recebida por e-mail:

```powershell
ssh -p $VM_PORT "${VM_USER}@${VM_HOST}"
```

O acesso é só por login interativo. `scp`, `sftp`, `ssh ... comando` e túneis de porta (`ssh -L`) são bloqueados nesta VM.

## 2. Entrar no diretório da prática

Na VM:

```bash
cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_2_series_temporais
```

Se o repositório ainda não estiver na VM, clone-o dentro de `~/workspace`, a pasta preservada pelo ambiente:

```bash
cd ~/workspace
git clone https://github.com/opaiot/ia-otimizacao-iot-industrias-negocios-public.git
cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_2_series_temporais
```

## 3. Verificar o Prometheus

Confirme que o comando está disponível:

```bash
prometheus --version
```

Teste se o Prometheus está respondendo:

```bash
curl http://localhost:9090/-/healthy
```

Consulte os targets e o estado deles:

```bash
curl -s "http://localhost:9090/api/v1/query?query=up" | jq -c '.data.result[] | {job: .metric.job, valor: .value[1]}'
```

O Prometheus é iniciado pelo ambiente, como `root`. Se ele não responder, confira `tail /var/log/opaiot/prometheus.log` e, se for o caso, reinicie-o com `sudo` conforme a [seção 4.3 do guia da VM](../ambiente_vm.md#43-reiniciar-o-prometheus-ou-o-grafana-quando-for-realmente-necessário) (ou avise os monitores). Sem `sudo`, `nohup prometheus ...` e `pkill` falham por falta de permissão, e `systemctl` não existe nesta VM.

## 4. Configurar o datasource do Grafana

O Grafana desta VM lê os arquivos de provisioning de `/usr/share/grafana/conf/provisioning/`, e **não** de `/etc/grafana/provisioning/` (um arquivo gravado lá é ignorado, sem aviso). Para conferir:

```bash
curl -s -u admin:admin http://localhost:3000/api/admin/settings | jq -r '.paths.provisioning'
```

A resposta `conf/provisioning` é relativa a `/usr/share/grafana`.

Defina o diretório e, se já existir uma configuração anterior da prática, faça backup dela:

```bash
PROVISIONING_DIR=/usr/share/grafana/conf/provisioning

if [ -f "$PROVISIONING_DIR/datasources/opaiot-aula2-prometheus.yml" ]; then
  sudo cp "$PROVISIONING_DIR/datasources/opaiot-aula2-prometheus.yml" \
    "$PROVISIONING_DIR/datasources/opaiot-aula2-prometheus.yml.bak.$(date +%Y%m%d%H%M%S)"
fi
```

Grave o datasource apontando para o Prometheus da própria VM:

```bash
sudo tee "$PROVISIONING_DIR/datasources/opaiot-aula2-prometheus.yml" >/dev/null <<'EOF'
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
cat "$PROVISIONING_DIR/datasources/opaiot-aula2-prometheus.yml"
```

## 5. Carregar o datasource no Grafana

O Grafana lê os arquivos de provisioning quando inicia, mas **não é preciso reiniciá-lo** (e não é possível com `sudo systemctl restart grafana-server`: a VM não tem `systemd` e o comando responde `System has not been booted with systemd as init system`). Peça que ele releia os datasources pela API de administração:

```bash
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -X POST http://localhost:3000/api/admin/provisioning/datasources/reload
```

A resposta esperada é `{"message":"Datasources config reloaded"}`. Verifique a API do Grafana e o datasource:

```bash
curl http://localhost:3000/api/health
curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" http://localhost:3000/api/datasources | jq -c '.[] | {name, uid, type, url, isDefault}'
curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" http://localhost:3000/api/datasources/uid/prometheus-aula2/health | jq -c .
```

O último comando deve responder com `"status":"OK"` e a mensagem `Successfully queried the Prometheus API.`

## 6. Criar um dashboard básico pela API

Use as credenciais padrão do Grafana (as mesmas variáveis do passo anterior):

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

A resposta traz `"status":"success"`. Confira que o dashboard existe e tem os 4 painéis:

```bash
curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" http://localhost:3000/api/dashboards/uid/opaiot-aula2-series | jq -c '{titulo: .dashboard.title, paineis: (.dashboard.panels | length)}'
```

O dashboard ficará neste endereço, que você abre no navegador do seu computador (troque `XXX` pelos três dígitos do seu usuário `opaiotXXX`):

```text
http://andromeda.lasdpc.icmc.usp.br:13XXX/d/opaiot-aula2-series
```

Dentro da VM, o mesmo dashboard responde em `http://localhost:3000/d/opaiot-aula2-series`.

## 7. Acessar o Grafana e o Prometheus pelo navegador

O Grafana e o Prometheus da sua VM abrem no navegador do seu computador, sem túnel SSH. Troque `XXX` pelos três dígitos do usuário `opaiotXXX` que você recebeu por e-mail (por exemplo, `opaiot001` usa as portas `13001` e `19001`):

```text
Grafana:    http://andromeda.lasdpc.icmc.usp.br:13XXX
Prometheus: http://andromeda.lasdpc.icmc.usp.br:19XXX
Dashboard:  http://andromeda.lasdpc.icmc.usp.br:13XXX/d/opaiot-aula2-series
```

Credenciais padrão do Grafana:

```text
usuário: admin
senha: admin
```

Ao entrar pela primeira vez pelo navegador, o Grafana pode pedir para trocar a senha do `admin`. Se você trocar, use a nova senha em todos os comandos da linha de comando (`-u admin:<nova-senha>`, `GRAFANA_PASSWORD=...`), inclusive no `configure_grafana.sh` da Aula 3; caso contrário eles falham com erro de autenticação.

Dentro do Grafana, o datasource `Prometheus - Aula 2` continua apontando para `http://localhost:9090`, como você configurou no passo 4: o Grafana roda dentro da VM e enxerga o Prometheus por esse endereço. Não troque a URL do datasource pelo endereço `:19XXX`, que serve só para o seu navegador.

### Pela linha de comando

Os mesmos dados podem ser consultados de dentro da sessão SSH, passando pelo datasource que você criou, o que também confirma que o caminho Grafana → Prometheus funciona:

```bash
curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  'http://localhost:3000/api/datasources/proxy/uid/prometheus-aula2/api/v1/query?query=up' \
  | jq -c '.data.result[] | {job: .metric.job, valor: .value[1]}'
```

Para consultas com caracteres especiais, como colchetes, deixe o `curl` codificar a expressão:

```bash
curl -s -G -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  --data-urlencode 'query=rate(prometheus_http_requests_total[5m])' \
  http://localhost:3000/api/datasources/proxy/uid/prometheus-aula2/api/v1/query \
  | jq -c '.data.result[] | {handler: .metric.handler, taxa: .value[1]}'
```

## 8. Consultas PromQL para testar

Estas expressões podem ser usadas em um painel, no `Explore` do Grafana (selecione `Prometheus - Aula 2`) ou pela API, como no passo anterior:

```promql
up
prometheus_tsdb_head_series
scrape_samples_scraped
rate(prometheus_http_requests_total[5m])
process_resident_memory_bytes
```

## 9. Ao terminar

Não há processos para encerrar: o Prometheus e o Grafana continuam rodando como serviços do ambiente e não precisam ser parados. O arquivo de provisioning e o dashboard podem ficar; eles não atrapalham as próximas aulas.

## 10. Problemas comuns

Se `curl http://localhost:9090/-/healthy` falhar, o Prometheus não está respondendo. Confira `tail /var/log/opaiot/prometheus.log` e reinicie-o com `sudo` conforme a [seção 4.3 do guia da VM](../ambiente_vm.md#43-reiniciar-o-prometheus-ou-o-grafana-quando-for-realmente-necessário); se continuar fora do ar, avise os monitores.

Se `curl http://localhost:3000/api/health` falhar, o Grafana não está respondendo. Confira `tail /var/log/opaiot/grafana.log` e reinicie-o com `sudo` conforme a [seção 4.3 do guia da VM](../ambiente_vm.md#43-reiniciar-o-prometheus-ou-o-grafana-quando-for-realmente-necessário); se continuar fora do ar, avise os monitores.

Se o datasource não aparecer na lista depois do `reload`, confirme que o arquivo está em `/usr/share/grafana/conf/provisioning/datasources/` (e não em `/etc/grafana/provisioning/`) e que o YAML está correto, com a mesma indentação do exemplo. Depois rode o `reload` de novo.

Se o endereço `http://andromeda.lasdpc.icmc.usp.br:13XXX` (Grafana) ou `:19XXX` (Prometheus) não abrir no navegador, confira se o `XXX` corresponde ao seu usuário e se o serviço responde por dentro da VM (`curl http://localhost:3000/api/health`). Se responde por dentro e não abre por fora, avise os monitores. O túnel SSH (`ssh -L`) não funciona nesta VM e não é necessário.

Se o login `admin/admin` não funcionar (os comandos `curl` respondem com erro `401`), a senha já foi alterada, por exemplo no primeiro acesso pelo navegador. Defina `GRAFANA_PASSWORD` com a senha atual e repita o comando; se ninguém souber a senha, avise os monitores.
