import hashlib
import hmac
import json
import os
import queue
import ssl
import threading
import time

import paho.mqtt.client as mqtt
from flask import Flask, Response, jsonify, request, send_file

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", "8883"))
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]
HMAC_KEY = bytes.fromhex(os.environ["HMAC_KEY_HEX"])
SENSOR_TOPIC = os.environ.get("SENSOR_TOPIC", "sensors/#")
CONTROL_TOPIC = os.environ.get("ATTACKER_CONTROL_TOPIC", "control/attacker")
STATUS_TOPIC = CONTROL_TOPIC + "/status"
HTTP_PORT = int(os.environ.get("HTTP_PORT", "8080"))

CA_CERT_PATH = "/certs/ca.crt"

app = Flask(__name__, static_folder=None)

# Como o dashboard é um monitor confiável (igual ao subscriber), ele conhece a
# chave HMAC e refaz a mesma validação, incluindo o bloqueio de replay por
# número de sequência. O rótulo de cada evento (adulteração/forjada/replay) é
# apenas cosmético, inferido do campo x_attacker injetado pelo agente malicioso
# - a aceitação/rejeição em si vem sempre da verificação criptográfica real.
last_seq_by_device = {}
_state_lock = threading.Lock()
attacker_active = False

subscribers = []
_subs_lock = threading.Lock()


def broadcast(event):
    data = json.dumps(event)
    with _subs_lock:
        for q in list(subscribers):
            try:
                q.put_nowait(data)
            except queue.Full:
                pass


def sign(device, seq, temp):
    message = f"{device}|{seq}|{temp}".encode()
    return hmac.new(HMAC_KEY, message, hashlib.sha256).hexdigest()


def classify(payload_bytes):
    try:
        data = json.loads(payload_bytes.decode())
        device = data["device"]
        seq = data["seq"]
        temp = data["temp"]
        received = data["hmac"]
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
        return {
            "status": "DESCARTADA",
            "reason": "payload malformado",
            "device": None,
            "seq": None,
            "temp": None,
            "attack": False,
            "attackKind": None,
        }

    marker = data.get("x_attacker")
    hmac_ok = hmac.compare_digest(received, sign(device, seq, temp))
    result = {"device": device, "seq": seq, "temp": temp}

    if not hmac_ok:
        if marker == "tamper":
            result.update(status="REJEITADA", reason="Adulteração — HMAC não confere",
                          attack=True, attackKind="tamper")
        elif marker == "forged":
            result.update(status="REJEITADA", reason="Forjada — assinatura inválida",
                          attack=True, attackKind="forged")
        else:
            result.update(status="REJEITADA", reason="HMAC inválido",
                          attack=True, attackKind="tamper")
        return result

    try:
        seq_int = int(seq)
    except (TypeError, ValueError):
        seq_int = None

    if seq_int is not None:
        with _state_lock:
            last = last_seq_by_device.get(device)
            if last is not None and seq_int <= last:
                result.update(status="REJEITADA",
                              reason=f"Replay / fora de ordem (último aceito: {last})",
                              attack=True, attackKind="replay")
                return result
            last_seq_by_device[device] = seq_int

    result.update(status="VALIDA", reason="OK", attack=False, attackKind=None)
    return result


def on_connect(client, userdata, flags, rc):
    client.subscribe(SENSOR_TOPIC)
    client.subscribe("control/#")
    broadcast({"type": "system", "ts": time.time(),
               "message": f"Dashboard conectado ao broker (rc={rc})"})


def on_message(client, userdata, msg):
    global attacker_active
    if msg.topic == STATUS_TOPIC:
        try:
            st = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return
        with _state_lock:
            attacker_active = bool(st.get("active", False))
            active = attacker_active
        broadcast({"type": "attacker", "ts": time.time(), "active": active})
        return

    if msg.topic.startswith("control/"):
        return

    info = classify(msg.payload)
    info.update(type="message", ts=time.time(), topic=msg.topic)
    broadcast(info)


mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.tls_set(ca_certs=CA_CERT_PATH, tls_version=ssl.PROTOCOL_TLS_CLIENT)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/events")
def events():
    def stream():
        q = queue.Queue(maxsize=500)
        with _subs_lock:
            subscribers.append(q)
        with _state_lock:
            active = attacker_active
        yield f"data: {json.dumps({'type': 'hello', 'attackerActive': active})}\n\n"
        try:
            while True:
                try:
                    data = q.get(timeout=20)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with _subs_lock:
                if q in subscribers:
                    subscribers.remove(q)

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Connection": "keep-alive"})


@app.route("/api/attacker", methods=["POST"])
def api_attacker():
    body = request.get_json(force=True, silent=True) or {}
    active = bool(body.get("active", False))
    mqtt_client.publish(CONTROL_TOPIC, json.dumps({"active": active}), qos=1, retain=True)
    return jsonify({"active": active})


def main():
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()
    app.run(host="0.0.0.0", port=HTTP_PORT, threaded=True)


if __name__ == "__main__":
    main()
