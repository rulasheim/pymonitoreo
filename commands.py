# commands.py

import requests
import ipaddress
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_COMMAND_GROUP
from host_utils import load_hosts, save_hosts


# ==========================================================
# Función para responder SIEMPRE al GRUPO, no al canal
# ==========================================================
def send_group(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_COMMAND_GROUP,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] Telegram (commands): {e}")


# ==========================================================
# Start con botones
# ==========================================================
def cmd_start(chat_id):
    if str(chat_id) != str(TELEGRAM_COMMAND_GROUP):
        return  # NO permitir start fuera del grupo

    image_url = "https://i.imgur.com/fHyEMsl.jpeg"

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={
                "chat_id": TELEGRAM_COMMAND_GROUP,
                "caption": (
                    "👋 <b>Bienvenido al Monitor de Infraestructura Heimtech</b>\n\n"
                    "Monitorea sucursales, registra hosts y consulta el estado general.\n"
                ),
                "parse_mode": "HTML"
            },
            files={"photo": requests.get(image_url).content}
        )
    except Exception as e:
        print(f"[ERROR] Imagen start: {e}")

    botones = {
        "inline_keyboard": [
            [{"text": "📘 Ver comandos", "callback_data": "ver_comandos"}],
            [{"text": "📡 Estado General", "callback_data": "cmd_infra"}],
            [
                {"text": "🟢 Hosts UP", "callback_data": "cmd_up"},
                {"text": "🔴 Hosts DOWN", "callback_data": "cmd_down"},
            ]
        ]
    }

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_COMMAND_GROUP,
            "text": "Selecciona una opción:",
            "reply_markup": botones,
            "parse_mode": "HTML"
        }
    )


# ==========================================================
# Infra — usa datos del monitor, no ping
# ==========================================================
def cmd_infra(chat_id):
    from monitoreo2025 import HOST_STATUS

    lines = ["📡 <b>ESTADO DE INFRAESTRUCTURA</b>\n"]

    for name, data in HOST_STATUS.items():
        estado = "🟢 UP" if data["up"] else "🔴 DOWN"
        lines.append(
            f"<b>{name}</b>\n"
            f"IP: <code>{data['ip']}</code>\n"
            f"Estado: {estado}\n"
        )

    send_group("\n".join(lines))


# ==========================================================
# Registrar nuevo host
# ==========================================================
def cmd_registrar(chat_id, args):
    partes = args.split()

    if len(partes) != 2:
        send_group("❌ Uso correcto:\n/registrar NombreHost 172.28.x.x")
        return

    nombre, ip = partes

    try:
        ipaddress.ip_address(ip)
    except:
        send_group(f"❌ La IP <code>{ip}</code> no es válida.")
        return

    hosts = load_hosts()

    if nombre in hosts:
        send_group(f"⚠️ El host <b>{nombre}</b> ya existe.")
        return

    hosts[nombre] = ip
    save_hosts(hosts)

    send_group(f"✅ Host registrado:\n<b>{nombre}</b>\nIP: <code>{ip}</code>")


# ==========================================================
# Eliminar host
# ==========================================================
def cmd_eliminar(chat_id, args):
    nombre = args.strip()
    hosts = load_hosts()

    if nombre not in hosts:
        send_group(f"❌ El host <b>{nombre}</b> no existe.")
        return

    del hosts[nombre]
    save_hosts(hosts)

    send_group(f"🗑️ Host eliminado:\n<b>{nombre}</b>")


# ==========================================================
# Buscar host
# ==========================================================
def cmd_buscar(chat_id, args):
    texto = args.strip().lower()
    hosts = load_hosts()
    from monitoreo2025 import HOST_STATUS

    resultados = {
        name: data for name, data in HOST_STATUS.items()
        if texto in name.lower() or texto in data["ip"]
    }

    if not resultados:
        send_group(f"🔎 Sin resultados para: <b>{texto}</b>")
        return

    lines = [f"🔎 <b>Resultados para:</b> {texto}\n"]

    for name, data in resultados.items():
        estado = "🟢 UP" if data["up"] else "🔴 DOWN"
        lines.append(
            f"<b>{name}</b>\n"
            f"IP: <code>{data['ip']}</code>\n"
            f"Estado: {estado}\n"
        )

    send_group("\n".join(lines))


# ==========================================================
# Hosts UP / DOWN
# ==========================================================
def cmd_up(chat_id):
    from monitoreo2025 import HOST_STATUS

    lines = ["🟢 <b>HOSTS ACTIVOS</b>\n"]

    for name, data in HOST_STATUS.items():
        if data["up"]:
            lines.append(f"<b>{name}</b> — {data['ip']}")

    send_group("\n".join(lines))


def cmd_down(chat_id):
    from monitoreo2025 import HOST_STATUS

    lines = ["🔴 <b>HOSTS CAÍDOS</b>\n"]

    for name, data in HOST_STATUS.items():
        if not data["up"]:
            lines.append(f"<b>{name}</b> — {data['ip']}")

    send_group("\n".join(lines))


# ==========================================================
# Detalle
# ==========================================================
def cmd_detalle(chat_id, args):
    nombre = args.strip()
    from monitoreo2025 import HOST_STATUS

    if nombre not in HOST_STATUS:
        send_group(f"❌ El host <b>{nombre}</b> no existe.")
        return

    data = HOST_STATUS[nombre]
    estado = "🟢 UP" if data["up"] else "🔴 DOWN"

    send_group(
        f"📘 <b>DETALLE DEL HOST</b>\n\n"
        f"<b>Nombre:</b> {nombre}\n"
        f"<b>IP:</b> <code>{data['ip']}</code>\n"
        f"<b>Estado:</b> {estado}"
    )


# ==========================================================
# Lista de comandos
# ==========================================================
def cmd_lista_comandos(chat_id):
    texto = (
        "📘 <b>Comandos disponibles</b>\n\n"
        "/infra – Estado general\n"
        "/registrar nombre ip – Registrar host\n"
        "/eliminar nombre – Eliminar host\n"
        "/buscar texto – Buscar\n"
        "/up – Activos\n"
        "/down – Caídos\n"
        "/detalle nombre – Detalle\n"
    )

    send_group(texto)
