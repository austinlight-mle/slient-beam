# client_screenshot.py

import mss, io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def capture_screenshots(max_monitors=2):
    """
    Capture up to max_monitors screens.
    Returns a list of (monitor_index, webp_bytes).
    """
    screenshots = []
    with mss.mss() as sct:
        # MSS index 1 is first monitor, 2 is second, etc.
        for idx in range(1, max_monitors+1):
            if idx >= len(sct.monitors):
                break
            sct_img = sct.grab(sct.monitors[idx])
            # Convert raw pixels to a Pillow Image (RGB):contentReference[oaicite:8]{index=8}
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            # Save to WebP in-memory
            buf = io.BytesIO()
            img.save(buf, format='WEBP', quality=50)
            webp_data = buf.getvalue()
            screenshots.append((idx, webp_data))
    return screenshots
