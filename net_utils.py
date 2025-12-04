# net_utils.py

import subprocess
import os

def is_host_up(host: str) -> bool:
    """Ping real usando comando del SO (Windows/Linux)."""
    try:
        cmd = ["ping", "-n", "1", host] if os.name == "nt" else ["ping", "-c", "1", host]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Ping {host}: {e}")
        return False
