# Pipeline IoT Fim a Fim - Aula 8 🚀

Sistema completo de IoT com **DHT22 → Mosquitto (MQTT) → Node.js Backend → PostgreSQL/TimescaleDB → Grafana**

## 📋 Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                          Wokwi (Externo)                        │
│                   ESP32 + DHT22 Simulador                        │
└─────────────────────────────┬──────────────────────────────────┘
                              │
                              │ MQTT (opaiot/temperature)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Eclipse Mosquitto (MQTT Broker)            │   │
│  │              (MQTT Pub/Sub - Port 1883)                │   │
│  └─────────────────┬───────────────────┬──────────────────┘   │
│                    │                   │                       │
│        Subscribe   │                   │ Publish              │
│                    ▼                   ▼                       │
│  ┌─────────────────────────┐  ┌──────────────────────────┐    │
│  │  Node.js Backend        │  │  Backend Status Topics  │    │
│  │  - MQTT Client          │  │  - backend/status       │    │
│  │  - PostgreSQL Client    │  │  - Data Metrics         │    │
│  │  - HTTP API (3000)      │  └──────────────────────────┘    │
│  └─────────────┬───────────┘                                   │
│                │ INSERT                                        │
│                ▼                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │    PostgreSQL + TimescaleDB (Port 5432)                │  │
│  │  - Hypertables para séries temporais                  │  │
│  │  - Compressão automática de dados                     │  │
│  │  - Retenção de 30 dias                                │  │
│  └─────────────────────────────────────────────────────────┘  │
│                │                                               │
│                │ SELECT                                       │
│                ▼                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │    Grafana Dashboard (Port 3001)                       │  │
│  │  - Visualização em tempo real                          │  │
│  │  - Gráficos de temperatura e umidade                   │  │
│  │  - Alertas e notificações                              │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Componentes

### 1. **Eclipse Mosquitto** (Broker MQTT - Open Source)
- Recebe mensagens dos sensores ESP32/DHT22
- Distribui mensagens aos subscribers
- Leve, rápido e confiável
- Sem interface web (mas logs completos)

### 2. **Node.js Backend**
- Faz subscribe no tópico `opaiot/temperature`
- Recebe dados do DHT22
- Armazena no PostgreSQL
- Expõe API HTTP para consultas
- **Porta**: 3000

### 3. **PostgreSQL + TimescaleDB**
- Banco de dados otimizado para séries temporais
- Hypertables para melhor performance
- Compressão automática de dados antigos
- Retenção de 30 dias
- **Porta**: 5432

### 4. **Grafana**
- Visualização de dados em tempo real
- Dashboard pré-configurado
- Suporte a alertas
- **URL**: http://localhost:3001
- **Credenciais**: admin / admin

## 🚀 Como Usar

### Pré-requisitos
- Docker e Docker Compose instalados
- Git para clonar o repositório

### 1. Iniciar os serviços

```bash
cd Modulo_2/Aula_8_pipeline_iot
docker-compose up -d
```

Verificar se tudo está iniciando:
```bash
docker-compose logs -f
```

### 2. Verificar status dos serviços

```bash
# Listar containers em execução
docker-compose ps

# Ver logs do backend
docker-compose logs backend

# Ver logs do PostgreSQL
docker-compose logs postgres

# Ver logs do Mosquitto
docker-compose logs mosquitto
```

### 3. Configurar Wokwi (Simulador)

Criar um novo projeto no [Wokwi.com](https://wokwi.com) com:

#### Componentes:
- 1x ESP32
- 1x DHT22
- 1x Resistor 10kΩ (pull-up para DATA do DHT22)

#### Conexões:
- DHT22 VCC → ESP32 3.3V
- DHT22 GND → ESP32 GND
- DHT22 DATA → ESP32 GPIO 15 (com resistor 10kΩ para 3.3V)

#### Código Arduino (Para usar no Wokwi):

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

// ========== CONFIGURAÇÕES WOKWI ==========
#define DHTPIN 15      // Pino do DHT22
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// WiFi Wokwi (use as credenciais do Wokwi)
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// MQTT - Use o IP da máquina host (NÃO localhost)
// Para encontrar seu IP, execute no PowerShell: ipconfig
const char* mqtt_server = "YOUR_HOST_IP";  // Ex: 192.168.1.100
const int mqtt_port = 1883;
const char* mqtt_topic = "opaiot/temperature";

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
const long interval = 5000; // Publicar a cada 5 segundos

void setup() {
  Serial.begin(115200);
  dht.begin();
  
  // Conectar ao WiFi
  Serial.print("Conectando ao WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi conectado! IP: ");
    Serial.println(WiFi.localIP());
  }
  
  // Conectar ao MQTT
  client.setServer(mqtt_server, mqtt_port);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conectar ao MQTT...");
    
    String clientId = "ESP32-DHT22-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("Conectado ao MQTT!");
      client.publish("backend/sensor", "ESP32 DHT22 conectado!");
    } else {
      Serial.print("Falha. Código: ");
      Serial.print(client.state());
      Serial.println(" Tentando novamente em 5s...");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;
    
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Erro ao ler DHT22!");
      return;
    }
    
    Serial.print("Temperatura: ");
    Serial.print(temperature);
    Serial.print("°C  Umidade: ");
    Serial.print(humidity);
    Serial.println("%");
    
    // Criar JSON
    String payload = "{\"temperature\": " + String(temperature) + 
                     ", \"humidity\": " + String(humidity) + 
                     ", \"deviceId\": \"esp32-dht22\", \"location\": \"sala\"}";
    
    // Publicar
    client.publish(mqtt_topic, payload.c_str());
  }
}
```

### 4. Obter IP da sua máquina

No **PowerShell** (Windows):
```powershell
ipconfig
```

Procure por `Endereço IPv4` na seção do seu adaptador de rede. Esse é o IP que você usará no código do Wokwi.

### 5. Acessar os serviços

#### Grafana (Dashboard)
```
URL: http://localhost:3001
Usuário: admin
Senha: admin
```

#### HiveMQ Web Console
```
URL: http://localhost:8080
```

#### API Backend
```
GET http://localhost:3000/api/latest        # Último registro
GET http://localhost:3000/api/data?hours=24 # Últimas 24h
GET http://localhost:3000/api/status        # Status do sistema
GET http://localhost:3000/health            # Health check
```

## 📊 Exemplo de Resposta da API

```json
{
  "id": 1,
  "device_id": "esp32-dht22",
  "location": "sala",
  "temperature": 25.5,
  "humidity": 60.0,
  "time": "2026-05-11T14:30:00.000Z"
}
```

## 🗄️ Estrutura do Banco de Dados

### Tabela: `temperature_metrics`
```sql
SELECT * FROM temperature_metrics;

-- Colunas:
-- id: BIGSERIAL PRIMARY KEY
-- device_id: VARCHAR(255)
-- location: VARCHAR(255)
-- temperature: FLOAT8
-- humidity: FLOAT8
-- time: TIMESTAMPTZ (coluna TIME - hypertable)
```

### Views Úteis
```sql
-- Últimos valores por dispositivo
SELECT * FROM v_latest_temperatures;

-- Média horária
SELECT * FROM v_hourly_average;
```

## 🛑 Parar os serviços

```bash
docker-compose down

# Ou, se quiser manter os volumes (dados):
docker-compose down --volumes
```

## 📝 Logs e Troubleshooting

### Ver logs em tempo real
```bash
docker-compose logs -f backend
```

### Conectar ao PostgreSQL
```bash
docker-compose exec postgres psql -U iot_user -d iot_database

-- Listar tabelas
\dt

-- Ver últimos registros
SELECT * FROM temperature_metrics ORDER BY time DESC LIMIT 10;

-- Ver estatísticas
SELECT * FROM hypertable_detailed_size('temperature_metrics');
```

### Conectar ao MQTT (testar publicação)
```bash
docker-compose exec hivemq sh

# Dentro do container:
mosquitto_pub -h localhost -t opaiot/temperature -m '{"temperature": 26.5, "humidity": 65}'
```

## 🔧 Configurações Principais

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `MQTT_BROKER` | `hivemq` | Host do broker MQTT |
| `MQTT_PORT` | `1883` | Porta MQTT |
| `MQTT_TOPIC` | `opaiot/temperature` | Tópico de publicação |
| `DB_HOST` | `postgres` | Host do PostgreSQL |
| `DB_PORT` | `5432` | Porta do PostgreSQL |
| `DB_USER` | `iot_user` | Usuário do DB |
| `DB_PASSWORD` | `iot_password` | Senha do DB |
| `DB_NAME` | `iot_database` | Nome do database |


## 📚 Recursos Úteis

- [HiveMQ Documentation](https://www.hivemq.com/docs/)
- [TimescaleDB Guide](https://docs.timescale.com/)
- [Grafana Docs](https://grafana.com/docs/)
- [MQTT Protocol](https://mqtt.org/)
- [Wokwi Simulator](https://wokwi.com/)

## 📞 Suporte

Para erros ou dúvidas, verifique:
1. Se todos os containers estão rodando: `docker-compose ps`
2. Se o Wokwi está usando o IP correto
3. Os logs dos serviços: `docker-compose logs <service>`

---

**Criado para a Aula 8 - Pipeline IoT Fim a Fim** 🎓
