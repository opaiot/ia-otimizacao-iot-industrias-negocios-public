// ======================================================
// Prática 2 — ESP32 com NTC e Steinhart-Hart
//
// Conexão sugerida:
//
// 3.3V --- Resistor fixo 10k --- GPIO34 --- NTC --- GND
//
// O GPIO34 lê o ponto médio do divisor de tensão.
//
// Objetivo:
// - Ler o ADC
// - Estimar a tensão no divisor
// - Calcular a resistência do NTC
// - Calcular a temperatura usando Steinhart-Hart
// ======================================================

#define NTC_PIN 34

const float VCC = 3.3;
const float ADC_MAX = 4095.0;

// Resistor fixo do divisor
const float R_FIXED = 10000.0; // 10 kΩ

// Coeficientes Steinhart-Hart para um NTC 10k típico.
// Esses coeficientes podem variar conforme o modelo real do sensor.
const float A = 1.009249522e-03;
const float B = 2.378405444e-04;
const float C = 2.019202697e-07;

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetPinAttenuation(NTC_PIN, ADC_11db);

  Serial.println("Pratica 4 — NTC com Steinhart-Hart");
  Serial.println("Circuito: 3.3V -- 10k -- GPIO34 -- NTC -- GND");
  Serial.println("------------------------------------------------");
}

void loop() {
  int adcValue = analogRead(NTC_PIN);

  float voltage = (adcValue / ADC_MAX) * VCC;

  // Evita divisão por zero ou valores inválidos
  if (voltage <= 0.0 || voltage >= VCC) {
    Serial.println("Leitura fora da faixa valida.");
    delay(500);
    return;
  }

  // Para o circuito:
  // 3.3V --- R_FIXED --- GPIO34 --- NTC --- GND
  //
  // Vout = VCC * R_NTC / (R_FIXED + R_NTC)
  // R_NTC = R_FIXED * Vout / (VCC - Vout)
  float resistanceNTC = R_FIXED * voltage / (VCC - voltage);

  float lnR = log(resistanceNTC);

  // Steinhart-Hart:
  // 1/T = A + B ln(R) + C (ln(R))^3
  float temperatureK = 1.0 / (A + B * lnR + C * pow(lnR, 3));

  float temperatureC = temperatureK - 273.15;
  
  // Modelo NTC segundo documentação do componente simulado
  // float celsius = 1 / (log(1 / (1023. / adcValue - 1)) / BETA + 1.0 / 298.15) - 273.15;

  Serial.print("ADC: ");
  Serial.print(adcValue);

  Serial.print(" | Vout: ");
  Serial.print(voltage, 3);
  Serial.print(" V");

  Serial.print(" | R_NTC: ");
  Serial.print(resistanceNTC, 1);
  Serial.print(" ohms");

  Serial.print(" | Temperatura: ");
  Serial.print(temperatureC, 2);
  Serial.println(" °C");

  delay(500);
}