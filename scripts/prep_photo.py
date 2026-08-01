#!/usr/bin/env python3
"""Prep a portrait photo for ASCII conversion.

Pipeline: (optional) background removal -> grayscale -> local-contrast boost
-> composite onto pure white. Writes data/portrait_prepped.png.

Usage:
    python scripts/prep_photo.py [path/to/photo.jpg]

With no argument it downloads your public GitHub avatar. rembg and OpenCV
are optional — if they aren't installed the script falls back to Pillow's
autocontrast, which is usually fine for avatars but a real photo looks much
better with the full pipeline (pip install opencv-python rembg).
"""
import io
import sys
from pathlib import Path

import requests
from PIL import Image, ImageOps

USERNAME = "dhruvrajkotia"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "portrait_prepped.png"


def load_source() -> Image.Image:
    if len(sys.argv) > 1:
        return Image.open(sys.argv[1])
    url = f"https://github.com/{USERNAME}.png?size=460"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))


def remove_background(img: Image.Image) -> Image.Image:
    try:
        from rembg import remove
        return remove(img)
    except ImportError:
        pass
    try:
        return grabcut(img)
    except ImportError:
        return img


def grabcut(img: Image.Image) -> Image.Image:
    """Centered-subject background removal — no ML model needed."""
    import cv2
    import numpy as np

    bgr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * 0.12), int(h * 0.05), int(w * 0.76), int(h * 0.93))
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")
    alpha = cv2.GaussianBlur(alpha, (7, 7), 0)
    rgba = np.dstack([cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), alpha])
    return Image.fromarray(rgba)


def boost_contrast(gray: Image.Image) -> Image.Image:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return ImageOps.autocontrast(gray, cutoff=1)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return Image.fromarray(clahe.apply(np.array(gray)))


def main() -> None:
    img = load_source().convert("RGBA")
    img = remove_background(img)
    # composite onto pure white so the background maps to the blank glyph
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white, img).convert("L")
    prepped = boost_contrast(flat)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prepped.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({prepped.width}x{prepped.height})")


if __name__ == "__main__":
    main()
