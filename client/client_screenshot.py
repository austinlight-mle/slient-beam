import mss, io, hashlib
from PIL import Image

# Cache last hashes per monitor to detect changes
_LAST_HASHES = {}


def capture_screenshots(max_monitors=2):
    screenshots = []
    with mss.mss() as sct:
        for idx in range(1, max_monitors + 1):
            if idx >= len(sct.monitors):
                break
            sct_img = sct.grab(sct.monitors[idx])
            # Compute hash of raw BGRA bytes to detect any pixel difference
            h = hashlib.md5(sct_img.bgra).hexdigest()
            if _LAST_HASHES.get(idx) == h:
                # No change since last capture for this monitor; skip sending
                continue
            _LAST_HASHES[idx] = h

            # Only encode to WEBP when there is a change
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(
                buf, format="WEBP", quality=0.5, lossless=False, method=6, exact=False
            )
            screenshots.append((idx, buf.getvalue()))
    return screenshots
