# 🎯 Guia Passo a Passo - Pipeline IoT

## Fase 1: Preparação (5 minutos)

### 1.1 Verificar Pré-requisitos

```powershell
# Verificar Docker
docker --version

# Verificar Docker Compose
docker-compose --version

# Ambos devem estar instalados
```

Se não estiverem, instale em: https://www.docker.com/products/docker-desktop

### 1.2 Obter seu IP local

```powershell
# No PowerShell, execute:
ipconfig

# Procure por algo como:
# Endereço IPv4: 192.168.X.X
# OU
# Endereço IPv4: 10.0.X.X

# Anote este IP (você usará no Wokwi)
```

## Fase 2: Iniciar o Pipeline (2 minutos)

### 2.1 Abrir Terminal no Diretório

```powershell
# Navegue para a pasta do projeto
cd D:\opaiot\opaIOT_2026\Modulo_2\Aula_8_pipeline_iot
```

### 2.2 Iniciar Todos os Serviços

```powershell
# Iniciar Docker Compose
docker-compose up -d

# Aguarde 30-60 segundos para todos os serviços iniciarem
```

### 2.3 Verificar Status

```powershell
# Ver status dos containers
docker-compose ps

# Todos devem estar em "Up"
```

## Fase 3: Configurar Wokwi (10 minutos)

### 3.1 Criar Novo Projeto

1. Acesse https://wokwi.com
2. Clique em "Create New Project"
3. Selecione "Arduino"

### 3.2 Adicionar Componentes

Clique no ícone de **+** no Wokwi:

- 1x **ESP32**
- 1x **DHT22**
- 1x **Resistor 10kΩ**

### 3.3 Fazer Conexões

```
DHT22 (lado esquerdo - VIEW IN 3D)
  [VCC] ─────────────> [3.3V] do ESP32
  [GND] ─────────────> [GND] do ESP32
  [DAT] ─┬───────────> [GPIO 15] do ESP32
         └─[R 10kΩ]──> [3.3V]
```

### 3.4 Copiar Código Arduino

1. Copie todo o código de `esp32_dht22_mqtt.ino`
2. Cole no editor de código do Wokwi
3. **IMPORTANTE**: Substitua `YOUR_HOST_IP` pelo seu IP local
   - Exemplo: `192.168.1.100`
   - NÃO use `localhost`

### 3.5 Iniciar Simulação

1. Clique no botão **Play** (▶) no Wokwi
2. Abra o Monitor Serial (Ctrl+Shift+I)
3. Deve aparecer algo como:

```
╔═══════════════════════════════════════╗
║  ESP32 + DHT22 - Publicador MQTT     ║
╚═══════════════════════════════════════╝
Inicializando DHT22... ✓ OK
Conectando ao WiFi: Wokwi-GUEST
...
✓ WiFi conectado! IP: 10.0.0.1
Tentando conectar ao MQTT [192.168.X.X:1883]... ✓ Conectado ao MQTT!
```

## Fase 4: Visualizar Dados em Tempo Real (5 minutos)

### 4.1 Grafana Dashboard

1. Abra https://localhost:3001
2. **Usuário**: admin
3. **Senha**: admin
4. Clique em "Dashboards" no menu lateral
5. Selecione "IoT - Monitoramento de Temperatura"

**Você deve ver**:
- Temperatura em tempo real (em azul)
- Umidade em tempo real (em azul)
- Gráficos com histórico

### 4.2 API Backend

Abra no navegador:
```
http://localhost:3000/api/latest
```

Deve retornar algo como:
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

### 4.3 HiveMQ Web Console

Abra: http://localhost:8080

- Veja os clientes conectados
- Visualize as mensagens publicadas
- Monitor de tópicos

## Fase 5: Verificar Integração (5 minutos)

### 5.1 Validar Pipeline Completo

```
Wokwi (ESP32 + DHT22)
    ↓
HiveMQ (MQTT Broker)
    ↓
Backend Node.js (Subscribe + Persistência)
    ↓
PostgreSQL + TimescaleDB
    ↓
Grafana (Visualização)
```

### 5.2 Testar com Dados Manuais

```powershell
# Publicar um valor de teste
docker-compose exec -T hivemq mosquitto_pub `
  -h localhost `
  -t opaiot/temperature `
  -m '{"temperature": 26.5, "humidity": 65.0, "deviceId": "esp32-dht22", "location": "sala"}'

# Verificar se aparece na API
curl http://localhost:3000/api/latest
```

### 5.3 Verificar Banco de Dados

```powershell
# Conectar ao PostgreSQL
docker-compose exec postgres psql -U iot_user -d iot_database

# Dentro do psql:
SELECT * FROM temperature_metrics ORDER BY time DESC LIMIT 5;
\q
```

## 📊 Estrutura de Dados Esperada

A tabela `temperature_metrics` tem a seguinte estrutura:

```
id              | integer      | ID único do registro
device_id       | text         | "esp32-dht22"
location        | text         | "sala"
temperature     | float        | Valor em °C
humidity        | float        | Valor em %
time            | timestamp    | Quando foi registrado
```

## 🔧 Comandos Úteis

### Ver Logs

```powershell
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Apenas banco de dados
docker-compose logs -f postgres

# Últimas 100 linhas
docker-compose logs --tail=100
```

### Reiniciar Serviços

```powershell
# Reiniciar um serviço específico
docker-compose restart backend

# Reiniciar tudo
docker-compose restart
```

### Parar Tudo

```powershell
# Parar sem remover
docker-compose stop

# Parar e remover
docker-compose down

# Remover TUDO incluindo volumes (⚠️ deleta dados!)
docker-compose down -v
```

### Acessar Containers

```powershell
# Abrir terminal no backend
docker-compose exec backend sh

# Abrir terminal no PostgreSQL
docker-compose exec postgres bash

# Executar psql diretamente
docker-compose exec postgres psql -U iot_user -d iot_database
```

## ❌ Troubleshooting

### Problema: Wokwi não consegue conectar ao MQTT

**Solução:**
1. Verifique se usou o IP correto (não localhost)
2. Verifique se o Docker Compose está rodando
3. Verifique se a porta 1883 não está bloqueada
4. Tente: `docker-compose logs hivemq`

### Problema: Grafana não mostra dados

**Solução:**
1. Verifique se o backend está rodando: `docker-compose ps`
2. Verifique se tem dados no BD: `docker-compose exec postgres psql -U iot_user -d iot_database -c "SELECT COUNT(*) FROM temperature_metrics;"`
3. Recarregue o Grafana (F5)
4. Se tiver poucos dados, toque o play do Wokwi novamente

### Problema: Backend não consegue conectar ao PostgreSQL

**Solução:**
1. Aguarde mais tempo para o banco iniciar (até 60 segundos)
2. Verifique: `docker-compose logs postgres`
3. Tente reiniciar: `docker-compose restart postgres`

### Problema: Porta já está em uso

**Solução:**
```powershell
# Ver qual processo está usando a porta
netstat -ano | findstr :3000
netstat -ano | findstr :5432
netstat -ano | findstr :1883

# Matar o processo (substitua PID)
taskkill /PID <PID> /F

# Ou mudar as portas no docker-compose.yml
```

## 📈 Próximas Melhorias

Depois que tudo estiver funcionando, você pode:

1. **Adicionar Alertas**: Configure alertas no Grafana para temperaturas anormais
2. **Múltiplos Sensores**: Adicione mais ESP32 com IDs diferentes
3. **Histórico Mais Longo**: Modifique a política de retenção no banco
4. **Exportar Dados**: Use queries para exportar dados em CSV
5. **API Mais Robusta**: Adicione autenticação e mais endpoints
6. **InfluxDB**: Migrate para um banco otimizado para séries temporais

## 📞 Suporte

Se tiver problemas:

1. **Leia o README.md** - tem muitas informações
2. **Verifique os logs**: `docker-compose logs -f`
3. **Reinicie tudo**: `docker-compose down && docker-compose up -d`
4. **Aguarde mais tempo**: Alguns serviços levam tempo para iniciar

---

**Sucesso! Seu pipeline IoT deve estar funcionando agora! 🎉**
