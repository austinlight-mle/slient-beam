from flask import Flask, request
import os
from datetime import datetime
import logging

app = Flask(__name__)

DATA_DIR = "received"  # Base directory for storing screenshots
os.makedirs(DATA_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/<client_id>/<monitor_num>/upload", methods=["POST"])
def upload(client_id: str, monitor_num: str):
    client_folder = os.path.join(DATA_DIR, client_id, monitor_num)
    os.makedirs(client_folder, exist_ok=True)

    for file_key in request.files:
        f = request.files[file_key]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"{timestamp}_{file_key}.webp"
        filepath = os.path.join(client_folder, filename)
        f.save(filepath)
        logger.info(f"Saved {filepath}")

    return "OK", 200


# WSGI entry point
if __name__ == "__main__":
    from waitress import serve

    logger.info("Starting production server on http://0.0.0.0:8081")
    serve(app, host="0.0.0.0", port=8081)
