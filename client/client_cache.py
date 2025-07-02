# client_cache.py

import os, time
from client_config import encrypt_data, decrypt_data
from client_network import send_screenshot

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# def cache_screenshot(monitor_num, image_bytess):
#     """Encrypt and save the screenshot to the local cache."""
#     timestamp = time.strftime("%Y%m%d%H%M%S")
#     filename = os.path.join(CACHE_DIR, f"{timestamp}_mon{monitor_num}.bin")
#     encrypted = encrypt_data(image_bytes)
#     with open(filename, 'wb') as f:
#         f.write(encrypted)

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
    """
    Attempt to resend all cached images.
    If send succeeds, delete the cache file.
    """
    for fname in sorted(os.listdir(CACHE_DIR)):
        path = os.path.join(CACHE_DIR, fname)
        try:
            with open(path, "rb") as f:
                encrypted = f.read()
            image_bytes = decrypt_data(encrypted)
            # Extract monitor number from filename (assumes our naming)
            mon = int(fname.split("_")[-1].lstrip("mon").split(".")[0])
            if send_screenshot(host_url, client_id, auth_token, mon, image_bytes):
                os.remove(path)
            else:
                # If one fails, stop retrying for now
                break
        except Exception as e:
            # If decryption fails or other error, skip the file
            continue
