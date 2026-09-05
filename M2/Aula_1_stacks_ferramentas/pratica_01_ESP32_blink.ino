// Define o pino 18 do Arduino como a porta que vamos usar
// Aqui vamos conectar o LED que queremos piscar
int PORT = 18;

// A função setup() (configuração) é executada apenas UMA VEZ
// quando você liga o Arduino ou aperta o botão de reset
// Use essa função para inicializar (preparar) todas as configurações do seu projeto
void setup()
{
    // Serial.begin(9600) - Inicia a comunicação entre Arduino e o computador
    // 9600 é a velocidade de comunicação (baud rate)
    // Isso permite que você envie mensagens ao computador via Monitor Serial
    Serial.begin(9600);

    // pinMode() define o modo de funcionamento de um pino
    // PORT = 18 significa "use o pino 18"
    // OUTPUT significa que vamos ENVIAR sinais (ligar/desligar)
    // (Se fosse INPUT, o pino seria para RECEBER sinais, como um botão)
    pinMode(PORT, OUTPUT);
}

// A função loop() (loço/repetição) é executada continuamente
// Depois que setup() termina, Arduino executa loop() infinitamente
// Aqui colocamos o que queremos que o Arduino faça repetidamente
void loop()
{
    // digitalWrite() envia um sinal digital (on/off) para um pino
    // HIGH = 5 volts = LIGADO
    // Isso liga o LED conectado ao pino 18
    digitalWrite(PORT, HIGH);

    // Serial.println() envia uma mensagem de texto ao computador
    // A mensagem aparece no Monitor Serial da IDE Arduino
    Serial.println("LED LIGADO");

    // delay(1000) faz o Arduino ESPERAR/PAUSAR por um tempo
    // 1000 significa 1000 milissegundos = 1 segundo
    // Enquanto a pausa acontece, o LED fica ligado por 1 segundo
    delay(1000);

    // LOW = 0 volts = DESLIGADO
    // Isso desliga o LED conectado ao pino 18
    digitalWrite(PORT, LOW);

    // Envia mensagem informando que o LED foi desligado
    Serial.println("LED DESLIGADO");

    // Aguarda mais 1 segundo antes de repetir o loop
    delay(1000);

    // Depois dessa linha, a função loop() começa tudo de novo automaticamente
}
