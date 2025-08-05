import time
import sys
from client_screenshot import capture_screenshots
from client_network import send_screenshot


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <host>")
        sys.exit(1)

    host = sys.argv[1] + ":8081"
    print(host)
    interval = 5

    while True:
        shots = capture_screenshots(max_monitors=2)
        for mon, img_bytes in shots:
            send_screenshot(host, mon, img_bytes)
        time.sleep(interval)


if __name__ == "__main__":
    main()
