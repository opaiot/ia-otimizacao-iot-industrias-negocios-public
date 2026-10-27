import hashlib
import hmac
import json
import os
import ssl

import paho.mqtt.client as mqtt

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", "8883"))
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "sensors/#")
HMAC_KEY = bytes.fromhex(os.environ["HMAC_KEY_HEX"])

CA_CERT_PATH = "/certs/ca.crt"

# HMAC garante que o conteudo não foi alterado e que quem assinou tem a
# chave certa, mas um payload legitimo reenviado tal como foi capturado
# (replay) continua com HMAC valido. Por isso guardamos, por dispositivo, o
# maior "seq" ja aceito: qualquer seq repetido ou menor é rejeitado aqui.
last_seq_by_device = {}


def sign(device: str, seq, temp: str) -> str:
    message = f"{device}|{seq}|{temp}".encode()
    return hmac.new(HMAC_KEY, message, hashlib.sha256).hexdigest()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[CONECTADO] broker={MQTT_HOST}:{MQTT_PORT} topic={MQTT_TOPIC}", flush=True)
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[ERRO] falha na conexao, rc={rc}", flush=True)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        device = data["device"]
        seq = data["seq"]
        temp = data["temp"]
        received_hmac = data["hmac"]
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
        print(f"[DESCARTADA] payload malformado em {msg.topic}", flush=True)
        return

    expected_hmac = sign(device, seq, temp)

    if not hmac.compare_digest(received_hmac, expected_hmac):
        print(f"[REJEITADA] device={device} seq={seq} - HMAC invalido", flush=True)
        return

    try:
        seq_int = int(seq)
    except (TypeError, ValueError):
        seq_int = None

    if seq_int is not None:
        last_seq = last_seq_by_device.get(device)
        if last_seq is not None and seq_int <= last_seq:
            print(
                f"[REJEITADA] device={device} seq={seq} - replay ou fora de ordem "
                f"(ultimo aceito: {last_seq})",
                flush=True,
            )
            return
        last_seq_by_device[device] = seq_int

    print(f"[VALIDA] device={device} seq={seq}", flush=True)
    print(f"temperatura={float(temp):.2f} C", flush=True)

    # Demonstracao: a mesma assinatura nao valida mais um payload adulterado
    tampered_temp = f"{float(temp) + 1:.2f}"
    tampered_ok = hmac.compare_digest(received_hmac, sign(device, seq, tampered_temp))
    print(flush=True)
    print("TESTE: temperatura adulterada (+1 C):", flush=True)
    print("ACEITA" if tampered_ok else "REJEITADA", flush=True)
    print(flush=True)


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
