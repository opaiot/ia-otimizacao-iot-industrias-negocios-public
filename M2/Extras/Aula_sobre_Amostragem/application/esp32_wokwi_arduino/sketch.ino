/*
 * IoT MPU6050 — ESP32 Arduino (Wokwi)
 *
 * WiFi : "Wokwi-GUEST" (rede virtual embutida no simulador)
 * MQTT : broker.emqx.io → tópico aula/opaiot/accelerometer
 * I2C  : SDA=GPIO21  SCL=GPIO22
 *
 * Fallbacks:
 *   - MQTT indisponível → imprime JSON na serial do Wokwi
 *   - MPU6050 não detectado → sinal sintético com 2 Hz, 5 Hz e 0,5 Hz
 *     (frequências conhecidas facilitam verificar a FFT no backend)
 *
 * Payload:
 *   {"ts":<ms>,"ax":<m/s²>,"ay":<m/s²>,"az":<m/s²>}
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <math.h>

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
static const char* WIFI_SSID        = "Wokwi-GUEST";
static const char* WIFI_PASS        = "";
static const char* MQTT_BROKER      = "broker.emqx.io";
static const int   MQTT_PORT        = 1883;
static const char* MQTT_TOPIC       = "aula/opaiot/accelerometer";
static const int   SAMPLE_INTERVAL  = 50;   // ms → 20 Hz

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------
WiFiClient    wifiClient;
PubSubClient  mqtt(wifiClient);
Adafruit_MPU6050 mpu;
bool mpuOk = false;

// ---------------------------------------------------------------------------
// WiFi
// ---------------------------------------------------------------------------
void wifiConnect() {
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.print("WiFi conectando");
    for (int i = 0; i < 30 && WiFi.status() != WL_CONNECTED; i++) {
        delay(500);
        Serial.print(".");
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi OK — IP: " + WiFi.localIP().toString());
    } else {
        Serial.println("\nWiFi timeout — modo serial");
    }
}

// ---------------------------------------------------------------------------
// MQTT
// ---------------------------------------------------------------------------
bool mqttConnect() {
    // Client ID único baseado no chip ID
    char clientId[32];
    snprintf(clientId, sizeof(clientId), "wokwi-%08X", (uint32_t)ESP.getEfuseMac());

    if (mqtt.connect(clientId)) {
        Serial.print("MQTT OK → ");
        Serial.println(MQTT_BROKER);
        return true;
    }
    Serial.printf("MQTT falhou (rc=%d) — serial only\n", mqtt.state());
    return false;
}

// ---------------------------------------------------------------------------
// Sinal sintético (fallback)
// ---------------------------------------------------------------------------
void simulatedAccel(unsigned long t_ms, float& ax, float& ay, float& az) {
    float t = t_ms * 0.001f;
    ax = 2.0f * sinf(2.0f * M_PI * 2.0f * t);    // 2 Hz, ±2 m/s²
    ay = 1.0f * sinf(2.0f * M_PI * 5.0f * t);    // 5 Hz, ±1 m/s²
    az = 9.81f + 0.5f * sinf(2.0f * M_PI * 0.5f * t); // ~g + 0,5 Hz
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n--- IoT MPU6050 (Arduino/Wokwi) ---");

    Wire.begin(21, 22);
    mpuOk = mpu.begin(0x68, &Wire);
    if (mpuOk) {
        mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
        mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
        Serial.println("MPU6050 detectado via I2C");
    } else {
        Serial.println("MPU6050 não encontrado — usando dados simulados");
    }

    wifiConnect();

    if (WiFi.status() == WL_CONNECTED) {
        mqtt.setServer(MQTT_BROKER, MQTT_PORT);
        mqttConnect();
    }

    Serial.println("\n--- Loop iniciado  (20 Hz) ---");
    Serial.println("Formato: {ts, ax, ay, az}  |  unidade: m/s²\n");
}

// ---------------------------------------------------------------------------
// Loop
// ---------------------------------------------------------------------------
void loop() {
    unsigned long ts = millis();
    float ax, ay, az;

    // Leitura do sensor
    if (mpuOk) {
        sensors_event_t a, g, temp;
        if (mpu.getEvent(&a, &g, &temp)) {
            ax = a.acceleration.x;
            ay = a.acceleration.y;
            az = a.acceleration.z;
        } else {
            simulatedAccel(ts, ax, ay, az);
        }
    } else {
        simulatedAccel(ts, ax, ay, az);
    }

    // Monta JSON (mesmo formato do código MicroPython)
    StaticJsonDocument<128> doc;
    doc["ts"] = ts;
    doc["ax"] = serialized(String(ax, 4));
    doc["ay"] = serialized(String(ay, 4));
    doc["az"] = serialized(String(az, 4));

    char payload[128];
    serializeJson(doc, payload);

    // Serial — sempre visível no monitor do Wokwi
    Serial.println(payload);

    // MQTT — reconecta se necessário
    if (WiFi.status() == WL_CONNECTED) {
        if (!mqtt.connected()) {
            mqttConnect();
        }
        if (mqtt.connected()) {
            mqtt.publish(MQTT_TOPIC, payload);
            mqtt.loop();
        }
    }

    delay(SAMPLE_INTERVAL);
}
