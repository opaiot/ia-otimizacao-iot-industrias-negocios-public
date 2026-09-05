// ======================================================
// Prática 1 — ESP32, DHT22 e MQTTX
//
// Objetivo:
// - Conectar o ESP32 à rede WiFi do Wokwi
// - Ler temperatura e umidade usando o sensor DHT22
// - Montar uma mensagem em formato JSON
// - Publicar os dados em um tópico MQTT
// - Visualizar as mensagens no MQTTX Web Client
//
// Broker MQTT:
// - broker.emqx.io
//
// Tópico MQTT:
// - opaiot-dht-1
//
// Sugestão de conexão:
// - DHT22 VCC  -> 3.3V
// - DHT22 GND  -> GND
// - DHT22 SDA  -> GPIO15
//
// Bibliotecas necessárias no Wokwi:
// - PubSubClient
// - DHT sensor library
// - Adafruit Unified Sensor
//
// Observação:
// - O ESP32 publica uma nova mensagem somente quando há mudança
//   nos valores lidos de temperatura ou umidade.
// ======================================================
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// WiFi
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// MQTT
const char* MQTT_CLIENT_ID = "opaiot-device";
const char* MQTT_BROKER = "broker.emqx.io";
const int MQTT_PORT = 1883;
const char* MQTT_USER = "";
const char* MQTT_PASSWORD = "";
const char* MQTT_TOPIC = "aula/opaiot/termo-higrometro";

// DHT22
#define DHT_PIN 15
#define DHT_TYPE DHT22

DHT sensor(DHT_PIN, DHT_TYPE);

WiFiClient espClient;
PubSubClient client(espClient);

String prevWeather = "";

void connectWiFi() {
  Serial.print("Connecting to WiFi");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(100);
  }

  Serial.println(" Connected!");
}

void connectMQTT() {
  Serial.print("Connecting to MQTT server... ");

  while (!client.connected()) {
    if (client.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("Connected!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 2 seconds");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  sensor.begin();

  connectWiFi();

  client.setServer(MQTT_BROKER, MQTT_PORT);

  connectMQTT();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();

  Serial.print("Measuring weather conditions... ");

  float temperature = sensor.readTemperature();
  float humidity = sensor.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Error reading DHT22 sensor");
    delay(1000);
    return;
  }

  String message = "{";
  message += "\"temperature\":";
  message += String(temperature, 1);
  message += ",";
  message += "\"humidity\":";
  message += String(humidity, 1);
  message += "}";

  if (message != prevWeather) {
    Serial.println("Updated!");
    Serial.print("Reporting to MQTT topic ");
    Serial.print(MQTT_TOPIC);
    Serial.print(": ");
    Serial.println(message);

    client.publish(MQTT_TOPIC, message.c_str());

    prevWeather = message;
  } else {
    Serial.println("No change");
  }

  delay(1000);
}