"""
vegetation_index.py

Color-based vegetation indices for detecting green plant coverage in
ordinary RGB imagery (drone photos, phone photos, satellite RGB exports).

No special (multispectral / NIR) camera required. If you DO have a
near-infrared band available, see `ndvi()` at the bottom, which is more
accurate and is the industry-standard index -- use it when possible.

Indices implemented:
    - ExG   (Excess Green Index)          -- primary detector
    - ExGR  (Excess Green minus Excess Red) -- reduces false positives on
                                                 reddish/brown soil
    - HSV green-band mask                  -- secondary confirmation filter
    - NDVI                                 -- for 4-band (RGB+NIR) imagery

The default `green_mask()` combines ExGR + HSV for robustness: a pixel is
counted as "green vegetation" only if BOTH agree, which cuts down on
false positives from green-tinted rocks, tarps, painted surfaces, etc.
"""

from __future__ import annotations
import numpy as np


def _to_float(img: np.ndarray) -> np.ndarray:
    """Ensure image is float32 in range [0, 255]."""
    if img.dtype != np.float32 and img.dtype != np.float64:
        img = img.astype(np.float32)
    return img


def excess_green(img_rgb: np.ndarray) -> np.ndarray:
    """
    ExG = 2G - R - B

    Classic vegetation index (Woebbecke et al., 1995). Plants reflect
    strongly in green relative to red/blue, so healthy vegetation scores
    high positive values; soil, rock, and dead material score near zero
    or negative.
    """
    img = _to_float(img_rgb)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return 2 * g - r - b


def excess_red(img_rgb: np.ndarray) -> np.ndarray:
    """ExR = 1.4R - G  (Meyer & Neto, 2008) -- used to subtract soil glare."""
    img = _to_float(img_rgb)
    r, g = img[..., 0], img[..., 1]
    return 1.4 * r - g


def excess_green_minus_red(img_rgb: np.ndarray) -> np.ndarray:
    """ExGR = ExG - ExR. More robust to reddish/brown soil than ExG alone."""
    return excess_green(img_rgb) - excess_red(img_rgb)


def hsv_green_mask(img_rgb: np.ndarray,
                    hue_range=(30, 95),
                    min_sat=25,
                    min_val=25) -> np.ndarray:
    """
    Boolean mask of pixels whose Hue falls in the green band (OpenCV's
    0-179 hue scale) with enough saturation/brightness to exclude
    near-black shadow and near-white overexposed pixels.
    """
    import cv2
    img = img_rgb.astype(np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mask = (
        (h >= hue_range[0]) & (h <= hue_range[1]) &
        (s >= min_sat) & (v >= min_val)
    )
    return mask


def green_mask(img_rgb: np.ndarray,
                exgr_threshold: float = 10.0,
                use_hsv_confirmation: bool = True) -> np.ndarray:
    """
    Primary entry point: returns a boolean mask (H, W) where True = plant
    canopy / green vegetation.

    Method: ExGR thresholding, optionally confirmed by an HSV green-hue
    check. Combining both cuts false positives (e.g. green plastic mulch,
    algae-green water, painted equipment) since real canopy usually
    satisfies both a strong excess-green color signal AND a green hue.
    """
    exgr = excess_green_minus_red(img_rgb)
    mask = exgr > exgr_threshold

    if use_hsv_confirmation:
        mask &= hsv_green_mask(img_rgb)

    return mask


def ndvi(nir_band: np.ndarray, red_band: np.ndarray,
          healthy_threshold: float = 0.3) -> tuple[np.ndarray, np.ndarray]:
    """
    NDVI = (NIR - Red) / (NIR + Red)

    Use this instead of the RGB indices above if you have a 4-band
    (RGB + Near-Infrared) drone/satellite capture -- it's the agricultural
    industry standard and far more reliable than color-only indices,
    since it directly measures chlorophyll's NIR reflectance rather than
    inferring it from visible color.

    Returns (ndvi_array, healthy_mask) where healthy_mask = ndvi > threshold.
    Typical interpretation:
        NDVI < 0.1        -> bare soil / water / non-vegetated
        0.1 <= NDVI < 0.3  -> sparse / stressed vegetation
        NDVI >= 0.3        -> healthy, dense vegetation
    """
    nir = _to_float(nir_band)
    red = _to_float(red_band)
    denom = (nir + red)
    denom[denom == 0] = 1e-6
    ndvi_arr = (nir - red) / denom
    return ndvi_arr, (ndvi_arr > healthy_threshold)
