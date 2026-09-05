# Aula 2 - Séries Temporais com Grafana

Esta aula usa o Grafana para visualizar séries temporais disponíveis em um Prometheus. Há duas formas de executar a prática:

| Ambiente | Quando usar | Entrada |
| --- | --- | --- |
| VM do curso | Caminho principal da prática. A VM não usa Docker. | [roteiro_para_vm.md](roteiro_para_vm.md) |
| Docker local | Alternativa para máquina local ou outro ambiente com Docker. | [docker-compose.yml](docker-compose.yml) |

## Opção 1 - VM do curso

Na VM, siga o roteiro por linha de comando:

```text
roteiro_para_vm.md
```

Esse guia mostra como:

- acessar a VM por SSH;
- verificar o Prometheus;
- configurar o datasource do Grafana;
- iniciar ou reiniciar o Grafana;
- criar um dashboard básico pela API;
- acessar Grafana e Prometheus pelo Windows usando túnel SSH.

Acesse o guia completo em [roteiro_para_vm.md](roteiro_para_vm.md).

## Opção 2 - Docker local

Use esta opção somente em uma máquina onde Docker esteja disponível.

Entre no diretório da aula:

```bash
cd Modulo_3/Aula_2_series_temporais
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

O datasource provisionado aponta para:

```text
http://andromeda.lasdpc.icmc.usp.br:19201
```

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
