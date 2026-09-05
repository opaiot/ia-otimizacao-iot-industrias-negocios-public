A forma mais simples hoje é instalar o **Apache Kafka 4.3.0** em modo **KRaft**, sem ZooKeeper. A documentação oficial indica Kafka `kafka_2.13-4.3.0.tgz` e exige **Java 17+**. ([kafka.apache.org][1])

Faça o passo a passo a seguir na sua VM.

## 1. Instalar Java no Ubuntu

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

## 2. Baixar o Kafka mais recente

```bash
cd /opt
sudo wget https://dlcdn.apache.org/kafka/4.3.0/kafka_2.13-4.3.0.tgz
sudo tar -xzf kafka_2.13-4.3.0.tgz
sudo mv kafka_2.13-4.3.0 kafka
sudo chown -R $USER:$USER /opt/kafka
```

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

---

## 4. Iniciar o Kafka

```bash
bin/kafka-server-start.sh config/server.properties
```

O terminal ficará ocupado com os logs do Kafka.

---

## 5. Testar em outro terminal

Abra outro terminal SSH na VM e rode:

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

Digite algumas mensagens:

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

---

## 6. Colocar o Kafka no PATH

Para facilitar o uso:

```bash
echo 'export KAFKA_HOME=/opt/kafka' >> ~/.bashrc
echo 'export PATH=$PATH:$KAFKA_HOME/bin' >> ~/.bashrc
source ~/.bashrc
```

Agora você pode usar comandos como:

```bash
kafka-topics.sh --list --bootstrap-server localhost:9092
```

---

## 7. Criar serviço systemd opcional

Para iniciar o Kafka como serviço:

```bash
sudo nano /etc/systemd/system/kafka.service
```

Cole:

```ini
[Unit]
Description=Apache Kafka Server
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=/opt/kafka
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Substitua `%i` pelo seu usuário real. Por exemplo:

```ini
User=junio
```

Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kafka
sudo systemctl start kafka
```

Verifique:

```bash
sudo systemctl status kafka
```

Logs:

```bash
journalctl -u kafka -f
```

---

## Observação importante para VM

Por padrão, o Kafka escuta em `localhost:9092`. Isso funciona dentro da própria VM. Se você quiser acessar o Kafka a partir da sua máquina host ou de outro container, será necessário ajustar o `advertised.listeners` no arquivo:

```bash
nano /opt/kafka/config/server.properties
```

Para uso local na VM, não precisa alterar nada.

[Referência: Quickstart Apache Kafka](https://kafka.apache.org/quickstart)
