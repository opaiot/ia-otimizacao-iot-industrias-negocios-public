# 🦟 Eclipse Mosquitto - Broker MQTT

## Por que Mosquitto?

A imagem `hivemq/hivemq` é proprietária e requer autenticação Docker Hub. O **Eclipse Mosquitto** é:

✅ **Open Source** - Código aberto e gratuito  
✅ **Leve** - ~15MB de imagem Docker  
✅ **Rápido** - Excelente performance  
✅ **Confiável** - Amplamente usado em produção  
✅ **Compatível** - MQTT 3.1 e 5.0  

## 📋 Configuração Atual

**Arquivo**: `mosquitto/config/mosquitto.conf`

### Listeners Habilitados:
- **1883** - MQTT não-criptografado (padrão)
- **8883** - MQTT com TLS (comentado, para produção)

### Segurança:
- ✅ Conexões anônimas permitidas (desenvolvimento)
- ✅ Persistência habilitada
- ✅ Logs completos

### Performance:
- Max 1000 mensagens enfileiradas
- Autosave a cada 30 minutos
- Connection_messages desabilitadas

## 🔧 Personalizar Configuração

### 1. Habilitar TLS (Produção)

Edite `mosquitto/config/mosquitto.conf`:

```conf
listener 8883
protocol mqtt
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
```

### 2. Adicionar Autenticação

Crie arquivo `mosquitto/config/passwd`:

```bash
# No container, gere hash da senha
mosquitto_passwd -c /mosquitto/config/passwd user1
```

Depois edite `mosquitto.conf`:

```conf
password_file /mosquitto/config/passwd
```

### 3. Habilitar WebSocket (Opcional)

Edite `mosquitto/config/mosquitto.conf`:

```conf
listener 9001
protocol websockets
socket_domain ipv4
```

Mapeie a porta no `docker-compose.yml`:

```yaml
ports:
  - "9001:9001"  # WebSocket
```

## 📡 Testar Mosquitto

### 1. Subscribe em tópico

```bash
docker-compose exec mosquitto mosquitto_sub -t opaiot/# -v
```

### 2. Publicar mensagem

```bash
docker-compose exec mosquitto mosquitto_pub \
  -t opaiot/temperature \
  -m '{"temperature": 25.5, "humidity": 60.0}'
```

### 3. Verificar status

```bash
docker-compose logs mosquitto
```

## 📊 Comparação: Mosquitto vs HiveMQ

| Aspecto | Mosquitto | HiveMQ |
|---------|-----------|--------|
| **Licença** | Open Source (EPL 2.0) | Proprietário |
| **Custo** | Gratuito | Pago |
| **Docker Hub** | Gratuito | Requer autenticação |
| **Tamanho** | ~15MB | ~600MB |
| **Performance** | Excelente | Muito boa |
| **Web UI** | Não (nativo) | Sim |
| **Clustering** | Limitado | Nativo |
| **Uso Típico** | IoT, Edge | Enterprise |

## 🚀 Próximos Passos

Para ambiente **desenvolvimento**: ✅ Configuração atual está ótima

Para ambiente **produção**, considere:

1. **Habilitar TLS** - Criptografia de conexões
2. **Adicionar autenticação** - Usuário e senha
3. **Configurar ACL** - Controle de acesso por tópico
4. **Aumentar limites** - `max_queued_messages`, `max_connections`
5. **Monitorar** - Integrar com Prometheus/Grafana

## 📚 Recursos

- [Mosquitto Documentation](https://mosquitto.org/documentation/)
- [Configuration Manual](https://mosquitto.org/man/mosquitto-conf-5.html)
- [MQTT Protocol](https://mqtt.org/)

## 🐛 Troubleshooting

### Erro: "Can't open socket for listening"

Certifique-se de que a porta 1883 não está em uso:

```powershell
netstat -ano | findstr :1883
```

### Erro: "Connection refused"

Verifique se o container está rodando:

```powershell
docker-compose ps
# Deve mostrar mosquitto "Up"
```

### Sem logs

Verifique permissões do diretório `/mosquitto/log`:

```bash
docker-compose exec mosquitto ls -la /mosquitto/log/
```

---

**Mosquitto versão**: `latest` (acompanha atualizações de segurança)  
**Instalado em**: `mosquitto/config/`  
**Último update**: Maio 2026
