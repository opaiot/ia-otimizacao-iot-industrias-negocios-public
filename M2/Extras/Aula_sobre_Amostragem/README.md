# Material Extra sobre Amostragem e Conversão A/D

Material didático sobre **amostragem, aquisição e tratamento de dados em IoT**. O projeto demonstra o ciclo completo de um sistema de sensoriamento: leitura de um acelerômetro num microcontrolador, transmissão via MQTT, processamento no servidor (FFT), armazenamento em série temporal e visualização em tempo real.

---

## Objetivo pedagógico

O laboratório foi concebido para responder, de forma prática, às seguintes perguntas:

| Pergunta | Conceito explorado |
|---|---|
| Com que frequência devo amostrar? | Taxa de amostragem e Teorema de Nyquist |
| Que informação está escondida no sinal? | Análise espectral via FFT |
| Como transmitir dados de IoT de forma eficiente? | Protocolo MQTT e payload JSON |
| Como armazenar e consultar séries temporais? | InfluxDB com linguagem Flux |
| Como visualizar dados em tempo real? | Grafana com auto-refresh |

---

## Arquitetura geral

```
┌──────────────────────────────┐
│  ESP32 + MPU6050             │  Lê ax, ay, az a 20 Hz
│  (físico ou simulado Wokwi)  │  Payload: {"ts", "ax", "ay", "az"}
└──────────────┬───────────────┘
               │ MQTT  (broker.emqx.io : 1883)
               │ tópico: aula/opaiot/accelerometer
               ▼
┌──────────────────────────────┐
│  Backend Python              │  Subscreve o tópico MQTT
│                              │  ├─ grava accel_raw  → InfluxDB
│                              │  └─ calcula FFT (Hann, 256 pts)
│                              │     e grava accel_fft → InfluxDB
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  InfluxDB 2.7                │  Série temporal com Flux queries
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Grafana 10.4                │  · Aceleração em tempo real
│  localhost:3000              │  · Espectro FFT por eixo (bar chart)
└──────────────────────────────┘
```

---

## Catálogo do repositório

```
IoTDataSamplingLab/
│
├── README.md                        ← este arquivo
│
├── adc_didatico.ipynb               ← notebook Jupyter com teoria de ADC,
│                                       quantização e FFT (estude antes de rodar)
│
└── application/                     ← sistema completo pronto para executar
    ├── README.md                    ← guia de uso passo a passo
    ├── docker-compose.yml           ← sobe Backend + InfluxDB + Grafana
    │
    ├── esp32_wokwi_micropython/     ← firmware MicroPython para simulador Wokwi
    │   ├── main.py                     loop principal: sensor I2C ou sinal simulado
    │   ├── mpu6050.py                  driver I2C do acelerômetro MPU6050
    │   ├── diagram.json                circuito do simulador (ESP32 + MPU6050)
    │   └── wokwi.toml                  configuração do projeto Wokwi
    │
    ├── esp32_wokwi_arduino/         ← firmware Arduino (C++) para simulador Wokwi
    │   ├── sketch.ino                  equivalente ao MicroPython em C++
    │   ├── libraries.txt               dependências (PubSubClient, ArduinoJson…)
    │   └── diagram.json                mesmo circuito do simulador
    │
    ├── backend/                     ← serviço Python (subscriber MQTT + FFT)
    │   ├── main.py                     lógica principal
    │   ├── requirements.txt            dependências Python
    │   └── Dockerfile                  imagem Docker
    │
    └── grafana/
        └── provisioning/
            ├── datasources/
            │   └── influxdb.yaml    ← datasource InfluxDB (auto-provisionado)
            └── dashboards/
                ├── dashboard.yaml   ← provisionador de dashboards
                └── mpu6050.json     ← dashboard "MPU6050 IoT — Acelerômetro"
```

> **ESP32 físico:** o firmware `esp32_wokwi_micropython/main.py` funciona também em hardware real. Basta ajustar `WIFI_SSID` e `WIFI_PASS` no topo do arquivo e enviar os arquivos com `mpremote`. Consulte o guia em `application/README.md`.

---

## Parâmetros de referência rápida

| Parâmetro | Valor |
|---|---|
| Sensor | MPU6050 — acelerômetro 3 eixos, I2C `0x68` |
| Pinos I2C (ESP32) | SDA → GPIO 21 · SCL → GPIO 22 |
| Faixa de medição | ±2 g → convertido para m/s² |
| Taxa de amostragem | **20 Hz** (50 ms entre amostras) |
| Broker MQTT | `broker.emqx.io` porta `1883` |
| Tópico MQTT | `aula/opaiot/accelerometer` |
| Payload | `{"ts":<ms>, "ax":<m/s²>, "ay":<m/s²>, "az":<m/s²>}` |
| Janela FFT | **256 amostras** ≈ 12,8 s de sinal |
| Resolução espectral | 20 / 256 ≈ **0,078 Hz por bin** |
| Frequência máxima (Nyquist) | **10 Hz** |
| Janelamento | Hann — reduz vazamento espectral |
| Measurements InfluxDB | `accel_raw` (sinal bruto) · `accel_fft` (espectro) |
| Grafana | `http://localhost:3000` · login `admin / admin` |

---

## Sinal simulado (fallback sem sensor físico)

Quando o MPU6050 não é detectado via I2C, o firmware gera um sinal sintético com frequências conhecidas — ideal para validar toda a cadeia sem hardware:

| Eixo | Frequência dominante | Amplitude |
|---|---|---|
| ax | **2 Hz** | ±2 m/s² |
| ay | **5 Hz** | ±1 m/s² |
| az | **0,5 Hz** | ±0,5 m/s² (sobre 9,81) |

Os picos devem aparecer claramente nos espectros do Grafana, confirmando que amostragem → MQTT → FFT → banco → visualização funcionam corretamente.

---

## Por onde começar

| Perfil | Caminho sugerido |
|---|---|
| Quero entender a teoria primeiro | Abra `adc_didatico.ipynb` |
| Quero rodar sem hardware | `application/README.md` → seção **Wokwi** |
| Tenho um ESP32 e MPU6050 | `application/README.md` → seção **ESP32 físico** |
