"""
Automatic exploratory carpal-region mask and ossification-candidate pipeline.

IMPORTANT:
- This is an image-processing baseline, NOT a validated anatomical model.
- It does not reliably identify each of the eight carpal bones.
- Review the generated masks before using them for measurements.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import cv2
import numpy as np


def _gray_u8(image: np.ndarray) -> np.ndarray:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Citra kosong/tidak valid.")
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.ndim != 2:
        raise ValueError("Citra harus grayscale.")
    if image.dtype != np.uint8:
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return image


def _largest_component(binary: np.ndarray, min_area: int = 20) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    out = np.zeros_like(binary)
    if count <= 1:
        return out
    candidates = [
        (int(stats[i, cv2.CC_STAT_AREA]), i)
        for i in range(1, count)
        if int(stats[i, cv2.CC_STAT_AREA]) >= min_area
    ]
    # Retain multiple meaningful components; do not force bones into one blob.
    for _, label in candidates:
        out[labels == label] = 255
    return out


def automatic_carpal_region_mask(
    image: np.ndarray,
    *,
    threshold_percentile: float = 58.0,
    close_kernel: int = 9,
    min_component_area: int = 35,
    central_fraction: float = 0.92,
) -> Dict[str, Any]:
    """
    Estimate a broad carpal-region mask from a cropped carpal ROI.

    The output is a coarse candidate envelope, not bone-by-bone anatomy.
    Assumes input is already cropped around the carpal region (ROI stage).
    """
    gray = _gray_u8(image)
    h, w = gray.shape
    if not 0 < threshold_percentile < 100:
        raise ValueError("threshold_percentile harus 0-100.")
    if close_kernel < 3 or close_kernel % 2 == 0:
        raise ValueError("close_kernel harus ganjil dan >=3.")
    if not 0.5 <= central_fraction <= 1.0:
        raise ValueError("central_fraction harus 0.5-1.0.")

    # Local contrast enhancement and edge-preserving denoising.
    denoised = cv2.bilateralFilter(gray, 5, 28, 28)
    enhanced = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8)).apply(denoised)

    # Restrict search to the central portion of the already selected carpal ROI.
    # This only reduces peripheral contamination; it is not anatomical localization.
    x_margin = int((1.0 - central_fraction) * w / 2)
    y_margin = int((1.0 - central_fraction) * h / 2)
    search = np.zeros((h, w), dtype=np.uint8)
    search[y_margin:h-y_margin if y_margin else h,
           x_margin:w-x_margin if x_margin else w] = 255

    values = enhanced[search > 0]
    threshold = float(np.percentile(values, threshold_percentile))
    bright = np.where((enhanced >= threshold) & (search > 0), 255, 0).astype(np.uint8)

    # Connect nearby trabecular/high-density regions into a broad candidate envelope.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (close_kernel, close_kernel)
    )
    closed = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, kernel, iterations=2)
    opened = cv2.morphologyEx(
        closed, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        iterations=1
    )
    candidate = _largest_component(opened, min_area=min_component_area)
    candidate = cv2.dilate(candidate, np.ones((3, 3), np.uint8), iterations=1)
    candidate[search == 0] = 0

    # Generate a review overlay.
    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    tint = overlay.copy()
    tint[candidate > 0] = (0, 255, 0)
    overlay = cv2.addWeighted(overlay, 0.65, tint, 0.35, 0)

    area = int(np.count_nonzero(candidate))
    total = int(candidate.size)
    ratio = 100.0 * area / total if total else 0.0

    warnings = []
    if area == 0:
        warnings.append("Mask kosong; coba percentile lebih rendah atau periksa ROI.")
    if ratio > 75:
        warnings.append("Mask sangat luas; kemungkinan mencakup struktur non-karpal.")
    if ratio < 8:
        warnings.append("Mask sangat kecil; kemungkinan banyak tulang tidak terdeteksi.")
    warnings.append(
        "Mask otomatis ini bukan delineasi anatomis tervalidasi dan tidak memisahkan "
        "delapan tulang karpal secara andal."
    )

    return {
        "gray_image": gray,
        "enhanced_image": enhanced,
        "search_region_mask": search,
        "threshold_mask": bright,
        "carpal_region_mask": candidate,
        "overlay": overlay,
        "threshold": threshold,
        "statistics": {
            "mask_pixels": area,
            "roi_pixels": total,
            "mask_ratio_percent": ratio,
            "components": max(0, cv2.connectedComponents(candidate, 8)[0] - 1),
        },
        "warnings": warnings,
    }


def segment_bright_candidates(
    image: np.ndarray,
    region_mask: np.ndarray,
    *,
    percentile: float = 72.0,
    min_component_area: int = 3,
) -> Dict[str, Any]:
    """Select radiopaque intensity candidates only inside the estimated region."""
    gray = _gray_u8(image)
    if region_mask is None or region_mask.shape[:2] != gray.shape:
        raise ValueError("region_mask harus berukuran sama dengan citra.")
    region = np.where(region_mask > 0, 255, 0).astype(np.uint8)
    values = gray[region > 0]
    if values.size < 32:
        raise ValueError("Mask wilayah terlalu kecil untuk segmentasi kandidat.")
    threshold = float(np.percentile(values, percentile))
    raw = np.where((gray >= threshold) & (region > 0), 255, 0).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(raw, 8)
    cleaned = np.zeros_like(raw)
    kept = 0
    for i in range(1, count):
        if int(stats[i, cv2.CC_STAT_AREA]) >= min_component_area:
            cleaned[labels == i] = 255
            kept += 1
    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    tint = overlay.copy()
    tint[cleaned > 0] = (0, 0, 255)
    overlay = cv2.addWeighted(overlay, 0.62, tint, 0.38, 0)
    return {
        "candidate_mask": cleaned,
        "overlay": overlay,
        "threshold": threshold,
        "statistics": {
            "region_pixels": int(np.count_nonzero(region)),
            "candidate_pixels": int(np.count_nonzero(cleaned)),
            "candidate_ratio_percent": (
                100.0 * np.count_nonzero(cleaned) / np.count_nonzero(region)
                if np.count_nonzero(region) else 0.0
            ),
            "components_kept": kept,
        },
    }


def save_auto_results(region_result: Dict[str, Any],
                      candidate_result: Dict[str, Any],
                      output_dir: str | Path = "outputs/auto_ossification") -> Dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    items = {
        "01_enhanced.png": region_result["enhanced_image"],
        "02_auto_carpal_region_mask.png": region_result["carpal_region_mask"],
        "03_auto_region_overlay.png": region_result["overlay"],
        "04_ossification_candidate_mask.png": candidate_result["candidate_mask"],
        "05_ossification_candidate_overlay.png": candidate_result["overlay"],
    }
    paths = {}
    for name, image in items.items():
        path = out / name
        if not cv2.imwrite(str(path), image):
            raise IOError(f"Gagal menyimpan {path}")
        paths[name] = path.as_posix()
    return paths
