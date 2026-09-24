"""
vegetation_index.py

Color-based vegetation indices for detecting green plant coverage in
ordinary RGB imagery.

The module provides:
    - ExG   (Excess Green)
    - ExR   (Excess Red)
    - ExGR  (Excess Green minus Excess Red)
    - HSV green-band analysis
    - Combined RGB vegetation mask
    - Continuous vegetation confidence
    - NDVI for RGB + NIR imagery

RGB imagery can estimate visible vegetation coverage and color-based
vegetation condition indicators. It should not be treated as a direct
measurement of physiological crop health.

For multispectral imagery with a Near-Infrared band, use NDVI when
available.
"""

from __future__ import annotations

import numpy as np


def _to_float(img: np.ndarray) -> np.ndarray:
    """Ensure image is float32/float64."""

    if img.dtype != np.float32 and img.dtype != np.float64:
        img = img.astype(np.float32)

    return img


# ============================================================
# RGB VEGETATION INDICES
# ============================================================

def excess_green(img_rgb: np.ndarray) -> np.ndarray:
    """
    ExG = 2G - R - B

    Higher positive values generally indicate stronger green
    color response.
    """

    img = _to_float(img_rgb)

    r = img[..., 0]
    g = img[..., 1]
    b = img[..., 2]

    return 2 * g - r - b


def excess_red(img_rgb: np.ndarray) -> np.ndarray:
    """
    ExR = 1.4R - G

    Used as part of ExGR to reduce some false positives caused
    by reddish/brown surfaces.
    """

    img = _to_float(img_rgb)

    r = img[..., 0]
    g = img[..., 1]

    return 1.4 * r - g


def excess_green_minus_red(img_rgb: np.ndarray) -> np.ndarray:
    """
    ExGR = ExG - ExR
    """

    return excess_green(img_rgb) - excess_red(img_rgb)


# ============================================================
# HSV ANALYSIS
# ============================================================

def hsv_channels(img_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return HSV channels using OpenCV's ranges:

        H: 0-179
        S: 0-255
        V: 0-255
    """

    import cv2

    img = np.clip(
        img_rgb,
        0,
        255,
    ).astype(np.uint8)

    hsv = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2HSV,
    )

    h = hsv[..., 0]
    s = hsv[..., 1]
    v = hsv[..., 2]

    return h, s, v


def hsv_green_mask(
    img_rgb: np.ndarray,
    hue_range=(30, 95),
    min_sat=25,
    min_val=25,
) -> np.ndarray:
    """
    Boolean mask for pixels inside the configured HSV green range.
    """

    h, s, v = hsv_channels(img_rgb)

    return (
        (h >= hue_range[0])
        & (h <= hue_range[1])
        & (s >= min_sat)
        & (v >= min_val)
    )


# ============================================================
# CONTINUOUS VEGETATION SIGNAL
# ============================================================

def vegetation_confidence(
    img_rgb: np.ndarray,
    exgr_threshold: float = 10.0,
    hue_range=(30, 95),
    min_sat: float = 25,
    min_val: float = 25,
) -> np.ndarray:
    """
    Estimate a continuous 0-1 vegetation confidence score.

    This is NOT a physiological crop-health measurement.

    The score combines:
        - ExGR response
        - HSV hue membership
        - saturation
        - brightness

    Higher values indicate stronger agreement with the RGB
    vegetation characteristics used by FieldScanner.
    """

    exgr = excess_green_minus_red(img_rgb)

    h, s, v = hsv_channels(img_rgb)

    # --------------------------------------------------------
    # ExGR component
    # --------------------------------------------------------

    # Values around the configured threshold start receiving
    # meaningful confidence.
    exgr_strength = (
        exgr - exgr_threshold
    ) / max(
        30.0,
        abs(exgr_threshold),
    )

    exgr_strength = np.clip(
        exgr_strength,
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # Hue component
    # --------------------------------------------------------

    hue_min, hue_max = hue_range

    hue_center = (
        hue_min + hue_max
    ) / 2.0

    hue_half_width = (
        hue_max - hue_min
    ) / 2.0

    hue_distance = np.abs(
        h.astype(np.float32) - hue_center
    )

    hue_score = 1.0 - (
        hue_distance / max(hue_half_width, 1.0)
    )

    hue_score = np.clip(
        hue_score,
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # Saturation component
    # --------------------------------------------------------

    saturation_score = (
        s.astype(np.float32) - min_sat
    ) / max(
        255.0 - min_sat,
        1.0,
    )

    saturation_score = np.clip(
        saturation_score,
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # Brightness component
    # --------------------------------------------------------

    brightness_score = (
        v.astype(np.float32) - min_val
    ) / max(
        255.0 - min_val,
        1.0,
    )

    brightness_score = np.clip(
        brightness_score,
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # Combined score
    # --------------------------------------------------------

    confidence = (
        0.45 * exgr_strength
        + 0.30 * hue_score
        + 0.15 * saturation_score
        + 0.10 * brightness_score
    )

    return np.clip(
        confidence,
        0.0,
        1.0,
    )


# ============================================================
# PRIMARY VEGETATION MASK
# ============================================================

def green_mask(
    img_rgb: np.ndarray,
    exgr_threshold: float = 10.0,
    use_hsv_confirmation: bool = True,
) -> np.ndarray:
    """
    Primary vegetation detector.

    Returns:
        Boolean array with shape (H, W)

    True = detected green vegetation.
    """

    exgr = excess_green_minus_red(
        img_rgb
    )

    mask = exgr > exgr_threshold

    if use_hsv_confirmation:

        mask &= hsv_green_mask(
            img_rgb
        )

    return mask


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def vegetation_features(
    img_rgb: np.ndarray,
    exgr_threshold: float = 10.0,
    use_hsv_confirmation: bool = True,
) -> dict:
    """
    Calculate all RGB vegetation features needed by the analyzer.

    Returns a dictionary containing:
        exg
        exr
        exgr
        green_mask
        confidence
        hue
        saturation
        value
    """

    exg = excess_green(img_rgb)
    exr = excess_red(img_rgb)
    exgr = exg - exr

    mask = green_mask(
        img_rgb,
        exgr_threshold=exgr_threshold,
        use_hsv_confirmation=use_hsv_confirmation,
    )

    confidence = vegetation_confidence(
        img_rgb,
        exgr_threshold=exgr_threshold,
    )

    h, s, v = hsv_channels(
        img_rgb
    )

    return {
        "exg": exg,
        "exr": exr,
        "exgr": exgr,
        "green_mask": mask,
        "confidence": confidence,
        "hue": h,
        "saturation": s,
        "value": v,
    }


# ============================================================
# NDVI
# ============================================================

def ndvi(
    nir_band: np.ndarray,
    red_band: np.ndarray,
    healthy_threshold: float = 0.3,
) -> tuple[np.ndarray, np.ndarray]:
    """
    NDVI = (NIR - Red) / (NIR + Red)

    Intended for imagery containing a Near-Infrared band.

    Returns:
        ndvi_array
        healthy_mask
    """

    nir = _to_float(nir_band)
    red = _to_float(red_band)

    denom = nir + red

    denom = np.where(
        denom == 0,
        1e-6,
        denom,
    )

    ndvi_arr = (
        (nir - red) / denom
    )

    healthy_mask = (
        ndvi_arr > healthy_threshold
    )

    return ndvi_arr, healthy_mask