// ESP32 + MQTT sobre TLS + HMAC-SHA256
//
// Camadas de segurança:
//   1. TLS (porta 8883)             -> criptografia do transporte
//   2. usuário/senha MQTT           -> autenticação no broker
//   3. HMAC-SHA256 (chave partilhada com o subscriber, nunca com o broker)
//                                   -> integridade e autenticidade dos dados
//
// Bibliotecas necessárias (Arduino IDE > Library Manager):
//   - PubSubClient (Nick O'Leary)
// mbedtls/md.h já faz parte do core do ESP32 (Espressif), não precisa instalar.

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "mbedtls/md.h"

#include "secrets.h"
#include "ca_cert.h"

WiFiClientSecure secureClient;
PubSubClient mqttClient(secureClient);

uint32_t seqNumber = 0;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Wi-Fi conectado, IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  while (!mqttClient.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    String clientId = String(DEVICE_ID) + "-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
      Serial.println(" conectado.");
    } else {
      Serial.print(" falhou, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" - tentando novamente em 3s");
      delay(3000);
    }
  }
}

static uint8_t hexNibble(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return 0;
}

size_t hexKeyToBytes(const char *hex, uint8_t *out, size_t maxLen) {
  size_t len = strlen(hex) / 2;
  if (len > maxLen) len = maxLen;
  for (size_t i = 0; i < len; i++) {
    out[i] = (hexNibble(hex[i * 2]) << 4) | hexNibble(hex[i * 2 + 1]);
  }
  return len;
}

void hmacSha256Hex(const String &message, const uint8_t *key, size_t keyLen, char *outHex) {
  uint8_t digest[32];
  mbedtls_md_context_t ctx;
  const mbedtls_md_info_t *info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);

  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, info, 1);
  mbedtls_md_hmac_starts(&ctx, key, keyLen);
  mbedtls_md_hmac_update(&ctx, (const unsigned char *)message.c_str(), message.length());
  mbedtls_md_hmac_finish(&ctx, digest);
  mbedtls_md_free(&ctx);

  for (int i = 0; i < 32; i++) {
    sprintf(outHex + (i * 2), "%02x", digest[i]);
  }
  outHex[64] = '\0';
}

float readSimulatedTemperature() {
  // Substitua por leitura real de um sensor (DHT22, DS18B20, etc.)
  float base = 25.0;
  float noise = (random(-100, 100) / 100.0);
  return base + noise;
}

void setup() {
  Serial.begin(115200);
  randomSeed(esp_random());

  connectWiFi();

  secureClient.setCACert(CA_CERT);

  connectMQTT();
}

void loop() {
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  seqNumber++;
  float temperature = readSimulatedTemperature();

  char tempStr[8];
  snprintf(tempStr, sizeof(tempStr), "%.2f", temperature);

  uint8_t hmacKey[32];
  size_t keyLen = hexKeyToBytes(HMAC_KEY_HEX, hmacKey, sizeof(hmacKey));

  String signingMessage = String(DEVICE_ID) + "|" + String(seqNumber) + "|" + String(tempStr);

  char hmacHexStr[65];
  hmacSha256Hex(signingMessage, hmacKey, keyLen, hmacHexStr);

  char payload[256];
  snprintf(payload, sizeof(payload),
           "{\"device\":\"%s\",\"seq\":%lu,\"temp\":\"%s\",\"hmac\":\"%s\"}",
           DEVICE_ID, (unsigned long)seqNumber, tempStr, hmacHexStr);

  Serial.print("Publicando: ");
  Serial.println(payload);

  mqttClient.publish(MQTT_TOPIC, payload);

  delay(5000);
}
