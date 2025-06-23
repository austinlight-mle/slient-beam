# client_config.py

import json, os, base64, hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

CONFIG_FILE = 'client_config.enc'
PASSWORD_HASH = 'sha256_hash_of_admin_password'  # store a salted hash of the admin password

def get_aes_key():
    """Get the 32-byte AES key from an environment variable (base64-encoded)."""
    key_b64 = os.getenv('MONITOR_KEY')
    if not key_b64:
        raise RuntimeError("Encryption key not set (MONITOR_KEY env var missing).")
    return base64.b64decode(key_b64)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data with AES-256 GCM. Returns nonce + tag + ciphertext."""
    key = get_aes_key()
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return cipher.nonce + tag + ciphertext

def decrypt_data(blob: bytes) -> bytes:
    """Decrypt data (nonce + tag + ciphertext) with AES-256 GCM."""
    key = get_aes_key()
    nonce = blob[:12]
    tag = blob[12:28]
    ciphertext = blob[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    data = cipher.decrypt_and_verify(ciphertext, tag)
    return data

def load_config():
    """Decrypt and load the JSON config."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError("Configuration file not found.")
    with open(CONFIG_FILE, 'rb') as f:
        encrypted = f.read()
    data = decrypt_data(encrypted)
    return json.loads(data.decode('utf-8'))

def save_config(config: dict, admin_password: str):
    """Encrypt and save the JSON config; requires correct admin password."""
    # Verify admin password
    salted = (admin_password + "some_salt").encode('utf-8')
    if hashlib.sha256(salted).hexdigest() != PASSWORD_HASH:
        raise PermissionError("Invalid admin password.")
    # Serialize and encrypt
    data = json.dumps(config).encode('utf-8')
    encrypted = encrypt_data(data)
    with open(CONFIG_FILE, 'wb') as f:
        f.write(encrypted)
