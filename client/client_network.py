# client_network.py

import requests
from requests.auth import HTTPBasicAuth
import getpass

username = getpass.getuser()


def send_screenshot(host_url, monitor_num, image_bytes):
    """
    Send one screenshot to the server via HTTPS POST.
    Returns True on success (status 200), False otherwise.
    """
    url = f"http://{host_url}/{username}/upload"
    print(url)
    try:
        files = {
            "screenshot": (f"monitor{monitor_num}.webp", image_bytes, "image/webp"),
        }
        resp = requests.post(url, files=files, timeout=10)
        print(resp.status_code)
        return resp.status_code == 200
    except requests.RequestException:
        return False
