# client_main.py

import time
from client_screenshot import capture_screenshots
from client_network import send_screenshot


def main():
    host = "127.0.0.1:8081"
    interval = 4

    while True:
        shots = capture_screenshots(max_monitors=2)
        for mon, img_bytes in shots:
            send_screenshot(host, mon, img_bytes)
            # cache_screenshot(mon, img_bytes)
        time.sleep(interval)


if __name__ == "__main__":
    main()
