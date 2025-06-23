# client_network.py

import requests
from requests.auth import HTTPBasicAuth

def send_screenshot(host_url, client_id, auth_token, monitor_num, image_bytes):
    """
    Send one screenshot to the server via HTTPS POST.
    Returns True on success (status 200), False otherwise.
    """
    url = f"https://{host_url}/upload"
    try:
        files = {'screenshot': (f'monitor{monitor_num}.webp', image_bytes, 'image/webp')}
        # Use HTTP Basic Auth with client_id and token
        auth = HTTPBasicAuth(client_id, auth_token)
        # Note: verify should use a proper CA cert or False if using self-signed
        resp = requests.post(url, files=files, auth=auth, verify=False, timeout=10)
        return resp.status_code == 200
    except requests.RequestException:
        return False
