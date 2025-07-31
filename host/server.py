from flask import Flask, request
from threading import Thread
import os, time, ssl
from datetime import datetime

app = Flask(__name__)
DATA_DIR = "received"  # base directory for storing screenshots
os.makedirs(DATA_DIR, exist_ok=True)


@app.route("/<client_id>/<monitor_num>/upload", methods=["POST"])
def upload(client_id: str, monitor_num: str):
    # Ensure client-specific folder exists
    client_folder = os.path.join(DATA_DIR, client_id)
    os.makedirs(client_folder, exist_ok=True)
    monitor_folder = os.path.join(client_folder, monitor_num)
    os.makedirs(monitor_folder, exist_ok=True)
    # Handle one or multiple files
    for file_key in request.files:
        f = request.files[file_key]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{timestamp}_{file_key}.webp"
        filepath = os.path.join(client_folder, monitor_num, filename)
        f.save(filepath)
    return "OK", 200


def run_server():
    app.run(host="0.0.0.0", port=8081, threaded=True, debug=False)


if __name__ == "__main__":
    run_server()
    print("Server running on HTTPS port 8081.")
