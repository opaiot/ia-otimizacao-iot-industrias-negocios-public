// ======================================================
// Prática 1 — ESP32 com Potenciômetro
//
// Objetivo:
// - Ler um sinal analógico com o ADC do ESP32
// - Exibir o valor bruto da leitura
// - Converter aproximadamente para tensão
//
// Sugestão de conexão:
// - Terminal 1 do potenciômetro -> 3.3V
// - Terminal 2, central       -> GPIO34
// - Terminal 3 do potenciômetro -> GND
//
// Observação:
// - GPIO34 é apenas entrada e possui ADC.
// ======================================================

#define POT_PIN 34

const float ADC_MAX = 4095.0;   // resolução padrão de 12 bits no ESP32
const float VREF = 3.3;         // tensão máxima esperada no pino

void setup() {
  Serial.begin(115200);

  // Configura a resolução do ADC para 12 bits: valores de 0 a 4095
  analogReadResolution(12);

  // Configura a atenuação para permitir leitura próxima de 0 a 3.3 V
  analogSetPinAttenuation(POT_PIN, ADC_11db);

  Serial.println("Pratica 3 — Leitura de potenciometro com ESP32");
  Serial.println("POT -> GPIO34");
  Serial.println("----------------------------------------------");
}

void loop() {
  int adcValue = analogRead(POT_PIN);

  float voltage = (adcValue / ADC_MAX) * VREF;

  Serial.print("ADC: ");
  Serial.print(adcValue);

  Serial.print(" | Tensao aproximada: ");
  Serial.print(voltage, 2);
  Serial.println(" V");

  delay(300);
}