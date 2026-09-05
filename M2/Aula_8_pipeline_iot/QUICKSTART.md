# 🚀 Início Rápido - Pipeline IoT

> ⏱️ **5 minutos para ficar operacional**

## 1️⃣ Verificar Pré-requisitos (30 segundos)

```powershell
docker --version
docker-compose --version
```

Se não tiver, instale: https://www.docker.com/products/docker-desktop

## 2️⃣ Obter seu IP Local (1 minuto)

```powershell
ipconfig
# Procure por "Endereço IPv4" (exemplo: 192.168.1.100)
# Você usará este IP no Wokwi
```

## 3️⃣ Iniciar Pipeline (2 minutos)

```powershell
cd D:\opaiot\opaIOT_2026\Modulo_2\Aula_8_pipeline_iot
docker-compose up -d
```

Aguarde até 60 segundos. Verificar status:

```powershell
docker-compose ps
# Todos devem estar "Up"
```

## 4️⃣ Acessar Serviços (1 minuto)

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| 📊 **Grafana** | http://localhost:3001 | admin / admin |
| � **API Backend** | http://localhost:3000/api/latest | - |
| 🦟 **MQTT** | mqtt://localhost:1883 | - |

## 5️⃣ Configurar Wokwi (5 minutos)

1. Acesse https://wokwi.com e crie novo projeto Arduino
2. Adicione: **ESP32** + **DHT22** + **Resistor 10kΩ**
3. Faça as conexões (ver em [SETUP.md](SETUP.md))
4. Copie código de [esp32_dht22_mqtt.ino](esp32_dht22_mqtt.ino)
5. **Troque `YOUR_HOST_IP` pelo seu IP local** (ex: 192.168.1.100)
6. Clique Play ▶

## 📊 Você deve ver:

- ✅ Wokwi: Mensagens no Serial Monitor
- ✅ Grafana: Gráficos de temperatura em tempo real
- ✅ API: Dados em http://localhost:3000/api/latest

## 🛑 Parar Tudo

```powershell
docker-compose down
```

---

## 📚 Documentação Completa

- **[README.md](README.md)** - Visão geral completa
- **[SETUP.md](SETUP.md)** - Guia passo a passo detalhado
- **[ESTRUTURA.md](ESTRUTURA.md)** - Detalhes técnicos
- **[QUERIES_UTEIS.sql](QUERIES_UTEIS.sql)** - Exemplos de banco de dados

## ❓ Problemas?

| Problema | Solução |
|----------|---------|
| Wokwi não conecta | Verifique se usou o IP correto (não localhost) |
| Grafana sem dados | Aguarde 60s ou reinicie: `docker-compose restart` |
| Porta em uso | `netstat -ano \| findstr :3000` depois `taskkill /PID xxx /F` |
| Precisa de ajuda | Veja [SETUP.md → Troubleshooting](SETUP.md#-troubleshooting) |

---

**Pronto para começar? Vá para [SETUP.md](SETUP.md)! 🎉**
