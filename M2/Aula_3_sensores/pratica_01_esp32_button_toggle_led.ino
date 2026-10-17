// ======================================================
// Prática 1 — ESP32, botão e LED
// Botão como interruptor digital com pull-up
//
// 1º clique -> LED acende
// 2º clique -> LED apaga
// 3º clique -> LED acende
// ...
//
// Ligação:
// - Botão em GPIO14
// - LED em GPIO2
// - Botão com pull-up:
//     solto       = HIGH
//     pressionado = LOW
// ======================================================

#define BUTTON_PIN 14
#define LED_PIN 2

bool ledState = false;

// Última leitura bruta do botão
int lastRawReading = HIGH;

// Estado estável aceito após debounce
int stableButtonState = HIGH;

// Controle de tempo do debounce
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50; // ms

void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);

  // Usa pull-up interno.
  // Com resistor externo de 10 kΩ para 3.3V, também funcionaria com INPUT.
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  digitalWrite(LED_PIN, ledState);

  Serial.println("Pratica 1 — Botao como interruptor digital");
}

void loop() {
  int rawReading = digitalRead(BUTTON_PIN);

  // Se a leitura bruta mudou, reinicia a contagem do debounce
  if (rawReading != lastRawReading) {
    lastDebounceTime = millis();
  }

  // Se a leitura permaneceu estável pelo tempo definido
  if ((millis() - lastDebounceTime) > debounceDelay) {

    // Se o estado estável mudou, atualiza
    if (rawReading != stableButtonState) {
      stableButtonState = rawReading;

      // Com pull-up:
      // HIGH = solto
      // LOW  = pressionado
      //
      // Detectamos apenas o evento de pressionamento.
      if (stableButtonState == LOW) {
        ledState = !ledState;
        digitalWrite(LED_PIN, ledState);

        Serial.print("Clique detectado. LED = ");
        Serial.println(ledState ? "ON" : "OFF");
      }
    }
  }

  lastRawReading = rawReading;
}