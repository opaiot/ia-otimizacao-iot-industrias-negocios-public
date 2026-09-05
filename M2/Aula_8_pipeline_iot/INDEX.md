├── 📄 **QUICKSTART.md** ⭐ **COMECE AQUI**
│   └─ 5 minutos para ficar operacional
│
├── 📖 **README.md** 📚 PRINCIPAL
│   ├─ Arquitetura do sistema
│   ├─ Descrição de componentes
│   ├─ Como usar
│   ├─ Acessar serviços
│   ├─ Configurar Wokwi
│   ├─ API endpoints
│   ├─ Troubleshooting
│   └─ Próximos passos
│
├── 📋 **SETUP.md** 🎓 GUIA DETALHADO
│   ├─ Passo a passo com screenshots
│   ├─ Fase 1: Preparação
│   ├─ Fase 2: Iniciar pipeline
│   ├─ Fase 3: Configurar Wokwi
│   ├─ Fase 4: Visualizar dados
│   ├─ Fase 5: Verificar integração
│   ├─ Comandos úteis
│   ├─ Troubleshooting completo
│   └─ Melhorias futuras
│
├── 🏗️  **ESTRUTURA.md** 🔧 TÉCNICO
│   ├─ Estrutura do projeto
│   ├─ Descrição de arquivos
│   ├─ Fluxo de dados
│   ├─ Variáveis de ambiente
│   ├─ Volumes e redes
│   ├─ Portas expostas
│   └─ Health checks
│
├── 📊 **QUERIES_UTEIS.sql** 🗄️  BANCO DE DADOS
│   ├─ Consultas básicas
│   ├─ Últimos valores
│   ├─ Estatísticas por período
│   ├─ Detecção de anomalias
│   ├─ Análise de série temporal
│   ├─ Exportar dados
│   ├─ Limpeza e manutenção
│   └─ Queries para Grafana
│
├── 🐳 **docker-compose.yml** ⚙️  CONFIG
│   ├─ HiveMQ (broker MQTT)
│   ├─ PostgreSQL + TimescaleDB
│   ├─ Backend Node.js
│   ├─ Grafana
│   └─ Volumes, redes, health checks
│
├── 🔧 **Dockerfile** (em backend/)
│   └─ Imagem Docker do backend Node.js
│
├── 📦 **package.json** (em backend/)
│   ├─ mqtt: Cliente MQTT
│   ├─ pg: PostgreSQL driver
│   └─ dotenv: Environment variables
│
├── 🚀 **backend/index.js** 💻 NODE.JS
│   ├─ Conecta ao HiveMQ
│   ├─ Subscribe em opaiot/temperature
│   ├─ Salva no PostgreSQL
│   ├─ Expõe API HTTP
│   └─ Health checks
│
├── 🗄️  **init-db/01-init.sql** 📊 SQL
│   ├─ Cria hypertable temperature_metrics
│   ├─ Índices e compressão
│   ├─ Retenção de dados
│   ├─ Views úteis
│   └─ Usuário Grafana
│
├── 📊 **grafana/provisioning/datasources/datasources.yml**
│   └─ Conecta PostgreSQL + TimescaleDB
│
├── 📋 **grafana/provisioning/dashboards/dashboards.yml**
│   └─ Configura dashboards
│
├── 📈 **grafana/provisioning/dashboards/iot-temperature-dashboard.json**
│   ├─ Dashboard pré-configurado
│   ├─ Painel: Temperatura atual
│   ├─ Painel: Umidade atual
│   ├─ Painel: Histórico temperatura
│   └─ Painel: Histórico umidade
│
├── 💻 **esp32_dht22_mqtt.ino** 🎯 ARDUINO/WOKWI
│   ├─ Código para ESP32
│   ├─ Lê sensor DHT22
│   ├─ Conecta WiFi
│   ├─ Publica MQTT
│   └─ Comentado em português
│
├── 🐚 **manage.bat** (Windows)
│   ├─ start: Iniciar
│   ├─ stop: Parar
│   ├─ logs: Ver logs
│   ├─ psql: Conectar ao BD
│   └─ test: Testar MQTT
│
├── 🧪 **test-mqtt.sh** (Bash)
│   └─ Script para testar publicação MQTT
│
├── 🔐 **.env.example**
│   └─ Variáveis de ambiente (exemplo)
│
├── 🙈 **.gitignore**
│   └─ Arquivos ignorados pelo Git
│
├── 🧪 **dados-teste.json**
│   └─ Dados de exemplo para testes
│
└── 🎁 **INDEX.md** (este arquivo)
    └─ Lista de todos os arquivos

═════════════════════════════════════════════════════════

## 📚 ORDEM RECOMENDADA DE LEITURA

1. **QUICKSTART.md** ⭐ (começar aqui - 5 min)
2. **SETUP.md** 🎓 (instruções detalhadas - 15 min)
3. **README.md** 📖 (visão geral - 10 min)
4. **ESTRUTURA.md** 🏗️ (entender técnica - 15 min)
5. **docker-compose.yml** (entender config)
6. **QUERIES_UTEIS.sql** (trabalhar com dados)

═════════════════════════════════════════════════════════

## 📂 ARQUIVOS POR PROPÓSITO

### 🚀 Para Começar
- QUICKSTART.md
- SETUP.md

### 📖 Documentação
- README.md
- ESTRUTURA.md
- INDEX.md (este arquivo)

### 🐳 Docker & Infraestrutura
- docker-compose.yml
- backend/Dockerfile
- .env.example
- .gitignore

### 💻 Código
- backend/index.js
- backend/package.json
- esp32_dht22_mqtt.ino

### 🗄️ Banco de Dados
- init-db/01-init.sql
- QUERIES_UTEIS.sql
- dados-teste.json

### 📊 Grafana
- grafana/provisioning/datasources/datasources.yml
- grafana/provisioning/dashboards/dashboards.yml
- grafana/provisioning/dashboards/iot-temperature-dashboard.json

### 🔧 Utilitários
- manage.bat
- test-mqtt.sh

═════════════════════════════════════════════════════════

## 🎯 FLUXO DE TRABALHO

```
1. QUICKSTART.md → Setup rápido (5 min)
   ↓
2. docker-compose up -d → Iniciar sistema
   ↓
3. SETUP.md → Configurar Wokwi (10 min)
   ↓
4. esp32_dht22_mqtt.ino → Código no Wokwi
   ↓
5. Grafana (localhost:3001) → Ver dados em tempo real
   ↓
6. QUERIES_UTEIS.sql → Analisar dados
```

═════════════════════════════════════════════════════════

## 📞 SUPORTE

- **Primeira vez?** → Leia QUICKSTART.md
- **Problemas?** → Veja Troubleshooting em SETUP.md
- **Técnico?** → Consulte ESTRUTURA.md
- **Banco de dados?** → Use QUERIES_UTEIS.sql
- **API?** → Veja README.md → How to Use → API Backend

═════════════════════════════════════════════════════════

**Última atualização: Maio 2026**
**Versão: 1.0.0**
**Aula: Módulo 2 - Aula 8 - Pipeline IoT Fim a Fim**
