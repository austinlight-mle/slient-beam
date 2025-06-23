# client_cache.py

import os, time
from client_config import encrypt_data, decrypt_data
from client_network import send_screenshot

CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_screenshot(monitor_num, image_bytes):
    """Encrypt and save the screenshot to the local cache."""
    timestamp = time.strftime("%Y%m%d%H%M%S")
    filename = os.path.join(CACHE_DIR, f"{timestamp}_mon{monitor_num}.bin")
    encrypted = encrypt_data(image_bytes)
    with open(filename, 'wb') as f:
        f.write(encrypted)

def retry_cached(host_url, client_id, auth_token):
    """
    Attempt to resend all cached images.
    If send succeeds, delete the cache file.
    """
    for fname in sorted(os.listdir(CACHE_DIR)):
        path = os.path.join(CACHE_DIR, fname)
        try:
            with open(path, 'rb') as f:
                encrypted = f.read()
            image_bytes = decrypt_data(encrypted)
            # Extract monitor number from filename (assumes our naming)
            mon = int(fname.split('_')[-1].lstrip('mon').split('.')[0])
            if send_screenshot(host_url, client_id, auth_token, mon, image_bytes):
                os.remove(path)
            else:
                # If one fails, stop retrying for now
                break
        except Exception as e:
            # If decryption fails or other error, skip the file
            continue
