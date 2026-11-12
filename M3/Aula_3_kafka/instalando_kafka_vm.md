# Instalando o Apache Kafka na VM

A forma mais simples hoje é instalar o **Apache Kafka 4.3.0** em modo **KRaft**, sem ZooKeeper. A [documentação oficial](https://kafka.apache.org/quickstart) indica o pacote `kafka_2.13-4.3.0.tgz` e exige **Java 17+**.

Faça o passo a passo a seguir na sua VM. Ela é um container Ubuntu, sem `systemd`, com 1 GiB de memória e limite de processos; por isso este roteiro tem alguns ajustes em relação à instalação em uma máquina comum (explicados em cada passo). Detalhes no [guia do ambiente da VM](../ambiente_vm.md).

## 1. Instalar Java no Ubuntu

A VM não traz Java. A instalação leva menos de um minuto:

```bash
sudo apt update
sudo apt install -y openjdk-17-jdk wget tar
```

Verifique:

```bash
java -version
```

Deve aparecer algo como `openjdk version "17..."`.

---

## 2. Baixar o Kafka

```bash
cd /opt
sudo wget https://archive.apache.org/dist/kafka/4.3.0/kafka_2.13-4.3.0.tgz
sudo tar -xzf kafka_2.13-4.3.0.tgz
sudo mv kafka_2.13-4.3.0 kafka
sudo chown -R "$(id -un):$(id -gn)" /opt/kafka
```

Dois cuidados:

- O endereço usa `archive.apache.org` porque o `dlcdn.apache.org` só mantém as versões mais recentes do Kafka, e a 4.3.0 já não está lá (o `wget` termina com `404 Not Found`). Se preferir uma versão mais nova, consulte [kafka.apache.org/downloads](https://kafka.apache.org/downloads) e ajuste a versão em todos os comandos.
- O `chown` usa `$(id -un)` e `$(id -gn)` em vez de `$USER`: na VM a variável `$USER` é **vazia**, e `chown -R $USER:$USER` viraria `chown -R :`, que não muda nada e não dá erro. O Kafka ficaria com o dono `root` e não conseguiria gravar seus logs em `/opt/kafka/logs`.

Entre no diretório:

```bash
cd /opt/kafka
```

---

## 3. Configurar o Kafka em modo KRaft

O Kafka moderno usa **KRaft** como modo nativo de coordenação, dispensando o ZooKeeper.

Gere um ID para o cluster:

```bash
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
echo $KAFKA_CLUSTER_ID
```

Formate o armazenamento:

```bash
bin/kafka-storage.sh format \
  --standalone \
  -t "$KAFKA_CLUSTER_ID" \
  -c config/server.properties
```

Por padrão, o armazenamento fica em `/tmp/kraft-combined-logs`.

---

## 4. Iniciar o Kafka

Inicie o broker **em segundo plano**, limitando o heap da JVM:

```bash
cd /opt/kafka
KAFKA_HEAP_OPTS="-Xms256m -Xmx512m" bin/kafka-server-start.sh -daemon config/server.properties
```

O limite de heap é necessário porque o container tem 1 GiB de memória para tudo, e o Prometheus e o Grafana da VM já usam cerca de 330 MB. Sem a variável `KAFKA_HEAP_OPTS`, o Kafka reserva 1 GB de heap sozinho.

Aguarde alguns segundos e confirme que o broker subiu:

```bash
ss -ltn | grep 9092
grep "Kafka Server started" /opt/kafka/logs/server.log
```

A porta `9092` deve estar em `LISTEN`, e o log deve conter a linha `Kafka Server started`.

> **Alternativa em primeiro plano.** Também é possível rodar `KAFKA_HEAP_OPTS="-Xms256m -Xmx512m" bin/kafka-server-start.sh config/server.properties`. O terminal fica ocupado com os logs do Kafka (use outra sessão SSH para os testes do passo 5), e o Kafka **para** se a sua conexão SSH cair. Para encerrar, `Ctrl+C`.

---

## 5. Testar

Se iniciou o Kafka em segundo plano, pode usar o mesmo terminal. Se iniciou em primeiro plano, abra outra sessão SSH na VM e entre no diretório:

```bash
cd /opt/kafka
```

Crie um tópico:

```bash
bin/kafka-topics.sh \
  --create \
  --topic teste \
  --bootstrap-server localhost:9092
```

Liste os tópicos:

```bash
bin/kafka-topics.sh \
  --list \
  --bootstrap-server localhost:9092
```

Produza mensagens:

```bash
bin/kafka-console-producer.sh \
  --topic teste \
  --bootstrap-server localhost:9092
```

Digite algumas mensagens e encerre com `Ctrl+C`:

```text
ola kafka
mensagem de teste
```

Agora consuma:

```bash
bin/kafka-console-consumer.sh \
  --topic teste \
  --from-beginning \
  --bootstrap-server localhost:9092
```

O consumer continua esperando novas mensagens; encerre com `Ctrl+C`.

---

## 6. Colocar o Kafka no PATH

Para facilitar o uso:

```bash
echo 'export KAFKA_HOME=/opt/kafka' >> ~/.bashrc
echo 'export PATH=$PATH:$KAFKA_HOME/bin' >> ~/.bashrc
export KAFKA_HOME=/opt/kafka
export PATH=$PATH:$KAFKA_HOME/bin
```

As duas últimas linhas valem para a sessão atual. Não use `source ~/.bashrc` aqui: na VM, o `~/.bashrc` mostra o banner de boas-vindas e muda para `~/workspace`.

Agora você pode usar comandos como:

```bash
kafka-topics.sh --list --bootstrap-server localhost:9092
```

O `~/.bashrc` é recriado quando o ambiente reinicia. Se depois de um reinício o `kafka-topics.sh` não for mais encontrado, repita as duas linhas `export`.

---

## 7. Executar o Kafka sem systemd

Em uma máquina comum, o Kafka poderia virar um serviço do `systemd` (`kafka.service`, `systemctl enable`, `journalctl -u kafka`). **Isso não funciona na VM do curso**: ela é um container em que o processo 1 é um `sleep infinity`, e `systemctl` responde `System has not been booted with systemd as init system (PID 1). Can't operate.`

No lugar do serviço, use o modo em segundo plano do passo 4 e estes comandos:

| Tarefa | Comando |
| --- | --- |
| Ver se o Kafka está rodando | `pgrep -af 'kafka\.Kafka'` |
| Ver o log | `tail -f /opt/kafka/logs/server.log` (saia com `Ctrl+C`) |
| Parar o Kafka | `/opt/kafka/bin/kafka-server-stop.sh` |
| Iniciar de novo | o comando do passo 4 |

Se o Kafka for parado e iniciado de novo, os tópicos e mensagens continuam lá, porque o armazenamento em `/tmp/kraft-combined-logs` é mantido. Se essa pasta tiver sido apagada, repita o passo 3 (formatar) antes de iniciar. Depois que o ambiente reinicia, o Kafka **não** volta sozinho: inicie-o de novo.

---

## 8. Limites do ambiente e problemas comuns

O container tem 1 GiB de memória e um limite de 256 processos e threads (veja o [guia da VM](../ambiente_vm.md#6-limites-de-memória-e-de-processos)). O broker do Kafka sozinho usa cerca de 108 threads, e cada comando `kafka-*.sh` abre uma JVM que usa mais algumas dezenas por alguns segundos. Por isso:

- Rode **um** comando `kafka-*.sh` de cada vez, em vez de vários ao mesmo tempo.
- Se aparecer `pthread_create failed (EAGAIN)`, `Failed to start the native thread` ou `Resource temporarily unavailable`, o limite de processos foi atingido: encerre o que não está usando (consumers, produtores e sessões com processos pendurados) e repita o comando.
- Confira o uso com `cat /sys/fs/cgroup/pids.current /sys/fs/cgroup/pids.max`.

Outros problemas:

- `Permission denied` ao iniciar o Kafka: confira o dono com `ls -ld /opt/kafka`. Deve ser o seu usuário; se for `root`, corrija com `sudo chown -R "$(id -un):$(id -gn)" /opt/kafka`.
- Porta `9092` em uso: já existe um Kafka rodando (`pgrep -af 'kafka\.Kafka'`).
- O Kafka não sobe e o log não ajuda: veja também `/opt/kafka/logs/kafkaServer.out`.

---

## Observação importante para VM

Por padrão, o Kafka escuta em `localhost:9092`. Isso funciona dentro da própria VM. Se você quiser acessar o Kafka a partir da sua máquina host ou de outro container, será necessário ajustar o `advertised.listeners` no arquivo:

```bash
nano /opt/kafka/config/server.properties
```

Para uso local na VM, não precisa alterar nada. Nesta VM o túnel SSH está bloqueado; por isso o Kafka da prática é usado de dentro da própria VM.

[Referência: Quickstart Apache Kafka](https://kafka.apache.org/quickstart)
