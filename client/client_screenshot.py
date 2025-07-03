# client_screenshot.py

import mss, io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


def capture_screenshots(max_monitors=2):
    screenshots = []
    with mss.mss() as sct:
        for idx in range(1, max_monitors + 1):
            if idx >= len(sct.monitors):
                break
            sct_img = sct.grab(sct.monitors[idx])
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(
                buf, format="WEBP", quality=1, lossless=False, method=6, exact=False
            )
            webp_data = buf.getvalue()
            screenshots.append((idx, webp_data))
    return screenshots
