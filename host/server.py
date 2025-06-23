# server.py

from flask import Flask, request, abort
from threading import Thread
import os, time, ssl
from datetime import datetime

app = Flask(__name__)
DATA_DIR = 'received'  # base directory for storing screenshots
os.makedirs(DATA_DIR, exist_ok=True)

# Pre-shared client credentials (in practice, load this from secure storage)
AUTHORIZED_CLIENTS = {
    'client1': 'secrettoken1',
    'client2': 'secrettoken2',
}

# Dictionary to log last heartbeat per client
client_status = {}

@app.route('/upload', methods=['POST'])
def upload():
    auth = request.authorization
    if not auth or auth.username not in AUTHORIZED_CLIENTS \
           or AUTHORIZED_CLIENTS[auth.username] != auth.password:
        abort(401)
    client_id = auth.username
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
    return 'OK', 200

def run_server():
    # SSL context: use your cert.pem and key.pem (self-signed OK for internal use)
    context = ('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', port=443, ssl_context=context, threaded=True, debug=False)

if __name__ == '__main__':
    # Start the Flask server in a background thread
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    print("Server running on HTTPS port 443. Enter 'list' to view clients, 'exit' to quit.")

    # CLI admin interface
    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd == 'list':
                print("Clients and last heartbeat:")
                for cid, ts in client_status.items():
                    print(f"  {cid}: {ts}")
            elif cmd == 'exit':
                print("Shutting down server...")
                break
            else:
                print("Commands: 'list', 'exit'")
    except (EOFError, KeyboardInterrupt):
        pass
