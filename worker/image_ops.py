from __future__ import annotations

import io
from typing import Tuple

import numpy as np
from PIL import Image


def _to_gray(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("L"), dtype=np.float32)


def blur_score(image_bytes: bytes) -> float:
    """Compute a simple blur score using variance of Laplacian. Higher is sharper.
    Returns normalized value 0..1 by mapping typical range [0, 1000] to [0,1].
    """
    img = Image.open(io.BytesIO(image_bytes))
    gray = _to_gray(img)
    # Laplacian kernel
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    lap = _convolve2d(gray, kernel)
    var = float(np.var(lap))
    # Normalize: 0..1000 -> 0..1 (clamped)
    return float(max(0.0, min(1.0, var / 1000.0)))


def glare_score(image_bytes: bytes) -> float:
    """Approx glare ratio: fraction of pixels near white (>= 250) in grayscale.
    Return 0..1 where higher is worse glare.
    """
    img = Image.open(io.BytesIO(image_bytes))
    gray = _to_gray(img)
    total = gray.size
    bright = np.sum(gray >= 250)
    return float(bright) / float(total)


def crop_bbox(image_bytes: bytes, bbox: Tuple[float, float, float, float]) -> bytes:
    """Crop image by bbox normalized (Left, Top, Width, Height) in [0,1]."""
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    L, T, W, H = bbox
    left = int(L * w)
    top = int(T * h)
    right = int((L + W) * w)
    bottom = int((T + H) * h)
    img2 = img.crop((left, top, right, bottom))
    out = io.BytesIO()
    img2.save(out, format="JPEG", quality=95)
    return out.getvalue()


def _convolve2d(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kh, kw = kernel.shape
    ih, iw = img.shape
    pad_h = kh // 2
    pad_w = kw // 2
    padded = np.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect")
    out = np.zeros_like(img)
    for i in range(ih):
        for j in range(iw):
            region = padded[i : i + kh, j : j + kw]
            out[i, j] = np.sum(region * kernel)
    return out

