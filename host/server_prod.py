from flask import Flask, request
import os, sys
from datetime import datetime
import logging

app = Flask(__name__)

# Anchor data directory to script/exe folder to avoid CWD issues
if getattr(sys, "frozen", False):  # PyInstaller exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "received")  # Base directory for storing screenshots
os.makedirs(DATA_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/<client_id>/<monitor_num>/upload", methods=["POST"])
def upload(client_id: str, monitor_num: str):
    # Create directory structure: received/<client_id>/<YYYYMMDD>/<monitor_num>/
    now_dt = datetime.now()  # single timestamp per request to keep folder/filenames consistent
    date_str = now_dt.strftime("%Y%m%d")
    monitor_folder = os.path.join(DATA_DIR, client_id, date_str, monitor_num)
    os.makedirs(monitor_folder, exist_ok=True)

    for file_key in request.files:
        f = request.files[file_key]
        timestamp = now_dt.strftime("%Y%m%d%H%M%S%f")
        filename = f"{timestamp}_{file_key}.webp"
        filepath = os.path.join(monitor_folder, filename)
        f.save(filepath)
        logger.info(f"Saved {filepath}")

    return "OK", 200


# WSGI entry point
if __name__ == "__main__":
    from waitress import serve

    logger.info("Starting production server on http://0.0.0.0:8081")
    serve(app, host="0.0.0.0", port=8081)
