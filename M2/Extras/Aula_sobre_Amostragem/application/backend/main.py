import json
import logging
import os
import time
from collections import deque
from datetime import datetime, timezone

import numpy as np
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# --- Config from environment ---
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "aula/opaiot/accelerometer")

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "myinfluxtoken")
INFLUX_ORG = os.getenv("INFLUX_ORG", "iot_org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "iot_data")

WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 256))  # samples for FFT (~12.8 s at 20 Hz)
SAMPLE_RATE = float(os.getenv("SAMPLE_RATE", 20.0))  # Hz

# Temporário: escreve espectro sintético para validar o Grafana
SYNTHETIC_FFT = False

AXES = ("ax", "ay", "az")

# --- State ---
buffers: dict[str, deque] = {ax: deque(maxlen=WINDOW_SIZE) for ax in AXES}
_sample_count = 0

# --- InfluxDB ---
influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx.write_api(write_options=SYNCHRONOUS)

hann_window = np.hanning(WINDOW_SIZE)
freqs = np.fft.rfftfreq(WINDOW_SIZE, d=1.0 / SAMPLE_RATE)


def write_raw(payload: dict):
    # ESP32 millis() is relative to boot, not a Unix timestamp.
    # Use server time for InfluxDB; store esp_ts_ms as a field for latency analysis.
    ts = datetime.now(tz=timezone.utc)
    point = (
        Point("accel_raw")
        .tag("source", "esp32")
        .field("ax", float(payload["ax"]))
        .field("ay", float(payload["ay"]))
        .field("az", float(payload["az"]))
        .field("esp_ts_ms", int(payload.get("ts", 0)))
        .time(ts, WritePrecision.MS)
    )
    write_api.write(bucket=INFLUX_BUCKET, record=point)


def _synthetic_spectrum(axis: str) -> np.ndarray:
    """Espectro sintético com picos gaussianos nas frequências do sinal simulado."""
    peak_hz = {"ax": 2.0, "ay": 5.0, "az": 0.5}
    mag = np.zeros(len(freqs))
    fc = peak_hz[axis]
    mag += 2.0 * np.exp(-((freqs - fc) ** 2) / (2 * 0.15 ** 2))   # pico principal
    mag += 0.3 * np.exp(-((freqs - fc * 2) ** 2) / (2 * 0.2 ** 2)) # 2° harmônico
    mag += 0.05 * np.random.default_rng().random(len(freqs))        # ruído de fundo
    return mag


def compute_and_write_fft(now: datetime):
    points = []
    for axis in AXES:
        if SYNTHETIC_FFT:
            mag = _synthetic_spectrum(axis)
        else:
            signal = np.array(buffers[axis], dtype=np.float64)
            signal -= signal.mean()
            signal *= hann_window
            mag = np.abs(np.fft.rfft(signal)) / (WINDOW_SIZE / 2)

        for i, (f, m) in enumerate(zip(freqs, mag)):
            points.append(
                Point("accel_fft")
                .tag("axis", axis)
                .tag("freq_bin", f"{i:03d}")
                .tag("freq_hz", f"{f:.3f}")
                .field("magnitude", float(m))
                .time(now, WritePrecision.MS)
            )

    write_api.write(bucket=INFLUX_BUCKET, record=points)
    log.info("FFT written — %d points for 3 axes", len(freqs))


def on_message(_client, _userdata, msg):
    global _sample_count
    try:
        payload = json.loads(msg.payload)
    except json.JSONDecodeError as e:
        log.warning("Bad JSON: %s", e)
        return

    try:
        write_raw(payload)
    except Exception as e:
        log.error("InfluxDB write_raw error: %s", e)
        return

    for axis in AXES:
        buffers[axis].append(float(payload[axis]))

    _sample_count += 1
    fft_ready = SYNTHETIC_FFT or len(buffers["ax"]) == WINDOW_SIZE
    if _sample_count % WINDOW_SIZE == 0 and fft_ready:
        try:
            compute_and_write_fft(datetime.now(tz=timezone.utc))
        except Exception as e:
            log.error("FFT write error: %s", e, exc_info=True)

    log.info("sample #%d  ax=%.3f ay=%.3f az=%.3f", _sample_count, payload["ax"], payload["ay"], payload["az"])


def on_connect(client, _userdata, _flags, rc):
    if rc == 0:
        log.info("MQTT connected to %s", MQTT_BROKER)
        client.subscribe(MQTT_TOPIC)
        log.info("Subscribed to %s", MQTT_TOPIC)
    else:
        log.error("MQTT connect failed, rc=%d", rc)


def on_disconnect(_client, _userdata, rc):
    if rc != 0:
        log.warning("Unexpected MQTT disconnect, rc=%d — will reconnect", rc)


def main():
    # Wait for InfluxDB to be ready
    for attempt in range(20):
        try:
            influx.ping()
            log.info("InfluxDB ready")
            break
        except Exception:
            log.info("Waiting for InfluxDB... (%d/20)", attempt + 1)
            time.sleep(3)
    else:
        raise RuntimeError("InfluxDB not reachable after retries")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    log.info("Starting MQTT loop")
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()
