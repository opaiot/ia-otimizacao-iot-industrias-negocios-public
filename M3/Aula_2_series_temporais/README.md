# Prática 2 - Séries Temporais com Grafana

Esta aula usa o Grafana para visualizar séries temporais disponíveis em um Prometheus. Há duas formas de executar a prática:

| Ambiente | Quando usar | Entrada |
| --- | --- | --- |
| VM do curso | Caminho principal da prática. A VM é um container Ubuntu (sem Docker nem `systemd`) com Prometheus e Grafana já instalados e em execução. | [roteiro_para_vm.md](roteiro_para_vm.md) |
| Docker local | Alternativa para máquina local ou outro ambiente com Docker. | [docker-compose.yml](docker-compose.yml) |

## Opção 1 - VM do curso

Na VM, siga o roteiro por linha de comando:

```text
roteiro_para_vm.md
```

Esse guia mostra como:

- acessar a VM por SSH (usuário, porta e senha recebidos por e-mail; só login interativo);
- verificar o Prometheus, que já está em execução;
- configurar o datasource do Grafana pelo diretório de provisioning que o Grafana da VM realmente lê;
- carregar o datasource sem reiniciar o Grafana;
- criar um dashboard básico pela API;
- acessar o Grafana e o Prometheus da sua VM pelo navegador (portas `13XXX` e `19XXX`, onde `XXX` são os três dígitos do seu usuário) e consultar os dados pela linha de comando.

Acesse o guia completo em [roteiro_para_vm.md](roteiro_para_vm.md). Para entender o ambiente (container sem `systemd`, limites de memória e de processos), veja o [guia da VM](../ambiente_vm.md).

## Opção 2 - Docker local

Use esta opção somente em uma máquina onde Docker esteja disponível.

Entre no diretório da aula:

```bash
cd M3/Aula_2_series_temporais
```

Suba o Grafana:

```bash
docker compose up -d
```

Verifique:

```bash
docker compose ps
```

Acesse:

```text
http://localhost:3000
```

Credenciais padrão:

```text
usuário: admin
senha: admin
```

O datasource provisionado aponta para o Prometheus de uma **VM dos monitores do curso** (porta `19201`), e não para o Prometheus da sua VM:

```text
http://andromeda.lasdpc.icmc.usp.br:19201
```

Esse endereço depende da VM dos monitores estar no ar. Para testar, rode `curl http://andromeda.lasdpc.icmc.usp.br:19201/-/healthy`: a resposta esperada é `Prometheus Server is Healthy.` Se não responder, o Grafana abre normalmente, mas o datasource mostra erro; avise os monitores.

Para ver, nesse Grafana local, os dados da **sua própria VM** (por exemplo, os jobs que você configurou nas Aulas 1 e 3), troque a `url` do datasource por `http://andromeda.lasdpc.icmc.usp.br:19XXX`, onde `XXX` são os três dígitos do seu usuário `opaiotXXX`, e reinicie o Grafana local com `docker compose restart grafana`.

Essa configuração está em:

```text
grafana/provisioning/datasources/prometheus.yml
```

Para testar no Grafana, abra `Explore` e execute:

```promql
up
```

## Parar o Docker local

```bash
docker compose down
```

Para remover também o volume do Grafana:

```bash
docker compose down -v
```

## Arquivos da aula

| Arquivo | Descrição |
| --- | --- |
| [roteiro_para_vm.md](roteiro_para_vm.md) | Passo a passo completo para execução na VM, sem Docker. |
| [docker-compose.yml](docker-compose.yml) | Sobe Grafana local em container. |
| [grafana/provisioning/datasources/prometheus.yml](grafana/provisioning/datasources/prometheus.yml) | Datasource Prometheus provisionado para o Grafana em Docker. |
