# host_utils.py

import json
from config import HOSTS_FILE

def load_hosts():
    """Lee hosts.json y regresa un diccionario."""
    try:
        with open(HOSTS_FILE, "r") as file:
            return json.load(file)
    except:
        return {}

def save_hosts(hosts: dict):
    """Guarda el diccionario hosts en hosts.json."""
    with open(HOSTS_FILE, "w") as file:
        json.dump(hosts, file, indent=4)
