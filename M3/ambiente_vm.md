# Ambiente da VM do curso (LASDPC)

Este guia reúne o que é comum às práticas do Módulo 3 executadas na VM do curso (Aulas 1, 2 e 3). Os roteiros de cada aula apontam para cá quando precisam de um detalhe do ambiente.

> As informações abaixo vêm de testes das práticas na própria VM do curso. Se algo se comportar de outra forma na sua VM, avise os monitores.

## 1. O que é a "VM"

A VM do curso **não é uma máquina virtual completa: é um container Docker** com Ubuntu 24.04, um por aluno (hostname `curso-opaiot-<usuário>`). Isso tem consequências práticas:

| O que você pode esperar | Na VM do curso |
| --- | --- |
| `systemctl` e `journalctl` | **Não funcionam.** O processo 1 do container é um `sleep infinity`, não o `systemd`. A mensagem típica é `System has not been booted with systemd as init system (PID 1). Can't operate.` O comando `service ... status` também não é confiável: informa `grafana is not running` mesmo com o Grafana no ar. |
| Docker dentro da VM | **Não há.** `docker` e `docker compose` não estão instalados. |
| `sudo` | Disponível, sem senha. |
| Variável `$USER` | **Vazia.** Use `$(id -un)` e `$(id -gn)` quando precisar do nome do usuário e do grupo. |
| Prometheus e Grafana | **Já instalados e em execução**, iniciados pelo próprio ambiente (veja a [seção 4](#4-prometheus-e-grafana-já-em-execução)). |
| Java | **Não vem instalado.** Só é necessário para o Kafka (Aula 3), cujo roteiro instala o JDK. |

Ferramentas que já vêm na VM: `git`, `python3`, `pip`, `venv`, `node`/`npm`, `curl`, `wget`, `jq`, `nano`, `vim`, `mosquitto_pub`/`mosquitto_sub`, `prometheus` e `promtool`, `grafana-server`.

## 2. Acesso por SSH

No PowerShell do Windows (ou no terminal do Linux/macOS), use o **usuário, a porta e a senha** que você recebeu por e-mail do curso. A porta SSH **não é a mesma para todos os alunos**:

```powershell
$VM_USER = "opaiotNNN"                       # troque pelo usuário do e-mail
$VM_HOST = "andromeda.lasdpc.icmc.usp.br"
$VM_PORT = "PORTA"                           # troque pela porta do e-mail

ssh -p $VM_PORT "${VM_USER}@${VM_HOST}"
```

Ao entrar, o ambiente mostra um resumo (container, diretórios úteis, endereços do Prometheus e do Grafana) e deixa você em `~/workspace`.

Você pode abrir **várias sessões ao mesmo tempo** (uma janela do PowerShell para cada uma). Isso é necessário quando uma prática pede um processo em primeiro plano e outro terminal para testar.

### O que não funciona nesta VM

O acesso é restrito a **login interativo**. Estes recursos do SSH estão bloqueados no servidor:

| Recurso | Como falha |
| --- | --- |
| Executar um comando direto, como `ssh ... "ls"` | `Comandos remotos diretos não são permitidos neste ambiente.` |
| `scp` e `sftp` | `Received message too long ...` (o banner de entrada atrapalha o protocolo) |
| Túnel de portas, como `ssh -L 3000:localhost:3000 ...` | `channel N: open failed: administratively prohibited` |

Por isso os roteiros não usam `scp` nem túnel SSH. Para levar arquivos pequenos para o seu computador, veja a [seção 7](#7-copiar-arquivos-pequenos-para-o-seu-computador).

## 3. Onde guardar os arquivos

Só o que estiver em **`~/workspace`** é preservado (é o que o banner de entrada informa). Clone o repositório e crie seus ambientes virtuais lá:

```bash
cd ~/workspace
git clone https://github.com/opaiot/ia-otimizacao-iot-industrias-negocios-public.git
```

Outras observações:

- O arquivo `~/.bashrc` é **recriado sempre que o ambiente reinicia**. Linhas que você acrescentar nele (por exemplo, um `export PATH=...`) podem sumir; se um comando "deixar de ser encontrado", repita o `export`.
- Programas instalados fora de `~/workspace` (como o Kafka em `/opt/kafka`) não têm garantia de persistência se o ambiente for recriado.

## 4. Prometheus e Grafana já em execução

O ambiente inicia os dois serviços sozinho, como `root`. **Não tente reiniciá-los** com `systemctl`, nem com `pkill` + comando de inicialização: sem `sudo` o `pkill` não tem permissão sobre um processo de `root`, e subir um segundo Prometheus ou Grafana como usuário comum falha por falta de permissão e por conflito de porta.

| Serviço | Porta dentro da VM | Endereço no seu navegador | Credenciais | Log |
| --- | --- | --- | --- | --- |
| Prometheus 2.45 | `9090` | `http://andromeda.lasdpc.icmc.usp.br:19XXX` | sem login | `/var/log/opaiot/prometheus.log` |
| Grafana 13 | `3000` | `http://andromeda.lasdpc.icmc.usp.br:13XXX` | `admin` / `admin` | `/var/log/opaiot/grafana.log` |

`XXX` são os três dígitos do seu usuário `opaiotXXX` (veja a [seção 5](#5-interface-web-do-prometheus-e-do-grafana)).

Confira se estão no ar:

```bash
curl http://localhost:9090/-/ready
curl http://localhost:3000/api/health
```

Se algum não responder, avise os monitores em vez de tentar reiniciá-lo.

### 4.1 Recarregar a configuração do Prometheus

O arquivo de configuração é `/etc/prometheus/prometheus.yml`. Depois de editá-lo (com `sudo nano`, ou com o script da Aula 3), valide e **recarregue sem reiniciar**, enviando o sinal `SIGHUP` ao processo:

```bash
promtool check config /etc/prometheus/prometheus.yml
sudo pkill -HUP -x prometheus
```

O `-x` casa só o processo chamado exatamente `prometheus`. (`pkill -f prometheus` casaria também seus próprios scripts, como o `2-prometheus.py` da Aula 1.)

A API de recarga por HTTP (`/-/reload`) não está habilitada nesta VM, por isso o `SIGHUP`. Aguarde alguns segundos e confira:

```bash
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job)\t\(.scrapeUrl)\t\(.health)"'
```

Cada job deve aparecer com `up`. Se a configuração tiver erro, o Prometheus mantém a anterior e registra o motivo no log (`tail /var/log/opaiot/prometheus.log`).

### 4.2 Recarregar o provisioning do Grafana

O Grafana desta VM lê os arquivos de provisioning de **`/usr/share/grafana/conf/provisioning/`** e **não** de `/etc/grafana/provisioning/` (um arquivo colocado lá é ignorado, sem nenhum erro). Para conferir o diretório em uso:

```bash
curl -s -u admin:admin http://localhost:3000/api/admin/settings | jq -r '.paths.provisioning'
```

A resposta `conf/provisioning` é relativa ao diretório do Grafana (`/usr/share/grafana`). Depois de criar ou alterar um arquivo em `datasources/`, recarregue sem reiniciar o Grafana:

```bash
curl -s -u admin:admin -X POST http://localhost:3000/api/admin/provisioning/datasources/reload
```

A resposta esperada é `{"message":"Datasources config reloaded"}`.

Datasources, pastas e dashboards também podem ser criados pela API HTTP, como faz o `configure_grafana.sh` da Aula 3; isso dispensa qualquer arquivo ou recarga.

## 5. Interface web do Prometheus e do Grafana

O Prometheus e o Grafana da sua VM abrem no **navegador do seu computador**, sem túnel SSH, nestes endereços:

| Serviço | Endereço |
| --- | --- |
| Prometheus | `http://andromeda.lasdpc.icmc.usp.br:19XXX` |
| Grafana | `http://andromeda.lasdpc.icmc.usp.br:13XXX` |

Troque `XXX` pelos três dígitos do usuário `opaiotXXX` que você recebeu por e-mail. Por exemplo, para o usuário `opaiot001` os endereços são `...:19001` (Prometheus) e `...:13001` (Grafana); para `opaiot120`, `...:19120` e `...:13120`. No Grafana, entre com `admin` / `admin`. Páginas úteis do Prometheus: `/targets` (estado dos jobs) e `/graph` (consultas PromQL).

Estes são os endereços externos disponibilizados pelo curso. O exportador da Aula 1 (porta `8000`) e os consumers da Aula 3 (portas `8000` a `8003`) não têm endereço externo: consulte-os **de dentro da VM**, com `curl`, ou pelo próprio Prometheus.

Dentro da VM, o Prometheus e o Grafana continuam em `http://localhost:9090` e `http://localhost:3000`. Use esses endereços nos comandos `curl` e, principalmente, na configuração do datasource do Grafana: o Grafana roda dentro da VM e enxerga o Prometheus como `http://localhost:9090`, e **não** pelo endereço `:19XXX`.

O túnel SSH (`ssh -L`) continua bloqueado, mas não é necessário. Os mesmos dados também podem ser consultados pela linha de comando, dentro da sessão SSH:

```bash
# targets do Prometheus e seu estado
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job)\t\(.health)"'

# uma consulta PromQL
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq -c '.data.result[] | {job: .metric.job, valor: .value[1]}'

# a mesma consulta, passando pelo datasource do Grafana
curl -s -u admin:admin 'http://localhost:3000/api/datasources/proxy/uid/<uid-do-datasource>/api/v1/query?query=up'
```

Se o endereço no navegador não abrir, confira se o `XXX` está certo e se o serviço responde por dentro da VM (`curl http://localhost:9090/-/ready` e `curl http://localhost:3000/api/health`). Se responde por dentro e não abre por fora, avise os monitores.

Quem preferir ver os dashboards em um Grafana na própria máquina pode usar as alternativas com Docker que cada aula descreve (Aula 1: [docker/](Aula_1_datasets/docker/README.md); Aula 2: [Docker local](Aula_2_series_temporais/README.md#opção-2---docker-local); Aula 3: [docker/](Aula_3_kafka/docker/README.md)). Elas não são necessárias para seguir os roteiros da VM.

## 6. Limites de memória e de processos

O container tem limites de recursos. Os valores abaixo valem para o ambiente testado; você pode conferir os seus:

```bash
cat /sys/fs/cgroup/memory.max     # memória máxima, em bytes (1073741824 = 1 GiB)
cat /sys/fs/cgroup/pids.max       # máximo de processos + threads
cat /sys/fs/cgroup/pids.current   # quantos estão em uso agora
```

- **Memória: 1 GiB**, dividida entre Prometheus (~65 MB), Grafana (~265 MB) e tudo o que você iniciar. O Kafka, por padrão, reserva 1 GB de heap sozinho; por isso o [roteiro do Kafka](Aula_3_kafka/instalando_kafka_vm.md) limita o heap.
- **Processos e threads: 256 no total.** Ordem de grandeza medida: broker Kafka ≈ 108 threads; Prometheus + Grafana ≈ 36; um `producer.py` ≈ 4 e um `consumer_metrics.py` ≈ 6; cada comando `kafka-*.sh` abre uma JVM que usa ≈ 24 por alguns segundos.
- Processos encerrados cujo "pai" já saiu (o caso típico é o `sudo`) ficam listados como `<defunct>` (zumbis) e **continuam ocupando uma vaga** até o ambiente reiniciar. Evite `sudo` desnecessário e não o use em laços. Para contar: `ps -eo stat | grep -c '^Z'`.

Quando o limite de processos é atingido, aparecem mensagens como `pthread_create failed (EAGAIN)`, `Failed to start the native thread` ou `Resource temporarily unavailable`. Encerre o que não estiver usando (consumers extras, terminais com processos pendurados) e tente de novo. Se a memória acabar, o sistema encerra processos sem aviso.

## 7. Copiar arquivos pequenos para o seu computador

Como `scp` e `sftp` não funcionam, há duas saídas:

1. **Ler na própria VM**, com `cat`, `head` ou `less` (texto e CSV) e `jq` (JSON).
2. **Copiar o conteúdo pelo terminal**, para arquivos pequenos. Na VM, compacte e codifique em texto (os `outputs/` da Aula 1, por exemplo, ocupam cerca de 11 KB assim):

   ```bash
   cd ~/workspace/ia-otimizacao-iot-industrias-negocios-public/M3/Aula_1_datasets
   tar -czf - outputs | base64 -w0; echo
   ```

   Selecione e copie a linha impressa. No **PowerShell do Windows**, recrie o arquivo:

   ```powershell
   $b64 = (Get-Clipboard) -join ""
   [IO.File]::WriteAllBytes("$env:USERPROFILE\Downloads\outputs.tar.gz", [Convert]::FromBase64String($b64.Trim()))
   tar -xzf "$env:USERPROFILE\Downloads\outputs.tar.gz" -C "$env:USERPROFILE\Downloads"
   ```

   No Linux/macOS, cole o texto em um arquivo `outputs.b64` e use `base64 -d outputs.b64 | tar -xzf -`.

## 8. Mensagens de erro frequentes

| Mensagem | Causa | O que fazer |
| --- | --- | --- |
| `System has not been booted with systemd ...` | A VM não usa `systemd`. | Não use `systemctl`/`journalctl`; veja as seções 4 e [Kafka em segundo plano](Aula_3_kafka/instalando_kafka_vm.md#7-executar-o-kafka-sem-systemd). |
| `pkill: killing pid 30 failed: Operation not permitted` | O Prometheus pertence ao `root`. | Não reinicie; recarregue com `sudo pkill -HUP -x prometheus` (seção 4.1). |
| `Error opening query log file ... permission denied` | Tentativa de subir um segundo Prometheus como usuário comum. | Não suba outro; o serviço já está em execução. |
| Datasource criado em `/etc/grafana/provisioning` não aparece | O Grafana desta VM lê `/usr/share/grafana/conf/provisioning`. | Seção 4.2. |
| `Comandos remotos diretos não são permitidos` / `administratively prohibited` / `Received message too long` | `ssh comando`, túnel e `scp`/`sftp` estão bloqueados. | Use sessão interativa (seção 2) e a seção 7. |
| `pthread_create failed (EAGAIN)` | Limite de processos/threads atingido. | Seção 6. |
