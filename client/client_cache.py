# client_cache.py

import os, time
from client_config import encrypt_data, decrypt_data
from client_network import send_screenshot

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

import os, time
import pyzipper
from dotenv import load_dotenv

load_dotenv()
ENABLE_ONEFILE_CACHE = os.getenv("ONEFILE_CACHE", "false").lower() == "true"
ENCRYPTION_KEY = os.getenv("ZIP_ENCRYPTION_KEY", "defaultpassword").encode()


def cache_screenshot(monitor_id, img_bytes):
    filename = f"shot_{monitor_id}_{int(time.time())}.webp"

    if ENABLE_ONEFILE_CACHE:
        with pyzipper.AESZipFile(
            CACHE_DIR + "/screenshots_secure.zip",
            "a",
            compression=pyzipper.ZIP_LZMA,
            encryption=pyzipper.WZ_AES,
        ) as archive:
            archive.setpassword(ENCRYPTION_KEY)
            archive.writestr(filename, img_bytes)
    else:
        with open(filename, "wb") as f:
            f.write(img_bytes)


def retry_cached(host_url, client_id, auth_token):
    for fname in sorted(os.listdir(CACHE_DIR)):
        path = os.path.join(CACHE_DIR, fname)
        try:
            with open(path, "rb") as f:
                encrypted = f.read()
            image_bytes = decrypt_data(encrypted)
            mon = int(fname.split("_")[-1].lstrip("mon").split(".")[0])
            if send_screenshot(host_url, client_id, auth_token, mon, image_bytes):
                os.remove(path)
            else:
                break
        except Exception as e:
            continue
