# client_network.py

import requests
import getpass

username = getpass.getuser()


def send_screenshot(host_url, monitor_num, image_bytes):
    url = f"http://{host_url}/{username}/upload"
    try:
        files = {
            "screenshot": (f"monitor{monitor_num}.webp", image_bytes, "image/webp"),
        }
        resp = requests.post(url, files=files, timeout=10)
        return resp.status_code == 200
    except requests.RequestException:
        return False
