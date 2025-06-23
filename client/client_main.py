# client_main.py

import time, threading, sys, signal
from client_config import load_config
from client_screenshot import capture_screenshots
from client_network import send_screenshot
from client_cache import cache_screenshot, retry_cached

# Prevent unauthorized shutdown: intercept signals
def require_password_on_exit(signum, frame):
    pwd = input("Enter admin password to stop the service: ")
    # Note: compare hash or call config logic as above
    print("Invalid password. Continuing to run...")

for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, require_password_on_exit)

def main():
    # Load configuration (decrypted)
    try:
        config = load_config()
    except Exception as e:
        print("Failed to load config:", e)
        sys.exit(1)
    if not config.get('enabled', False):
        print("Client is disabled in configuration.")
        return

    host = config['host']
    interval = config.get('interval', 5)
    client_id = config['client_id']
    auth_token = config['auth_token']

    while True:
        # Retry sending any cached images first
        retry_cached(host, client_id, auth_token)
        # Capture new screenshots
        shots = capture_screenshots(max_monitors=2)
        for mon, img_bytes in shots:
            success = send_screenshot(host, client_id, auth_token, mon, img_bytes)
            if not success:
                cache_screenshot(mon, img_bytes)
        time.sleep(interval)

if __name__ == '__main__':
    # The script should be packaged/run in a way that hides the console (PyInstaller --noconsole)
    main()
