"""
ESP32 + MPU6050 — versão Wokwi
WiFi: "Wokwi-GUEST" (sem senha, rede virtual do simulador)
MQTT: broker.emqx.io (funciona via rede do Wokwi)
Fallback: se MQTT falhar, imprime JSON na serial (monitor do Wokwi)
"""
import math
import ujson
import utime
import machine
from machine import I2C, Pin

from mpu6050 import MPU6050

# --- Config ---
WIFI_SSID = "Wokwi-GUEST"   # rede virtual embutida no Wokwi
WIFI_PASS = ""
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = b"aula/opaiot/accelerometer"
SAMPLE_INTERVAL_MS = 50      # 20 Hz


# ---------------------------------------------------------------------------
# WiFi
# ---------------------------------------------------------------------------

def wifi_connect() -> bool:
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASS)
        print("Conectando WiFi", end="")
        for _ in range(30):
            if wlan.isconnected():
                print(f"\nWiFi OK — IP: {wlan.ifconfig()[0]}")
                return True
            utime.sleep_ms(500)
            print(".", end="")
        print("\nWiFi timeout — modo serial")
        return False
    except Exception as e:
        print(f"WiFi indisponível: {e}")
        return False


# ---------------------------------------------------------------------------
# MQTT
# ---------------------------------------------------------------------------

def mqtt_connect():
    try:
        import ubinascii
        from umqtt.simple import MQTTClient
        cid = b"wokwi-" + ubinascii.hexlify(machine.unique_id())
        client = MQTTClient(cid, MQTT_BROKER, port=MQTT_PORT, keepalive=30)
        client.connect()
        print(f"MQTT OK → {MQTT_BROKER}  tópico: {MQTT_TOPIC.decode()}")
        return client
    except Exception as e:
        print(f"MQTT falhou: {e} — publicando só na serial")
        return None


def mqtt_publish(client, payload: str) -> object:
    """Publica e retorna o cliente (ou None se conexão perdida)."""
    try:
        client.publish(MQTT_TOPIC, payload)
        return client
    except Exception as e:
        print(f"MQTT erro: {e} — reconectando...")
        try:
            return mqtt_connect()
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Dados simulados (fallback se I2C falhar no simulador)
# ---------------------------------------------------------------------------

def simulated_accel(t_ms: int) -> tuple:
    """
    Sinal sintético com componentes conhecidas — ideal para verificar FFT:
      ax: 2 Hz, amplitude 2 m/s²
      ay: 5 Hz, amplitude 1 m/s²
      az: gravidade + 0,5 Hz, amplitude 0,5 m/s²
    """
    t = t_ms / 1000.0
    ax = 2.0 * math.sin(2 * math.pi * 2 * t)
    ay = 1.0 * math.sin(2 * math.pi * 5 * t)
    az = 9.81 + 0.5 * math.sin(2 * math.pi * 0.5 * t)
    return ax, ay, az


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # I2C + MPU6050
    i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
    mpu = None
    try:
        mpu = MPU6050(i2c)
        # teste de leitura
        mpu.read_accel()
        print("MPU6050 detectado via I2C")
    except Exception as e:
        print(f"MPU6050 não encontrado ({e}) — usando dados simulados")
        mpu = None

    # Rede
    online = wifi_connect()
    client = mqtt_connect() if online else None

    print("\n--- Loop iniciado ---")
    print("Formato: {ts, ax, ay, az}  |  unidade: m/s²\n")

    while True:
        ts = utime.ticks_ms()

        if mpu:
            try:
                ax, ay, az = mpu.read_accel()
            except Exception:
                ax, ay, az = simulated_accel(ts)
        else:
            ax, ay, az = simulated_accel(ts)

        payload = ujson.dumps({
            "ts": ts,
            "ax": round(ax, 4),
            "ay": round(ay, 4),
            "az": round(az, 4),
        })

        # Sempre imprime na serial do Wokwi
        print(payload)

        # MQTT se disponível
        if client:
            client = mqtt_publish(client, payload)

        utime.sleep_ms(SAMPLE_INTERVAL_MS)


main()
