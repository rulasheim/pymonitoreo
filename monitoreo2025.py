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
from status_utils import load_status, save_status

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


# ==========================================================
# ENVÍO DE MENSAJES
# ==========================================================

def send_alert(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_ALERT_CHANNEL, "text": text, "parse_mode": "HTML"}

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] ALERT: {e}")


def send_group(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_COMMAND_GROUP, "text": text, "parse_mode": "HTML"}

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] GROUP: {e}")


# ==========================================================
# MANEJO DE COMANDOS TELEGRAM
# ==========================================================

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

        # CALLBACK BUTTONS
        if "callback_query" in update:
            cq = update["callback_query"]
            data = cq["data"]

            if data == "ver_comandos":
                cmd_lista_comandos(TELEGRAM_COMMAND_GROUP)

            elif data == "cmd_infra":
                cmd_infra(TELEGRAM_COMMAND_GROUP)

            elif data == "cmd_up":
                cmd_up(TELEGRAM_COMMAND_GROUP)

            elif data == "cmd_down":
                cmd_down(TELEGRAM_COMMAND_GROUP)

            continue

        # MENSAJES NORMALES
        if "message" not in update:
            continue

        msg = update["message"]
        chat_id = msg["chat"]["id"]

        if str(chat_id) != str(TELEGRAM_COMMAND_GROUP):
            continue

        if "text" not in msg:
            continue

        text = msg["text"].strip()
        print(f"[CMD] {text}")

        if text == "/start":
            cmd_start(chat_id)

        elif text == "/infra":
            cmd_infra(chat_id)

        elif text.startswith("/registrar"):
            cmd_registrar(chat_id, text.replace("/registrar", "").strip())

        elif text.startswith("/eliminar"):
            cmd_eliminar(chat_id, text.replace("/eliminar", "").strip())

        elif text.startswith("/buscar"):
            cmd_buscar(chat_id, text.replace("/buscar", "").strip())

        elif text == "/up":
            cmd_up(chat_id)

        elif text == "/down":
            cmd_down(chat_id)

        elif text.startswith("/detalle"):
            cmd_detalle(chat_id, text.replace("/detalle", "").strip())


# ==========================================================
# LOOP PRINCIPAL DE MONITOREO
# ==========================================================

def main():
    print("Iniciando monitoreo…")
    send_alert(
        "🚀 Monitoreo de infraestructura Heimtech iniciado v1.4\n"
        "Revisa Performance SLA desde Matriz:\n"
        "🔗 https://187.218.57.198:4443/ng/network/virtualwan/health-check"
    )

    status_prev = {}
    down_since = {}
    alerted_down = {}

    status_json = load_status()

    while True:
        HOSTS = load_hosts()

        # Inicialización
        for name, ip in HOSTS.items():
            if name not in status_prev:
                status_prev[name] = None
                down_since[name] = None
                alerted_down[name] = False
                status_json.setdefault(name, "UNKNOWN")

        for name, host in HOSTS.items():
            is_up = is_host_up(host)
            now = time.time()

            fg_url = f"https://{host}:4443"
            sla_url = "https://187.218.57.198:4443/ng/network/virtualwan/health-check"

            # Actualizar JSON
            status_json[name] = "UP" if is_up else "DOWN"
            save_status(status_json)

            # PRIMERA VEZ
            if status_prev[name] is None:
                status_prev[name] = is_up
                continue

            # SIN CAMBIO
            if is_up == status_prev[name]:

                if not is_up and down_since[name] and not alerted_down[name]:
                    if now - down_since[name] >= 60:

                        send_alert(
                            f"🚨 <b>HOST CAÍDO +1 MIN</b>\n"
                            f"<b>{name}</b>\n"
                            f"IP: <code>{host}</code>\n"
                            f"🔗 FG: {fg_url}\n\n"
                            f"📡 Revisa Performance SLA:\n"
                            f"{sla_url}"
                        )

                        alerted_down[name] = True
                continue

            # CAMBIOS DE ESTADO
            # UP → DOWN
            if not is_up:
                status_prev[name] = False
                down_since[name] = now
                alerted_down[name] = False
                print(f"[DOWN] {name} detectado como caído. Esperando 60s…")
                continue

            # DOWN → UP
            if is_up:
                if alerted_down[name]:

                    send_alert(
                        f"✅ <b>HOST RECUPERADO</b>\n"
                        f"<b>{name}</b>\n"
                        f"IP: <code>{host}</code>\n"
                        f"🔗 FG: {fg_url}\n\n"
                        f"📡 Revisa Performance SLA:\n"
                        f"{sla_url}"
                    )

                status_prev[name] = True
                down_since[name] = None
                alerted_down[name] = False
                continue

        check_telegram_commands()
        time.sleep(PING_INTERVAL)


if __name__ == "__main__":
    main()
