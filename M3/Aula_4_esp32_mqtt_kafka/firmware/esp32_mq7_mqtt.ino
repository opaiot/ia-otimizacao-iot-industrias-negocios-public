
/*
 * ESP32 + DHT22 + MQ-7 - Publicador MQTT (Aula 4)
 *
 * DHT22: temperatura e umidade (formato da Aula 3).
 * MQ-7: monoxido de carbono via ADC, mapeado para o campo co2 do pipeline.
 *
 * Componentes (Wokwi ou hardware):
 * - ESP32
 * - DHT22 no GPIO 15 (pull-up 10 kOhm)
 * - MQ-7: AOUT no GPIO 34
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <time.h>

#define DHT_PIN 15
#define DHT_TYPE DHT22
#define MQ7_AOUT_PIN 34

#define MQTT_TOPIC "opaiot/air_quality"
#define MQTT_SERVER "andromeda.lasdpc.icmc.usp.br"
#define MQTT_PORT 20202
#define SENSOR_ID "sensor-wokwi-04"
#define ROOM "lab-01"
#define PUBLISH_INTERVAL_MS 5000
#define MQ7_SAMPLE_COUNT 20
#define ADC_MAX 4095.0f
#define VREF 3.3f
#define RL_KOHM 10.0f
#define RO_CLEAN_AIR_KOHM 10.0f

// WiFi: use Wokwi-GUEST no simulador; na placa fisica, troque pelas credenciais.
const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASS = "";

// IP do host com Mosquitto. No Wokwi use o IP da sua rede, nao "localhost".

// Calibracao didatica do MQ-7. Ajuste RO_CLEAN_AIR apos aquecer o sensor em ar limpo.

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastPublishMs = 0;

void connectWiFi()
{
  Serial.printf("Conectando ao WiFi: %s\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.printf("WiFi conectado. IP: %s\n", WiFi.localIP().toString().c_str());
  }
  else
  {
    Serial.println("Falha ao conectar WiFi.");
  }
}

void syncTimeUtc()
{
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

  struct tm timeinfo;
  for (int attempt = 0; attempt < 20; attempt++)
  {
    if (getLocalTime(&timeinfo))
    {
      Serial.println("Horario UTC sincronizado via NTP.");
      return;
    }
    delay(500);
  }

  Serial.println("NTP indisponivel; timestamp sera omitido no MQTT.");
}

bool utcTimestamp(char *buffer, size_t bufferSize)
{
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo))
  {
    return false;
  }

  return strftime(buffer, bufferSize, "%Y-%m-%dT%H:%M:%SZ", &timeinfo) > 0;
}

void connectMqtt()
{
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);

  while (!mqttClient.connected())
  {
    String clientId = "esp32-air-quality-";
    clientId += String(random(0xffff), HEX);

    Serial.printf("Conectando MQTT %s:%d ... ", MQTT_SERVER, MQTT_PORT);

    if (mqttClient.connect(clientId.c_str()))
    {
      Serial.println("ok");
      return;
    }

    Serial.printf("falhou (rc=%d). Nova tentativa em 5s.\n", mqttClient.state());
    delay(5000);
  }
}

int readMq7AdcAverage()
{
  long sum = 0;

  for (int i = 0; i < MQ7_SAMPLE_COUNT; i++)
  {
    sum += analogRead(MQ7_AOUT_PIN);
    delay(20);
  }

  return static_cast<int>(sum / MQ7_SAMPLE_COUNT);
}

float adcToVoltage(int adcValue)
{
  return (static_cast<float>(adcValue) / ADC_MAX) * VREF;
}

float estimateCoPpm(int adcValue)
{
  float voltage = adcToVoltage(adcValue);
  if (voltage <= 0.01f)
  {
    return 0.0f;
  }

  float rsKohm = ((VREF - voltage) / voltage) * RL_KOHM;
  float ratio = rsKohm / RO_CLEAN_AIR_KOHM;

  float ppm = 400.0f + (ratio - 1.0f) * 700.0f;

  if (ppm < 0.0f)
  {
    ppm = 0.0f;
  }
  if (ppm > 2000.0f)
  {
    ppm = 2000.0f;
  }

  return ppm;
}

bool publishTelemetry(float temperature, float humidity, int co2)
{
  char timestamp[32];
  bool hasTimestamp = utcTimestamp(timestamp, sizeof(timestamp));

  char payload[256];
  if (hasTimestamp)
  {
    snprintf(
        payload,
        sizeof(payload),
        "{\"sensor_id\":\"%s\",\"room\":\"%s\",\"temperature\":%.2f,\"humidity\":%.2f,\"co2\":%d,\"timestamp\":\"%s\"}",
        SENSOR_ID,
        ROOM,
        temperature,
        humidity,
        co2,
        timestamp);
  }
  else
  {
    snprintf(
        payload,
        sizeof(payload),
        "{\"sensor_id\":\"%s\",\"room\":\"%s\",\"temperature\":%.2f,\"humidity\":%.2f,\"co2\":%d}",
        SENSOR_ID,
        ROOM,
        temperature,
        humidity,
        co2);
  }

  Serial.printf("Publicando em %s: %s\n", MQTT_TOPIC, payload);
  return mqttClient.publish(MQTT_TOPIC, payload, false);
}

void setup()
{
  Serial.begin(115200);
  delay(100);

  randomSeed(esp_random());

  Serial.println();
  Serial.println("ESP32 + DHT22 + MQ-7 - MQTT Aula 4");

  dht.begin();
  analogReadResolution(12);
  analogSetPinAttenuation(MQ7_AOUT_PIN, ADC_11db);

  connectWiFi();
  syncTimeUtc();
  connectMqtt();

  lastPublishMs = millis();
}

void loop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    connectWiFi();
    syncTimeUtc();
  }

  if (!mqttClient.connected())
  {
    connectMqtt();
  }

  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublishMs < PUBLISH_INTERVAL_MS)
  {
    return;
  }
  lastPublishMs = now;

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature))
  {
    Serial.println("Erro na leitura do DHT22.");
    return;
  }

  int adcValue = readMq7AdcAverage();
  float voltage = adcToVoltage(adcValue);
  float coPpm = estimateCoPpm(adcValue);
  int co2Field = static_cast<int>(coPpm + 0.5f);

  Serial.printf(
      "Leitura: temp=%.2f C, umid=%.2f %%, mq7_adc=%d, tensao=%.3f V, co=%.0f ppm\n",
      temperature,
      humidity,
      adcValue,
      voltage,
      coPpm);

  if (!publishTelemetry(temperature, humidity, co2Field))
  {
    Serial.println("Falha ao publicar no MQTT.");
  }
}
