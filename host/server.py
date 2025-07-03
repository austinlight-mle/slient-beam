# server.py

from flask import Flask, request, abort
from threading import Thread
import os, time, ssl
from datetime import datetime

app = Flask(__name__)
DATA_DIR = "received"  # base directory for storing screenshots
os.makedirs(DATA_DIR, exist_ok=True)
client_status = {}


@app.route("/<client_id>/upload", methods=["POST"])
def upload(client_id: str):
    # Ensure client-specific folder exists
    client_folder = os.path.join(DATA_DIR, client_id)
    os.makedirs(client_folder, exist_ok=True)
    # Handle one or multiple files
    for file_key in request.files:
        f = request.files[file_key]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{timestamp}_{file_key}.webp"
        filepath = os.path.join(client_folder, filename)
        f.save(filepath)
    # Update heartbeat/status
    client_status[client_id] = datetime.now()
    return "OK", 200


def run_server():
    app.run(host="0.0.0.0", port=8081, threaded=True, debug=False)


if __name__ == "__main__":
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    print(
        "Server running on HTTPS port 8081. Enter 'list' to view clients, 'exit' to quit."
    )

    # CLI admin interface
    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd == "list":
                print("Clients and last heartbeat:")
                for cid, ts in client_status.items():
                    print(f"  {cid}: {ts}")
            elif cmd == "exit":
                print("Shutting down server...")
                break
            else:
                print("Commands: 'list', 'exit'")
    except (EOFError, KeyboardInterrupt):
        pass
