import json
import os

STATUS_FILE = "status.json"

# =========================
# Cargar estados
# =========================
def load_status():
    if not os.path.exists(STATUS_FILE):
        return {}

    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


# =========================
# Guardar estados
# =========================
def save_status(status_dict):
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status_dict, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Guardando status.json: {e}")
