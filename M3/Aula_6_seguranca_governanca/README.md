# Prática 6 - Segurança e Governança com Mosquitto MQTT e Grafana

Esta aula parte de um broker MQTT aberto, demonstra o risco, e então ativa autenticação por usuário e autorização por tópico (ACL), organizando os tópicos por papel: dispositivo que publica, monitor que lê e operador que comanda. Tudo roda localmente com Docker.

## 1. Objetivo da prática

Ao final da prática, você deve conseguir:

- demonstrar o que um broker MQTT **sem autenticação** permite a qualquer cliente;
- ativar autenticação por usuário e senha no Mosquitto (`password_file`);
- escrever e aplicar uma **ACL por tópico**, separando papéis de leitura, escrita e comando;
- verificar, pelos logs do broker, publicações e assinaturas negadas;
- discutir governança: organização hierárquica de tópicos e o lugar de ferramentas visuais como o Grafana.

## 2. Conceitos da prática

**Autenticação x autorização.** Autenticação responde "quem é você" (usuário e senha no `password_file`); autorização responde "o que você pode fazer" (a ACL diz quais tópicos cada usuário lê ou escreve). Uma sem a outra é governança pela metade: usuário autenticado sem ACL continua podendo publicar em qualquer tópico.

**Organização de tópicos.** A ACL só funciona bem sobre uma hierarquia de tópicos pensada. A prática usa:

```text
opaiot/sensors/<sensor>/telemetry   <- telemetria publicada pelos dispositivos
opaiot/devices/<device>/status      <- estado reportado pelos dispositivos
opaiot/devices/<device>/cmd         <- comandos enviados aos dispositivos
```

**Papéis da prática** (definidos em [mosquitto/config/acl](mosquitto/config/acl)):

| Usuário | Pode | Não pode |
| --- | --- | --- |
| `sensor01` | escrever em `opaiot/sensors/sensor01/telemetry` | escrever como outro sensor, ler tópicos |
| `monitor01` | ler `opaiot/sensors/+/telemetry` e `opaiot/devices/+/status` | publicar qualquer coisa |
| `operador01` | ler telemetria e escrever em `opaiot/devices/+/cmd` | escrever telemetria |

**Falha silenciosa.** O Mosquitto **não devolve erro** ao cliente em uma publicação negada por ACL: a mensagem é descartada e o comando do cliente termina como se tivesse dado certo. O fato só aparece no log do broker, e **somente se o log estiver configurado para isso** (`log_type all`, incluído na configuração segura desta aula). Negação invisível para o cliente e ausente do log é um problema de auditoria, não de conveniência.

**Grafana como camada visual.** O Grafana não consome MQTT diretamente como fonte nativa. Em um pipeline real, entre o broker e o Grafana existe uma camada intermediária (por exemplo, MQTT → ponte Python → Prometheus → Grafana, como nas Aulas 4 e 5, ou MQTT → Telegraf → InfluxDB → Grafana). Aqui ele entra como camada visual e de governança: quem vê o quê também é uma decisão de acesso.

**Arquivos da aula:**

| Arquivo | Descrição |
| --- | --- |
| [docker-compose.yml](docker-compose.yml) | Mosquitto (portas `20202`/`20203` no host) e Grafana (porta `9001`) |
| [mosquitto/config/mosquitto.conf](mosquitto/config/mosquitto.conf) | **Arquivo ativo**: é o que o broker lê. Começa como cópia da configuração aberta |
| [mosquitto/config/mosquitto-open.conf](mosquitto/config/mosquitto-open.conf) | Referência da configuração aberta (`allow_anonymous true`), usada na parte 1 |
| [mosquitto/config/mosquitto-secure.conf](mosquitto/config/mosquitto-secure.conf) | Referência da configuração com autenticação, ACL e `log_type all`, usada na parte 2 |
| [mosquitto/config/acl](mosquitto/config/acl) | ACL por tópico com os três papéis |

O `passwd` (criado no passo 3.3), os logs e o banco de persistência são artefatos de execução e não são versionados.

> As portas no host são deslocadas (`20202` para MQTT, `20203` para WebSocket, `9001` para o Grafana) para não conflitar com as outras práticas do módulo. Os comandos abaixo usam `docker exec`, que fala com o broker por dentro do container (porta `1883`); clientes MQTT instalados no host usam `-p 20202`.

## 3. Prática passo a passo

Pré-requisitos: Docker com Docker Compose v2.

### 3.1. Subir o ambiente aberto

```bash
cd M3/Aula_6_seguranca_governanca
docker compose up -d
docker compose ps
```

### 3.2. Demonstrar o broker sem autenticação

Em um terminal, assine tudo:

```bash
docker exec -it opaiot-mosquitto mosquitto_sub -h localhost -t "opaiot/#" -v
```

Em outro terminal, publique sem credencial nenhuma:

```bash
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -t "opaiot/sensors/sensor01/telemetry" -m '{"temperature":25.5}'

docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -t "opaiot/devices/ac01/cmd" -m '{"setpoint":18}'
```

As duas mensagens chegam ao assinante. Qualquer cliente anônimo lê telemetria **e envia comandos a equipamentos** — este é o cenário que a aula corrige. Encerre o `mosquitto_sub` com `Ctrl+C`.

### 3.3. Criar os usuários

Crie o arquivo de senhas com os três papéis (defina uma senha para cada; o `-c` só no primeiro, para criar o arquivo):

```bash
docker exec -it -u mosquitto opaiot-mosquitto mosquitto_passwd -c /mosquitto/config/passwd sensor01
docker exec -it -u mosquitto opaiot-mosquitto mosquitto_passwd /mosquitto/config/passwd monitor01
docker exec -it -u mosquitto opaiot-mosquitto mosquitto_passwd /mosquitto/config/passwd operador01
```

> O `-u mosquitto` é essencial. O `docker exec` roda como `root` por padrão, e o `mosquitto_passwd` cria o arquivo com modo `0600` pertencendo a quem o executou. Como o **broker** roda com o usuário `mosquitto`, um arquivo de root fica ilegível para ele e o Mosquitto encerra com `Error: Unable to open pwfile`.

### 3.4. Proteger os arquivos sensíveis

O `acl` vem do repositório e é legível por todos. O Mosquitto 2.1 ainda aceita, mas avisa que **versões futuras vão recusar** arquivos assim. Ajuste dono e permissão dos dois arquivos:

```bash
docker exec opaiot-mosquitto chown mosquitto:mosquitto /mosquitto/config/acl /mosquitto/config/passwd
docker exec opaiot-mosquitto chmod 0700 /mosquitto/config/acl /mosquitto/config/passwd
```

Arquivos com credenciais e regras de acesso não devem ser legíveis por outros usuários do sistema — é a mesma razão pela qual uma chave SSH privada precisa de `0600`.

### 3.5. Ativar autenticação e ACL

Substitua o conteúdo de `mosquitto/config/mosquitto.conf` pelo de `mosquitto/config/mosquitto-secure.conf` e reinicie o broker:

```bash
cp mosquitto/config/mosquitto-secure.conf mosquitto/config/mosquitto.conf
docker compose restart mosquitto
docker compose logs --tail=8 mosquitto
```

(No PowerShell, use `Copy-Item` em vez de `cp`.) O log deve mostrar o broker abrindo os listeners `1883` e `9001` e terminar com `mosquitto version 2.x running`, sem avisos de permissão. Se aparecer `Unable to open pwfile`, volte ao passo 3.3.

Além da autenticação e da ACL, essa configuração ativa `log_type all`, para que as negações apareçam no log (passo 3.7).

### 3.6. Testar autenticação

Cliente anônimo agora é rejeitado:

```bash
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -t "opaiot/sensors/sensor01/telemetry" -m '{"temperature":25.5}'
```

A resposta é `Connection error: Connection Refused: not authorised.`. Com credencial, funciona (troque `senha` pela que você definiu):

```bash
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -u sensor01 -P senha \
  -t "opaiot/sensors/sensor01/telemetry" -m '{"temperature":25.5}'
```

### 3.7. Testar a ACL papel por papel

Deixe o monitor assinando em um terminal:

```bash
docker exec -it opaiot-mosquitto mosquitto_sub -h localhost \
  -u monitor01 -P senha -t "opaiot/sensors/+/telemetry" -v
```

Em outro terminal, verifique cada regra:

```bash
# PERMITIDO: sensor01 publica a própria telemetria (o monitor recebe)
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -u sensor01 -P senha \
  -t "opaiot/sensors/sensor01/telemetry" -m '{"temperature":26.1}'

# NEGADO (silencioso): sensor01 tenta se passar por sensor02 (nada chega ao monitor)
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -u sensor01 -P senha \
  -t "opaiot/sensors/sensor02/telemetry" -m '{"temperature":99.9}'

# NEGADO (silencioso): sensor01 tenta enviar comando
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -u sensor01 -P senha \
  -t "opaiot/devices/ac01/cmd" -m '{"setpoint":18}'

# PERMITIDO: operador01 envia comando
docker exec -it opaiot-mosquitto mosquitto_pub -h localhost \
  -u operador01 -P senha \
  -t "opaiot/devices/ac01/cmd" -m '{"setpoint":21}'
```

Repare que os dois comandos negados **terminam com sucesso** (código de saída 0) e nada chega ao monitor: a negação por ACL é silenciosa para o cliente. A evidência está no log do broker:

```bash
docker exec opaiot-mosquitto sh -c "tail -40 /mosquitto/log/mosquitto.log" | grep -i denied
```

Cada tentativa negada aparece como `Denied PUBLISH from <client> ... 'opaiot/sensors/sensor02/telemetry'`.

> Isso só funciona porque a configuração segura inclui `log_type all`. Com os tipos de log padrão, a negação não é registrada em lugar nenhum — o evento ficaria invisível para o cliente **e** para a operação. Pense nisso ao projetar auditoria.

### 3.8. Grafana como camada visual

Abra <http://localhost:9001> (usuário `admin`, senha `admin123`). Não há datasource MQTT nativo: discuta (ou esboce) como os dados chegariam até ele — por exemplo, reutilizando a ponte MQTT → Kafka → Prometheus das Aulas 4 e 5, agora com a ponte autenticando no broker como um usuário de **leitura**. Que papel do ACL essa ponte deveria usar?

### 3.9. Encerrar

```bash
docker compose down
```

Para voltar o broker ao estado aberto da parte 1 e refazer a prática do início:

```bash
cp mosquitto/config/mosquitto-open.conf mosquitto/config/mosquitto.conf
rm -f mosquitto/config/passwd
```

### Problemas comuns

- **Mosquitto reinicia em loop** após ativar a configuração segura, com `Error: Unable to open pwfile`: o `passwd` não existe (passo 3.3 pulado) ou foi criado sem `-u mosquitto`, ficando ilegível para o broker. Apague-o (`docker exec opaiot-mosquitto rm -f /mosquitto/config/passwd`) e repita o passo 3.3.
- `Connection Refused: not authorised` com usuário e senha certos: confirme o usuário no arquivo com `docker exec opaiot-mosquitto sh -c 'cut -d: -f1 /mosquitto/config/passwd'` e reinicie o broker (`docker compose restart mosquitto`).
- Avisos `has world readable permissions` ou `owner is not mosquitto` no log: faça o passo 3.4.
- Mudou o ACL e nada aconteceu: o Mosquitto lê o `acl_file` na partida; reinicie o broker após editar.
- Nenhuma linha `Denied` no log: a configuração em uso não tem `log_type all` (confira se o `mosquitto.conf` é mesmo a cópia do `mosquitto-secure.conf`).

## 4. Sugestão de exercícios sobre a prática

1. **Assinatura negada.** Conecte `sensor01` com `mosquitto_sub -t "opaiot/#"`. O cliente conecta, mas o que ele recebe? Confirme no log do broker como uma assinatura negada aparece (compare com a publicação negada).
2. **Novo papel.** Adicione ao ACL um usuário `auditor01` que pode ler **tudo** sob `opaiot/#` mas não pode escrever nada. Crie a senha, reinicie o broker e prove as duas propriedades.
3. **Wildcard e escopo.** O `operador01` pode escrever em `opaiot/devices/+/cmd`. Ajuste a regra para restringi-lo a um único equipamento (`ac01`) e demonstre a diferença. Quando um `+` em ACL é conveniência e quando é risco?
4. **Segundo sensor.** Crie `sensor02` com escrita apenas em `opaiot/sensors/sensor02/telemetry`. Generalize: com o padrão `pattern write opaiot/sensors/%u/telemetry`, o Mosquitto autoriza cada usuário no próprio tópico. Reescreva o ACL usando `pattern` e teste com os dois sensores.
5. **Transporte.** Autenticação por senha em MQTT sem TLS trafega a senha em texto claro. Consulte a documentação do Mosquitto e descreva (sem precisar implementar) o que mudaria no `mosquitto.conf` para servir MQTT sobre TLS: artefatos necessários e portas.
6. **Desafio.** Suba a ponte da [Aula 4](../Aula_4_esp32_mqtt_kafka/README.md) apontando para este broker com o usuário `monitor01` e confirme no log do broker que ela só assina — fechando o ciclo dispositivo → broker autenticado → pipeline de dados.
