# client_config.py

import json, os, base64, hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv
load_dotenv()


CONFIG_FILE = 'client_config.enc'
PASSWORD_HASH = 'f95618c6d325577d7756a62e47c8303b3f88e038bf0f6841900ad16fdbf146bd'  # store a salted hash of the admin password

def get_aes_key():
    """Get the 32-byte AES key from an environment variable (base64-encoded)."""
    key_b64 = os.getenv('MONITOR_KEY')
    if not key_b64:
        raise RuntimeError("Encryption key not set (MONITOR_KEY env var missing).")
    return base64.b64decode(key_b64)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data with AES-256 GCM. Returns nonce + tag + ciphertext."""
    key = get_aes_key()
    print("[encrypt_data]", key.hex())
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    print("  Nonce:", cipher.nonce.hex())
    print("  Tag:  ", tag.hex())
    print("  Ciphertext:", len(ciphertext), "bytes")
    return cipher.nonce + tag + ciphertext

def decrypt_data(blob: bytes) -> bytes:
    """Decrypt data (nonce + tag + ciphertext) with AES-256 GCM."""
    key = get_aes_key()
    print("[decrypt_data]", key.hex())
    nonce = blob[:16]
    tag = blob[16:32]
    ciphertext = blob[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    print("  Nonce:", nonce.hex())
    print("  Tag:  ", tag.hex())
    print("  Ciphertext:", len(ciphertext), "bytes")
    data = cipher.decrypt_and_verify(ciphertext, tag)
    return data

def load_config():
    """Decrypt and load the JSON config."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError("Configuration file not found.")
    with open(CONFIG_FILE, 'rb') as f:
        encrypted = f.read()
        print("[LOAD] Total size read:", len(encrypted))
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
    print("[SAVE] Total size written:", len(encrypted))
    with open(CONFIG_FILE, 'wb') as f:
        f.write(encrypted)
