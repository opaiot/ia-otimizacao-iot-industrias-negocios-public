/*
 * ========================================
 * CÓDIGO PARA WOKWI - ESP32 + DHT22
 * Publicador MQTT de Dados de Temperatura
 * ========================================
 *
 * Este código simula um sensor de temperatura e umidade (DHT22)
 * conectado a um ESP32, que publica os dados em um broker MQTT.
 *
 * Componentes:
 * - ESP32
 * - DHT22 (Sensor de Temperatura e Umidade)
 * - Resistor 10kΩ (pull-up no pino DATA do DHT22)
 */

#include <WiFi.h>         // Biblioteca para conexão WiFi
#include <PubSubClient.h> // Biblioteca para MQTT
#include "DHT.h"          // Biblioteca para DHT22

// ========================================
// CONFIGURAÇÕES DOS PINOS
// ========================================

// Pino GPIO do ESP32 onde o DHT22 está conectado
#define DHTPIN 15
// Tipo do sensor (DHT22 é mais preciso que DHT11)
#define DHTTYPE DHT22

// Criar objeto do sensor DHT
DHT dht(DHTPIN, DHTTYPE);

// ========================================
// CONFIGURAÇÕES DE REDE
// ========================================

// ATENÇÃO: Para Wokwi, estas são as credenciais padrão
// Em um projeto real, use credenciais reais do seu WiFi
const char *ssid = "Wokwi-GUEST"; // Nome da rede WiFi
const char *password = "";        // Senha (vazia para Wokwi)

// ========================================
// CONFIGURAÇÕES MQTT
// ========================================

// IP da máquina que está rodando o Docker Compose
// IMPORTANTE: Use seu IP local, NÃO "localhost"
// No PowerShell, execute: ipconfig
// Procure por "Endereço IPv4" e use esse valor
// Exemplo: "192.168.1.100"
const char *mqtt_server = "YOUR_HOST_IP";

// Porta MQTT (padrão é 1883)
const int mqtt_port = 1883;

// Tópico onde vamos publicar os dados
// Este deve ser o mesmo configurado no docker-compose.yml
const char *mqtt_topic = "opaiot/temperature";

// ========================================
// OBJETOS GLOBAIS
// ========================================

// Cliente WiFi (conexão de rede)
WiFiClient espClient;

// Cliente MQTT (conexão com o broker de mensagens)
PubSubClient client(espClient);

// Variável para controlar o tempo de publicação
unsigned long lastMsg = 0;

// Intervalo entre publicações (em milissegundos)
// 5000 = 5 segundos
const long interval = 5000;

// ========================================
// FUNÇÃO: setup()
// ========================================
// Executada uma única vez quando o ESP32 é ligado

void setup()
{
    // Inicializar comunicação serial (para debug no Monitor)
    Serial.begin(115200);

    // Pequeno delay para garantir que o serial está pronto
    delay(100);

    Serial.println();
    Serial.println("╔═══════════════════════════════════════╗");
    Serial.println("║  ESP32 + DHT22 - Publicador MQTT     ║");
    Serial.println("╚═══════════════════════════════════════╝");

    // ========== INICIALIZAR DHT22 ==========
    Serial.print("Inicializando DHT22... ");
    dht.begin();
    Serial.println("✓ OK");

    // ========== CONECTAR WiFi ==========
    Serial.print("Conectando ao WiFi: ");
    Serial.println(ssid);

    // WiFi.begin() inicia a conexão com a rede
    WiFi.begin(ssid, password);

    // Loop de espera até conectar
    int attempts = 0;
    const int maxAttempts = 20; // Máximo de tentativas

    while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts)
    {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.print("✓ WiFi conectado! IP: ");
        Serial.println(WiFi.localIP());
    }
    else
    {
        Serial.println("✗ Falha ao conectar WiFi");
        Serial.println("Continuando mesmo assim...");
    }

    // ========== CONFIGURAR MQTT ==========
    // Informar ao cliente MQTT qual é o servidor e porta
    client.setServer(mqtt_server, mqtt_port);

    // Configurar intervalo de reconexão
    // Se a conexão cair, tentará reconectar automaticamente
    client.setKeepAlive(60); // 60 segundos
}

// ========================================
// FUNÇÃO: reconnect()
// ========================================
// Tenta estabelecer/restabelecer conexão com o broker MQTT

void reconnect()
{
    int attempts = 0;
    const int maxAttempts = 5;

    // Loop enquanto não estiver conectado
    while (!client.connected() && attempts < maxAttempts)
    {
        Serial.print("Tentando conectar ao MQTT [");
        Serial.print(mqtt_server);
        Serial.print(":");
        Serial.print(mqtt_port);
        Serial.print("]... ");

        // Criar ID único para o cliente
        // Isso permite ter múltiplos ESP32 conectados simultaneamente
        String clientId = "ESP32-DHT22-";
        clientId += String(random(0xffff), HEX);

        // Tentar conectar
        if (client.connect(clientId.c_str()))
        {
            Serial.println("✓ Conectado ao MQTT!");

            // Publicar mensagem de status (opcional)
            // Serve para confirmar que o dispositivo está online
            String statusMsg = "ESP32 " + clientId + " conectado!";
            client.publish("backend/sensor-status", statusMsg.c_str());
        }
        else
        {
            // Se falhar, mostrar código de erro
            Serial.print("✗ Falha. Código: ");
            Serial.print(client.state());
            Serial.println(" Tentando novamente em 5s...");

            // Aguardar 5 segundos antes de tentar novamente
            delay(5000);
            attempts++;
        }
    }

    if (!client.connected())
    {
        Serial.println("✗ Não foi possível conectar ao MQTT");
        Serial.println("Verifique se o Host IP está correto!");
    }
}

// ========================================
// FUNÇÃO: loop()
// ========================================
// Executada continuamente

void loop()
{
    // ========== GARANTIR CONEXÃO MQTT ==========
    if (!client.connected())
    {
        reconnect();
    }

    // Processar mensagens MQTT recebidas (se houver subscribers)
    client.loop();

    // ========== LER SENSORES A CADA INTERVALO ==========
    unsigned long now = millis(); // Tempo decorrido em milissegundos

    // Verificar se passou o intervalo definido
    if (now - lastMsg > interval)
    {
        lastMsg = now;

        // Ler valores do DHT22
        float humidity = dht.readHumidity();       // % de umidade
        float temperature = dht.readTemperature(); // Temperatura em °C

        // ========== VALIDAR LEITURA ==========
        // isnan() verifica se o valor é "Not a Number" (erro)
        if (isnan(humidity) || isnan(temperature))
        {
            Serial.println("✗ Erro ao ler DHT22! Sensores conectados?");
            return; // Sair da função e não publicar dados inválidos
        }

        // ========== EXIBIR NO MONITOR SERIAL ==========
        Serial.println();
        Serial.print("┌─ Leitura do Sensor ─────────────────┐");
        Serial.println();
        Serial.print("│ Temperatura: ");
        Serial.print(temperature);
        Serial.println("°C");
        Serial.print("│ Umidade:     ");
        Serial.print(humidity);
        Serial.println("%");
        Serial.println("└──────────────────────────────────────┘");

        // ========== CRIAR MENSAGEM JSON ==========
        // JSON é um formato padrão para trocar dados
        // O backend Node.js espera receber dados neste formato
        String payload = "{\"temperature\": " + String(temperature) +
                         ", \"humidity\": " + String(humidity) +
                         ", \"deviceId\": \"esp32-dht22\", " +
                         "\"location\": \"sala\"}";

        Serial.print("📤 Publicando: ");
        Serial.println(payload);

        // ========== PUBLICAR NO MQTT ==========
        // Se estiver conectado, enviar a mensagem
        if (client.connected())
        {
            // client.publish(tópico, mensagem)
            bool success = client.publish(mqtt_topic, payload.c_str());

            if (success)
            {
                Serial.println("✓ Mensagem enviada com sucesso!");
            }
            else
            {
                Serial.println("✗ Erro ao enviar mensagem");
            }
        }
        else
        {
            Serial.println("✗ Não conectado ao MQTT - aguardando reconexão...");
        }
    }
}

/*
 * ========================================
 * NOTAS IMPORTANTES
 * ========================================
 *
 * 1. SUBSTITUIR "YOUR_HOST_IP":
 *    - No PowerShell: ipconfig
 *    - Procure por "Endereço IPv4"
 *    - Use o IP da sua rede local (ex: 192.168.1.100)
 *    - NÃO use "localhost" ou "127.0.0.1"
 *
 * 2. CONEXÕES DO DHT22:
 *    - VCC (5V/3.3V) → ESP32 3.3V
 *    - GND → ESP32 GND
 *    - DATA (out) → ESP32 GPIO 15 (com resistor 10kΩ para 3.3V)
 *
 * 3. MONITOR SERIAL NO WOKWI:
 *    - Abra: Ctrl+Shift+I (no Wokwi)
 *    - Veja as mensagens de debug
 *
 * 4. VALORES ESPERADOS:
 *    - Temperatura: 15°C a 35°C (depende do ambiente simulado)
 *    - Umidade: 20% a 80% (depende do ambiente simulado)
 *
 * 5. VERIFIQUE SE O PIPELINE ESTÁ RODANDO:
 *    - Grafana: http://localhost:3001
 *    - API Backend: http://localhost:3000/api/latest
 *    - Se os dados não aparecerem, verifique os logs
 */
