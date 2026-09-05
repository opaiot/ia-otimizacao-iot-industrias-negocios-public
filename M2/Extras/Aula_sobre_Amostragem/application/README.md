# Guia de uso — IoTDataSamplingLab

Este guia explica como colocar o sistema no ar, seja com o **simulador Wokwi** (sem hardware) ou com um **ESP32 físico**, e como interpretar o que aparece no Grafana.

---

## Índice

1. [Visão geral da stack](#1-visão-geral-da-stack)
2. [Pré-requisitos](#2-pré-requisitos)
3. [Opção A — Simulador Wokwi (sem hardware)](#3-opção-a--simulador-wokwi-sem-hardware)
   - [MicroPython](#31-micropython-pasta-esp32_wokwi_micropython)
   - [Arduino (C++)](#32-arduino-c-pasta-esp32_wokwi_arduino)
4. [Opção B — ESP32 físico](#4-opção-b--esp32-físico)
5. [Iniciar a stack Docker](#5-iniciar-a-stack-docker)
6. [Acessar o Grafana](#6-acessar-o-grafana)
7. [Verificar o funcionamento](#7-verificar-o-funcionamento)
8. [Entendendo os dados](#8-entendendo-os-dados)
9. [Parâmetros configuráveis](#9-parâmetros-configuráveis)
10. [Solução de problemas](#10-solução-de-problemas)

---

## 1. Visão geral da stack

```
┌─────────────────────────┐
│  ESP32 + MPU6050        │  publica JSON via MQTT a 20 Hz
└──────────┬──────────────┘
           │  broker.emqx.io:1883
           │  tópico: aula/opaiot/accelerometer
           ▼
┌─────────────────────────┐
│  Backend Python         │  container Docker
│  (paho-mqtt + numpy)    │  ├─ accel_raw  → InfluxDB (sinal bruto)
│                         │  └─ accel_fft  → InfluxDB (espectro)
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  InfluxDB 2.7           │  container Docker  (porta 8086)
└──────────┬──────────────┘
           │  Flux queries
           ▼
┌─────────────────────────┐
│  Grafana 10.4           │  container Docker  (porta 3000)
└─────────────────────────┘
```

O ESP32 e o Grafana são os únicos pontos de interação manual. Tudo mais sobe automaticamente via Docker Compose.

---

## 2. Pré-requisitos

### Para qualquer opção

- **Docker** e **Docker Compose** instalados no computador host
- Acesso à internet (o broker MQTT é público)

### Apenas para o ESP32 físico

- Placa **ESP32** (qualquer variante com GPIO 21/22 disponíveis)
- Sensor **MPU6050** ligado via I2C:

  | Pino MPU6050 | Pino ESP32 |
  |---|---|
  | VCC | 3,3 V |
  | GND | GND |
  | SDA | GPIO 21 |
  | SCL | GPIO 22 |

- **Python 3** com `esptool` e `mpremote` instalados (para gravar firmware)

---

## 3. Opção A — Simulador Wokwi (sem hardware)

O Wokwi é um simulador online de ESP32. Não precisa de nenhum hardware.  
Acesse: **[wokwi.com](https://wokwi.com)**

O sinal simulado tem frequências conhecidas (2 Hz, 5 Hz e 0,5 Hz) que permitem validar visualmente se a FFT está correta.

### 3.1 MicroPython — pasta `esp32_wokwi_micropython/`

1. No Wokwi, crie um novo projeto **ESP32** com **MicroPython**.
2. Importe (ou copie manualmente) os arquivos:
   - `esp32_wokwi_micropython/main.py`
   - `esp32_wokwi_micropython/mpu6050.py`
   - `esp32_wokwi_micropython/diagram.json` (circuito já com MPU6050 conectado)
3. Clique em **Start Simulation**.
4. No monitor serial, você verá:

   ```
   WiFi OK — IP: 10.0.0.2
   MQTT OK → broker.emqx.io  tópico: aula/opaiot/accelerometer
   {"ts": 1234, "ax": 1.8532, "ay": 0.9876, "az": 9.8100}
   ```

> O arquivo `wokwi.toml` já habilita a integração com a extensão VS Code do Wokwi — nenhum binário de firmware precisa ser baixado manualmente.

[**Link projeto Wokwi**](https://wokwi.com/projects/464505939773171713)

### 3.2 Arduino (C++) — pasta `esp32_wokwi_arduino/`

1. No Wokwi, crie um novo projeto **ESP32** com **Arduino**.
2. Importe os arquivos:
   - `esp32_wokwi_arduino/sketch.ino`
   - `esp32_wokwi_arduino/diagram.json`
3. As bibliotecas listadas em `libraries.txt` são instaladas automaticamente pelo Wokwi:
   - `PubSubClient`
   - `ArduinoJson`
   - `Adafruit MPU6050`
   - `Adafruit Unified Sensor`
4. Clique em **Start Simulation**.

   ```
   WiFi OK — IP: 10.13.37.4
   MQTT OK → broker.emqx.io
   {"ts":2048,"ax":"1.9921","ay":"0.9511","az":"9.8100"}
   ```

[**Link projeto Wokwi**](https://wokwi.com/projects/464490620985924609)

---

## 4. Opção B — ESP32 físico

O firmware tanto em MicroPython quanto Arduino suporta hardware real. Para tanto, pode ser necessário migrar o diretório ou configurar o ambiente, seja usando a IDE do Arduino ou o VS Code. 

Observe que o firmware tenta inicializar o MPU6050 via I2C e, se não encontrar, cai automaticamente em modo de sinal simulado.

No caso do MicroPython segue um passo a passo para uso no hardware físico.

### 4.1 Gravar o firmware MicroPython

```bash
pip install esptool

# Apagar flash
esptool.py --port /dev/ttyUSB0 erase_flash

# Gravar firmware (baixe o .bin em micropython.org/download/ESP32_GENERIC)
esptool.py --port /dev/ttyUSB0 write_flash -z 0x1000 ESP32_GENERIC-<versão>.bin
```

> No Windows substitua `/dev/ttyUSB0` por `COM3` (ou a porta que aparecer no Gerenciador de Dispositivos).

### 4.2 Configurar credenciais WiFi

Edite as constantes no topo de `esp32_wokwi_micropython/main.py`:

```python
WIFI_SSID = "Nome_da_sua_rede"
WIFI_PASS = "senha_da_rede"
```

Os demais parâmetros (broker, tópico, pinos, taxa de amostragem) já estão configurados e não precisam ser alterados.

### 4.3 Enviar arquivos para o ESP32

```bash
pip install mpremote

mpremote connect /dev/ttyUSB0 cp esp32_wokwi_micropython/mpu6050.py :mpu6050.py
mpremote connect /dev/ttyUSB0 cp esp32_wokwi_micropython/main.py    :main.py
```

### 4.4 Monitorar a saída serial

```bash
mpremote connect /dev/ttyUSB0
```

Saída esperada após boot:

```
WiFi OK — IP: 192.168.1.42
MQTT OK → broker.emqx.io  tópico: aula/opaiot/accelerometer
MPU6050 detectado via I2C
{"ts": 312, "ax": 0.0241, "ay": -0.0118, "az": 9.8053}
```

> Se o MPU6050 não for detectado, o firmware entra em modo de sinal simulado automaticamente — o sistema continua funcionando e os dados chegam ao backend normalmente.

---

## 5. Iniciar a stack Docker

Com o ESP32 (físico ou simulado) já publicando mensagens:

```bash
cd application/
docker compose up --build
```

Na primeira execução, o Docker baixa as imagens e constrói o backend (~2 min).  
Nas execuções seguintes, use `docker compose up` (sem `--build`).

Aguarde até ver no terminal:

```
iot_backend  | InfluxDB ready
iot_backend  | MQTT connected to broker.emqx.io
iot_backend  | Subscribed to aula/opaiot/accelerometer
```

Para rodar em segundo plano:

```bash
docker compose up -d
docker compose logs -f backend   # acompanhar logs do backend
```

Para encerrar:

```bash
docker compose down
```

---

## 6. Acessar o Grafana

| Serviço | URL | Login |
|---|---|---|
| **Grafana** | http://localhost:3000 | `admin` / `admin` |
| InfluxDB | http://localhost:8086 | `admin` / `adminpass123` |

No Grafana, o dashboard **"MPU6050 IoT — Acelerômetro"** é provisionado automaticamente. Ele aparece em **Dashboards → Browse**.

---

## 7. Verificar o funcionamento

### 7.1 Backend recebendo mensagens

```bash
docker compose logs -f backend
```

Logs esperados (um por amostra + FFT a cada 256 amostras):

```
INFO  MQTT connected to broker.emqx.io
INFO  Subscribed to aula/opaiot/accelerometer
INFO  sample #1   ax=1.953 ay=0.951 az=9.810
INFO  sample #2   ax=1.618 ay=0.588 az=9.810
...
INFO  FFT written — 129 points for 3 axes   ← aparece a cada ~12,8 s
```

### 7.2 Testar o tópico MQTT diretamente (opcional)

Use o **MQTTX** (app ou web em [mqttx.app](https://mqttx.app)):

- Broker: `broker.emqx.io` · porta `1883`
- Subscribe: `aula/opaiot/accelerometer`

Payload esperado:
```json
{"ts": 12345, "ax": 1.9532, "ay": 0.9511, "az": 9.8100}
```

### 7.3 Consultar dados no InfluxDB

Acesse http://localhost:8086 → **Data Explorer** e execute:

```flux
from(bucket: "iot_data")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "accel_raw")
  |> limit(n: 5)
```

---

## 8. Entendendo os dados

### Dashboard — painel superior: Aceleração em tempo real

Mostra `ax`, `ay` e `az` em m/s² com auto-refresh de 5 s.  
Útil para ver o sinal bruto e confirmar que a leitura está chegando.

### Dashboard — painéis inferiores: Espectro FFT

Cada painel mostra o **espectro de magnitude** do último janelamento para um eixo.

| Conceito | Explicação |
|---|---|
| **Janela FFT** | 256 amostras coletadas antes de calcular o espectro |
| **Frequência de amostragem** | 20 Hz → período de 50 ms por amostra |
| **Duração da janela** | 256 × 50 ms = **12,8 segundos** de sinal |
| **Resolução espectral** | 20 Hz ÷ 256 = **0,078 Hz por bin** |
| **Frequência máxima** | 20 Hz ÷ 2 = **10 Hz** (Nyquist) |
| **Janela de Hann** | Aplicada antes da FFT para reduzir vazamento espectral |
| **Normalização** | Magnitude dividida por N/2 → valores em m/s² |

O espectro é atualizado a cada 256 novas amostras (~12,8 s). No sinal simulado, picos nítidos devem aparecer em:

| Eixo | Frequência esperada |
|---|---|
| ax | **2 Hz** |
| ay | **5 Hz** |
| az | **0,5 Hz** |

### Measurements no InfluxDB

| Measurement | Campos | Tags | Descrição |
|---|---|---|---|
| `accel_raw` | `ax`, `ay`, `az`, `esp_ts_ms` | `source=esp32` | Uma linha por amostra recebida |
| `accel_fft` | `magnitude` | `axis`, `freq_bin`, `freq_hz` | Uma linha por bin espectral por janela |

---

## 9. Parâmetros configuráveis

Edite as variáveis de ambiente no `docker-compose.yml` (seção `backend → environment`):

| Variável | Padrão | Descrição |
|---|---|---|
| `MQTT_BROKER` | `broker.emqx.io` | Endereço do broker MQTT |
| `MQTT_PORT` | `1883` | Porta MQTT |
| `MQTT_TOPIC` | `aula/opaiot/accelerometer` | Tópico subscrito |
| `WINDOW_SIZE` | `256` | Número de amostras por janela FFT |
| `SAMPLE_RATE` | `20.0` | Taxa de amostragem declarada (Hz) |

Após editar, aplique com:

```bash
docker compose up -d --no-deps backend
```

---

## 10. Solução de problemas

### Backend não recebe mensagens

```bash
docker compose logs backend | grep -E "MQTT|error"
```

Causas comuns:
- ESP32 publicando em tópico diferente (verifique `MQTT_TOPIC` no firmware e no `docker-compose.yml`)
- Broker inacessível (teste conexão com MQTTX)

### Grafana mostra "No data"

1. Confirme que o backend está rodando: `docker compose ps`
2. Verifique se há dados no InfluxDB (seção 7.3)
3. Certifique-se de que o espectro FFT já foi calculado (aparece no log após 256 amostras)
4. Recarregue o dashboard: botão de refresh ou `docker compose restart grafana`

### ESP32 não conecta no WiFi

- Para o **Wokwi**: a rede é sempre `Wokwi-GUEST` sem senha — não altere.
- Para o **ESP32 físico**: verifique `WIFI_SSID` e `WIFI_PASS` no topo de `esp32_wokwi_micropython/main.py`.

### Reiniciar um serviço específico

```bash
docker compose restart backend    # só o backend
docker compose restart grafana    # só o grafana
docker compose restart influxdb   # só o InfluxDB
```

### Apagar todos os dados e recomeçar

```bash
docker compose down -v    # remove containers e volumes (dados do InfluxDB)
docker compose up --build
```
