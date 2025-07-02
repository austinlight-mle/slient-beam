# init_config.py

from client_config import save_config
from dotenv import load_dotenv
import os

load_dotenv()
host = "192.168.1.100:443"         # Replace with your real host IP/domain and port
client_id = "client1"              # Must match what's allowed on the host
auth_token = "lA9X-PZyB6csWiNsPRrfB8ATUMKGMfCW"  # Must match value in host's AUTHORIZED_CLIENTS
interval = 5                       # Screenshot interval in seconds
enabled = True                     # Activate the client
admin_password = os.environ["ADMIN_PASSWORD"]      # Your admin password (must match the hashed one in client_config.py)

# === DO NOT MODIFY BELOW ===
config = {
    "host": host,
    "interval": interval,
    "enabled": enabled,
    "client_id": client_id,
    "auth_token": auth_token
}

try:
    save_config(config, admin_password)
except PermissionError:
    print("Invalid admin password.")
except Exception as e:
    print(f"Failed to write config: {e}")
