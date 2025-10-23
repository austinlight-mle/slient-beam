import mss, io
from PIL import Image, ImageChops, ImageStat

# Cache grayscale previews per monitor for robust change detection
_LAST_PREVIEWS = {}

# Perceptual thresholds
PREVIEW_SIZE = (160, 90)  # higher resolution preview to catch small text changes
RMS_THRESHOLD = 1.0       # average per-pixel grayscale RMS diff (0-255)
PIX_DIFF_THRESHOLD = 3    # per-pixel grayscale change to consider "real"
MIN_CHANGED_FRACTION = 0.0005  # fraction of preview pixels that must exceed PIX_DIFF_THRESHOLD


def _has_meaningful_change(curr_preview: Image.Image, last_preview: Image.Image) -> bool:
    """Decide if there is a visually meaningful change.
    Combines RMS (global) and sparse pixel-change (local) checks to catch small typing changes
    while ignoring tiny color jitter.
    """
    diff = ImageChops.difference(curr_preview, last_preview)
    rms = ImageStat.Stat(diff).rms[0]
    if rms >= RMS_THRESHOLD:
        return True

    # Localized change check: how many pixels changed by >= PIX_DIFF_THRESHOLD?
    hist = diff.histogram()  # 256 bins for L mode
    changed_pixels = sum(hist[PIX_DIFF_THRESHOLD:])
    w, h = curr_preview.size
    min_pixels = max(5, int(w * h * MIN_CHANGED_FRACTION))
    return changed_pixels >= min_pixels


def capture_screenshots(max_monitors=2):
    screenshots = []
    with mss.mss() as sct:
        for idx in range(1, max_monitors + 1):
            if idx >= len(sct.monitors):
                break
            sct_img = sct.grab(sct.monitors[idx])

            # Build RGB image and a grayscale preview for perceptual change detection
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            preview = img.convert("L").resize(PREVIEW_SIZE, Image.BILINEAR)

            last = _LAST_PREVIEWS.get(idx)
            if last is not None and not _has_meaningful_change(preview, last):
                # No meaningful change; skip sending
                continue
            _LAST_PREVIEWS[idx] = preview

            # Only encode to WEBP when there is a meaningful change
            buf = io.BytesIO()
            img.save(
                buf, format="WEBP", quality=0.5, lossless=False, method=6, exact=False
            )
            screenshots.append((idx, buf.getvalue()))
    return screenshots
