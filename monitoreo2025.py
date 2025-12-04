import time
import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ALERT_CHANNEL,
    TELEGRAM_COMMAND_GROUP,
    PING_INTERVAL
)

from host_utils import load_hosts
from net_utils import is_host_up

from commands import (
    cmd_start,
    cmd_lista_comandos,
    cmd_infra,
    cmd_registrar,
    cmd_eliminar,
    cmd_buscar,
    cmd_up,
    cmd_down,
    cmd_detalle
)

# =======================================
# ENVÍO DE MENSAJES
# =======================================

def send_alert(text: str):
    """Envía alertas al CANAL de monitoreo"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ALERT_CHANNEL, "text": text, "parse_mode": "HTML"}

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] ALERT: {e}")


def send_group(text: str):
    """Envía respuestas y comandos al GRUPO NOC"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_COMMAND_GROUP, "text": text, "parse_mode": "HTML"}

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] GROUP: {e}")


# =======================================
# MANEJO DE COMANDOS
# =======================================

LAST_UPDATE_ID = None


def check_telegram_commands():
    global LAST_UPDATE_ID

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {}

    if LAST_UPDATE_ID is not None:
        params["offset"] = LAST_UPDATE_ID

    try:
        resp = requests.get(url, params=params, timeout=10).json()
    except Exception as e:
        print(f"[ERROR] getUpdates: {e}")
        return

    if "result" not in resp:
        return

    for update in resp["result"]:
        LAST_UPDATE_ID = update["update_id"] + 1

        # ============================================
        # CALLBACK BUTTONS
        # ============================================
        if "callback_query" in update:
            cq = update["callback_query"]
            data = cq["data"]

            print(f"[CALLBACK] {data}")

            if data == "ver_comandos":
                cmd_lista_comandos(TELEGRAM_COMMAND_GROUP)

            elif data == "cmd_infra":
                cmd_infra(TELEGRAM_COMMAND_GROUP)

            elif data == "cmd_up":
                cmd_up(TELEGRAM_COMMAND_GROUP)

            elif data == "cmd_down":
                cmd_down(TELEGRAM_COMMAND_GROUP)

            continue

        # ============================================
        # MENSAJES NORMALES
        # ============================================
        if "message" not in update:
            continue

        msg = update["message"]
        chat_id = msg["chat"]["id"]

        # Solo responder si escriben en el GRUPO
        if str(chat_id) != str(TELEGRAM_COMMAND_GROUP):
            continue

        if "text" not in msg:
            continue

        text = msg["text"].strip()
        print(f"[CMD] {text}")

        # --------------------------------------------
        # COMANDOS
        # --------------------------------------------
        if text == "/start":
            cmd_start(chat_id)
            continue

        if text == "/infra":
            cmd_infra(chat_id)
            continue

        if text.startswith("/registrar"):
            args = text.replace("/registrar", "").strip()
            cmd_registrar(chat_id, args)
            continue

        if text.startswith("/eliminar"):
            args = text.replace("/eliminar", "").strip()
            cmd_eliminar(chat_id, args)
            continue

        if text.startswith("/buscar"):
            args = text.replace("/buscar", "").strip()
            cmd_buscar(chat_id, args)
            continue

        if text == "/up":
            cmd_up(chat_id)
            continue

        if text == "/down":
            cmd_down(chat_id)
            continue

        if text.startswith("/detalle"):
            args = text.replace("/detalle", "").strip()
            cmd_detalle(chat_id, args)
            continue


# =======================================
# LOOP PRINCIPAL DE MONITOREO
# =======================================

def main():
    print("Iniciando monitoreo...")
    send_alert("🚀 Monitoreo de infraestructura Heimtech iniciado.")

    status_prev = {}

    while True:
        HOSTS = load_hosts()

        # Inicializar estado
        for name in HOSTS:
            if name not in status_prev:
                status_prev[name] = None

        for name, host in HOSTS.items():
            is_up = is_host_up(host)

            # PRIMERA EVALUACIÓN
            if status_prev[name] is None:
                status_prev[name] = is_up

                if not is_up:
                    send_alert(
                        f"🚨 <b>ALERTA INICIAL</b>\n"
                        f"<b>{name}</b> ({host}) está <b>CAÍDO</b>."
                    )
                continue

            # CAMBIO DE ESTADO
            if is_up != status_prev[name]:
                status_prev[name] = is_up

                if not is_up:
                    send_alert(
                        f"🚨 <b>HOST CAÍDO</b>\n"
                        f"<b>{name}</b>\n"
                        f"IP: <code>{host}</code>\n"
                        f"Estado: ❌ INALCANZABLE"
                    )
                else:
                    send_alert(
                        f"✅ <b>HOST RECUPERADO</b>\n"
                        f"<b>{name}</b>\n"
                        f"IP: <code>{host}</code>\n"
                        f"Estado: 🟢 RESPONDIENDO"
                    )

        check_telegram_commands()

        time.sleep(PING_INTERVAL)


if __name__ == "__main__":
    main()
