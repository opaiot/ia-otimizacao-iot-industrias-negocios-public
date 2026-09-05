// ======================================================
// Prática 2 — ESP32 com Encoder Rotativo
//
// Conexões:
// - CLK -> GPIO32
// - DT  -> GPIO33
// - SW  -> GPIO25
//
// Objetivo:
// - Ler a posição relativa do encoder
// - Identificar o sentido de rotação
// - Ler o botão SW do encoder
// ======================================================

#define ENCODER_CLK 32
#define ENCODER_DT  33
#define ENCODER_SW  25

int position = 0;

int lastCLKState = HIGH;

// Controle de debounce do botão SW
int lastRawButtonState = HIGH;
int stableButtonState = HIGH;
unsigned long lastButtonDebounceTime = 0;
const unsigned long buttonDebounceDelay = 50; // ms

void setup() {
  Serial.begin(115200);

  pinMode(ENCODER_CLK, INPUT_PULLUP);
  pinMode(ENCODER_DT, INPUT_PULLUP);
  pinMode(ENCODER_SW, INPUT_PULLUP);

  lastCLKState = digitalRead(ENCODER_CLK);

  Serial.println("Pratica 2 — Encoder Rotativo com ESP32");
  Serial.println("CLK -> GPIO32 | DT -> GPIO33 | SW -> GPIO25");
  Serial.println("----------------------------------------");
}

void loop() {
  readEncoder();
  readButton();
}

// ======================================================
// Leitura do encoder
// ======================================================
void readEncoder() {
  int currentCLKState = digitalRead(ENCODER_CLK);

  // Detecta mudança no canal CLK
  if (currentCLKState != lastCLKState) {

    // Considera apenas uma borda para evitar dupla contagem.
    // Aqui usamos a borda de descida: HIGH -> LOW.
    if (lastCLKState == HIGH && currentCLKState == LOW) {

      int dtState = digitalRead(ENCODER_DT);

      if (dtState == HIGH) {
        position++;
        Serial.print("Sentido: horario");
      } else {
        position--;
        Serial.print("Sentido: anti-horario");
      }

      Serial.print(" | Posicao: ");
      Serial.println(position);
    }

    lastCLKState = currentCLKState;
  }
}

// ======================================================
// Leitura do botão SW do encoder
// ======================================================
void readButton() {
  int rawButtonState = digitalRead(ENCODER_SW);

  if (rawButtonState != lastRawButtonState) {
    lastButtonDebounceTime = millis();
  }

  if ((millis() - lastButtonDebounceTime) > buttonDebounceDelay) {
    if (rawButtonState != stableButtonState) {
      stableButtonState = rawButtonState;

      // Com INPUT_PULLUP:
      // HIGH = solto
      // LOW  = pressionado
      if (stableButtonState == LOW) {
        Serial.println("Botao SW pressionado");
      }
    }
  }

  lastRawButtonState = rawButtonState;
}