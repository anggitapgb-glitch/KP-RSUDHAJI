"""
Kandidat segmentasi area osifikasi di dalam area tulang karpal OSSIA.

Input:
1) citra ROI karpal grayscale
2) mask area tulang karpal (dibuat/diperiksa manual sebagai batas analisis)

Output:
- enhanced_image
- candidate_mask (piksel radiopak/intensitas tinggi di dalam mask tulang)
- overlay
- statistik kandidat

PENTING:
Threshold intensitas hanya menghasilkan kandidat radiopak, bukan identifikasi
osifikasi anatomis yang tervalidasi. Mask referensi perlu ditinjau ahli.
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
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError("Channel citra tidak didukung.")
    if image.ndim != 2:
        raise ValueError("Citra harus grayscale 2D.")
    if image.dtype != np.uint8:
        image = np.nan_to_num(image, nan=0, posinf=255, neginf=0)
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return image


def _binary_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if mask is None or not isinstance(mask, np.ndarray) or mask.size == 0:
        raise ValueError("Mask karpal belum diberikan.")
    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    if mask.ndim != 2 or mask.shape != shape:
        raise ValueError(f"Mask harus berukuran sama dengan ROI: {shape[1]}x{shape[0]}.")
    return np.where(mask > 0, 255, 0).astype(np.uint8)


def enhance_carpal_roi(
    image: np.ndarray,
    clahe_clip: float = 2.0,
    clahe_grid: int = 8,
    bilateral_d: int = 5,
    sigma_color: float = 30,
    sigma_space: float = 30,
) -> np.ndarray:
    """Denoising bilateral lalu CLAHE untuk mempertahankan tepi/detail lokal."""
    gray = _gray_u8(image)
    if clahe_clip <= 0 or clahe_grid < 1 or bilateral_d < 1:
        raise ValueError("Parameter enhancement tidak valid.")
    denoised = cv2.bilateralFilter(
        gray, d=bilateral_d, sigmaColor=sigma_color, sigmaSpace=sigma_space
    )
    clahe = cv2.createCLAHE(
        clipLimit=float(clahe_clip), tileGridSize=(int(clahe_grid), int(clahe_grid))
    )
    return clahe.apply(denoised)


def _masked_otsu(image: np.ndarray, bone_mask: np.ndarray, bright_foreground: bool) -> tuple[np.ndarray, float]:
    """Otsu dihitung hanya dari piksel di dalam mask tulang."""
    values = image[bone_mask > 0]
    if values.size < 32:
        raise ValueError("Area mask karpal terlalu kecil untuk thresholding.")
    # Histogram Otsu satu dimensi pada piksel terpilih, bukan pada background luar.
    hist = np.bincount(values, minlength=256).astype(np.float64)
    total = hist.sum()
    sum_total = np.dot(np.arange(256), hist)
    sum_bg = 0.0
    weight_bg = 0.0
    best_var = -1.0
    threshold = 0
    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if between > best_var:
            best_var = between
            threshold = t

    if bright_foreground:
        candidate = (image > threshold).astype(np.uint8) * 255
    else:
        candidate = (image <= threshold).astype(np.uint8) * 255
    candidate[bone_mask == 0] = 0
    return candidate, float(threshold)


def segment_ossification_candidates(
    image: np.ndarray,
    carpal_bone_mask: np.ndarray,
    *,
    method: str = "percentile",
    percentile: float = 70.0,
    bright_foreground: bool = True,
    clahe_clip: float = 2.0,
    clahe_grid: int = 8,
    min_component_area: int = 3,
    morphology: str = "none",
    morphology_kernel: int = 3,
) -> Dict[str, Any]:
    """
    Kandidat radiopak dalam mask tulang karpal.

    method:
      - percentile: threshold persentil intensitas di dalam mask tulang.
      - otsu: Otsu dihitung hanya dari piksel mask tulang.
    """
    gray = _gray_u8(image)
    bone_mask = _binary_mask(carpal_bone_mask, gray.shape)
    enhanced = enhance_carpal_roi(gray, clahe_clip=clahe_clip, clahe_grid=clahe_grid)

    values = enhanced[bone_mask > 0]
    if values.size < 32:
        raise ValueError("Mask tulang karpal terlalu kecil/kosong.")

    if method == "percentile":
        if not 0 < percentile < 100:
            raise ValueError("percentile harus di antara 0 dan 100.")
        threshold = float(np.percentile(values, percentile))
        if bright_foreground:
            candidate = (enhanced >= threshold).astype(np.uint8) * 255
        else:
            candidate = (enhanced <= threshold).astype(np.uint8) * 255
    elif method == "otsu":
        candidate, threshold = _masked_otsu(enhanced, bone_mask, bright_foreground)
    else:
        raise ValueError("method harus percentile atau otsu.")

    candidate[bone_mask == 0] = 0

    if morphology not in {"none", "open", "close"}:
        raise ValueError("morphology harus none, open, atau close.")
    if morphology_kernel < 1 or morphology_kernel % 2 == 0:
        raise ValueError("morphology_kernel harus ganjil positif.")
    if min_component_area < 1:
        raise ValueError("min_component_area minimal 1.")

    if morphology != "none":
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (morphology_kernel, morphology_kernel)
        )
        op = cv2.MORPH_OPEN if morphology == "open" else cv2.MORPH_CLOSE
        candidate = cv2.morphologyEx(candidate, op, kernel)

    # Hapus komponen sangat kecil hanya jika diminta; nilai default konservatif.
    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, 8)
    cleaned = np.zeros_like(candidate)
    kept_components = 0
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= min_component_area:
            cleaned[labels == label] = 255
            kept_components += 1

    cleaned[bone_mask == 0] = 0
    bone_pixels = int(np.count_nonzero(bone_mask))
    candidate_pixels = int(np.count_nonzero(cleaned))
    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    tint = overlay.copy()
    tint[cleaned > 0] = (0, 0, 255)
    overlay = cv2.addWeighted(overlay, 0.60, tint, 0.40, 0)
    # Batas area tulang ditampilkan hijau agar pembatas analisis terlihat.
    contours, _ = cv2.findContours(bone_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 255, 0), 1)

    return {
        "gray_image": gray,
        "enhanced_image": enhanced,
        "carpal_bone_mask": bone_mask,
        "candidate_mask": cleaned,
        "overlay": overlay,
        "threshold": float(threshold),
        "method": method,
        "statistics": {
            "bone_area_pixels": bone_pixels,
            "candidate_ossification_pixels": candidate_pixels,
            "candidate_ratio_percent": (
                100.0 * candidate_pixels / bone_pixels if bone_pixels else 0.0
            ),
            "components_kept": kept_components,
        },
        "settings": {
            "method": method, "percentile": percentile,
            "bright_foreground": bright_foreground,
            "clahe_clip": clahe_clip, "clahe_grid": clahe_grid,
            "min_component_area": min_component_area,
            "morphology": morphology, "morphology_kernel": morphology_kernel,
        },
    }


def save_ossification_results(
    result: Dict[str, Any], output_dir: str | Path = "outputs/ossification"
) -> Dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    images = {
        "01_enhanced.png": result["enhanced_image"],
        "02_carpal_bone_mask.png": result["carpal_bone_mask"],
        "03_ossification_candidate_mask.png": result["candidate_mask"],
        "04_ossification_overlay.png": result["overlay"],
    }
    saved = {}
    for filename, image in images.items():
        path = out / filename
        if not cv2.imwrite(str(path), image):
            raise IOError(f"Gagal menyimpan {path}")
        saved[filename] = path.as_posix()
    return saved
