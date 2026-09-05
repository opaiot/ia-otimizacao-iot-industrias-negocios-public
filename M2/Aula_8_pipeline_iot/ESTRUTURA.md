# Estrutura do Projeto - Pipeline IoT

```
Aula_8_pipeline_iot/
│
├── README.md                           # Documentação principal
├── SETUP.md                            # Guia passo a passo
├── docker-compose.yml                  # Orquestração de containers
├── manage.bat                          # Script de gerenciamento (Windows)
├── test-mqtt.sh                        # Script de teste MQTT
├── esp32_dht22_mqtt.ino               # Código Arduino para Wokwi
├── .env.example                        # Variáveis de ambiente (exemplo)
├── .gitignore                          # Arquivos ignorados pelo Git
│
├── backend/                            # Backend Node.js
│   ├── Dockerfile                      # Container do backend
│   ├── package.json                    # Dependências Node.js
│   ├── index.js                        # Aplicação principal
│   └── node_modules/                   # Dependências instaladas
│
├── init-db/                            # Scripts de inicialização do BD
│   └── 01-init.sql                    # Criar tabelas e configurações
│
├── grafana/                            # Configurações do Grafana
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml         # Conexão com PostgreSQL
│       └── dashboards/
│           ├── dashboards.yml          # Provisionamento de dashboards
│           └── iot-temperature-dashboard.json  # Dashboard principal
│
└── postgres-data/                      # Dados do PostgreSQL (volume)
    └── [criado automaticamente pelo Docker]
```

## Descrição de Arquivos

### Arquivos de Configuração

#### `docker-compose.yml`
- Define todos os serviços (Mosquitto, PostgreSQL, Backend, Grafana)
- Configuração de redes internas
- Mapeamento de portas
- Variáveis de ambiente
- Health checks

#### `manage.bat`
- Script auxiliar para Windows
- Comandos: start, stop, restart, status, logs, clean, test, psql, build

#### `.env.example`
- Exemplo de variáveis de ambiente
- Copie como `.env` para configurar valores personalizados

#### `.gitignore`
- Evita commitar: `.env`, `node_modules/`, dados de BD, logs

### Backend Node.js

#### `backend/Dockerfile`
- Cria imagem Docker do backend
- Usa Node.js 18 Alpine (leve e rápido)
- Instala dependências e inicia aplicação

#### `backend/package.json`
- Dependências do Node.js:
  - `mqtt`: Cliente MQTT
  - `pg`: Driver PostgreSQL
  - `dotenv`: Carregador de variáveis de ambiente

#### `backend/index.js`
- **Conecta ao Mosquitto**: MQTT client
- **Subscreve ao tópico**: `opaiot/temperature`
- **Recebe mensagens**: Do DHT22 via Wokwi
- **Salva no banco**: Insere em `temperature_metrics`
- **Expõe API HTTP**: 
  - GET `/health` - Status
  - GET `/api/latest` - Último valor
  - GET `/api/data?hours=24` - Histórico

### Banco de Dados

#### `init-db/01-init.sql`
- Cria extensão TimescaleDB
- Define tabela `temperature_metrics` como hypertable
- Cria índices para performance
- Políticas de compressão e retenção
- Views úteis (`v_latest_temperatures`, `v_hourly_average`)
- Usuário Grafana com permissões de leitura

### Grafana

#### `grafana/provisioning/datasources/datasources.yml`
- Define conexão com PostgreSQL
- Credenciais do usuario `grafana_reader`
- Detecta TimescaleDB

#### `grafana/provisioning/dashboards/iot-temperature-dashboard.json`
- Dashboard pré-configurado
- 4 painéis:
  1. Temperatura atual (stat)
  2. Umidade atual (stat)
  3. Histórico de temperatura (série temporal)
  4. Histórico de umidade (série temporal)

### Código Arduino

#### `esp32_dht22_mqtt.ino`
- Código completo do ESP32 para Wokwi
- Comentário detalhado em português
- Lê DHT22 a cada 5 segundos
- Publica JSON no MQTT
- Reconecta automaticamente se cair

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│ Wokwi (Externo)                                             │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ESP32 (Simulador)                                     │   │
│ │ - Lê sensor DHT22                                     │   │
│ │ - Conecta WiFi "Wokwi-GUEST"                         │   │
│ │ - Conecta MQTT [seu_ip:1883]                         │   │
│ │ - Publica JSON a cada 5s                             │   │
│ └─────────────────┬───────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                      │
                      │ MQTT Frame
                      │ Tópico: opaiot/temperature
                      │ Payload: {"temperature": 25.5, ...}
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Docker Compose Network (Seu Computador)                    │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Mosquitto (Port 1883 - MQTT Broker)                  │   │
│ │ - Recebe mensagens                                   │   │
│ │ - Distribui para subscribers                         │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    │                                       │
│                    │ MQTT Subscribe                       │
│                    ▼                                       │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Backend Node.js (Port 3000)                          │   │
│ │ - MQTT Client (subscreve opaiot/temperature)        │   │
│ │ - Parse JSON da mensagem                            │   │
│ │ - Valida dados                                       │   │
│ │ - Cria query INSERT                                  │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    │                                       │
│                    │ INSERT                                │
│                    ▼                                       │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ PostgreSQL + TimescaleDB (Port 5432)                 │   │
│ │ - Recebe INSERT via socket TCP                       │   │
│ │ - Escreve em temperature_metrics (hypertable)       │   │
│ │ - Compressão automática                              │   │
│ │ - Mantém 30 dias de histórico                        │   │
│ └──────────────────┬─────────────────────────────────┘   │
│                    │                                       │
│                    │ SELECT (polling)                     │
│                    ▼                                       │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Grafana (Port 3001 - Port 80 na host)                │   │
│ │ - Conecta PostgreSQL a cada 10s (refresh)           │   │
│ │ - Executa queries                                    │   │
│ │ - Renderiza gráficos em tempo real                   │   │
│ │ - Acesso via browser: http://localhost:3001         │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                      ▲
                      │ HTTPS
                      │
            ┌─────────────────┐
            │ Seu Navegador   │
            │ (localhost:3001)│
            └─────────────────┘
```

## Variáveis de Ambiente

### MQTT
```
MQTT_BROKER=mosquitto           # Nome do serviço Docker
MQTT_PORT=1883                  # Porta MQTT
MQTT_TOPIC=opaiot/temperature   # Tópico de publicação
```

### PostgreSQL
```
POSTGRES_USER=iot_user
POSTGRES_PASSWORD=iot_password
POSTGRES_DB=iot_database
DB_HOST=postgres
DB_PORT=5432
```

### Grafana
```
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
TZ=America/Sao_Paulo
```

## Volumes (Persistência de Dados)

| Volume | Destino | Descrição |
|--------|---------|-----------|
| `postgres-data` | `/var/lib/postgresql/data` | Dados do banco PostgreSQL |
| `mosquitto-data` | `/mosquitto/data` | Dados do Mosquitto |
| `mosquitto-logs` | `/mosquitto/log` | Logs do Mosquitto |
| `grafana-storage` | `/var/lib/grafana` | Configurações do Grafana |

## Redes Docker

Rede: `iot-network` (bridge)

Conecta:
- Mosquitto
- PostgreSQL
- Backend
- Grafana

Permite comunicação interna entre containers usando nomes (ex: `mosquitto:1883`)

## Portas Expostas

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Mosquitto MQTT | 1883 | Protocolo MQTT |
| Mosquitto MQTT-TLS | 8883 | MQTT com TLS |
| Backend API | 3000 | API HTTP |
| PostgreSQL | 5432 | Banco de dados |
| Grafana | 3001 | Dashboard web |

## Health Checks

Cada serviço tem um health check:

```
mosquitto:  mosquitto_sub -h 127.0.0.1 -t $SYS/broker/uptime -E
postgres:   pg_isready -U iot_user
grafana:    curl -f http://localhost:3000/api/health
```

O Docker Compose aguarda esses checks antes de iniciar dependências.

---

Última atualização: Maio 2026
