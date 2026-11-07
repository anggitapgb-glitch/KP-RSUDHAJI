"""
Mask refinement OSSIA: membersihkan noise dan menganalisis komponen terhubung.

Perhatian: operasi ini hanya memodifikasi mask biner. Tidak mengenali tulang.
Pilih parameter berdasarkan inspeksi dan validasi terhadap anotasi referensi.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import cv2
import numpy as np


def to_binary(mask: np.ndarray) -> np.ndarray:
    if mask is None or not isinstance(mask, np.ndarray) or mask.size == 0 or mask.ndim != 2:
        raise ValueError("Mask harus berupa array 2D yang tidak kosong.")
    return np.where(mask > 0, 255, 0).astype(np.uint8)


def connected_component_filter(mask: np.ndarray, min_area: int = 12) -> Dict[str, Any]:
    """Hapus komponen foreground lebih kecil dari min_area piksel."""
    binary = to_binary(mask)
    if min_area < 1:
        raise ValueError("min_area minimal 1.")
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    output = np.zeros_like(binary)
    components = []
    for label in range(1, count):
        x, y, w, h, area = [int(v) for v in stats[label]]
        keep = area >= min_area
        if keep:
            output[labels == label] = 255
        components.append({
            "label": label, "area": area, "x": x, "y": y, "width": w, "height": h,
            "centroid_x": float(centroids[label][0]), "centroid_y": float(centroids[label][1]),
            "kept": keep,
        })
    components.sort(key=lambda item: item["area"], reverse=True)
    return {"mask": output, "component_count": count - 1, "components": components}


def refine_mask(
    mask: np.ndarray,
    *,
    min_component_area: int = 12,
    morphology: str = "open",
    kernel_size: int = 3,
    iterations: int = 1,
) -> Dict[str, Any]:
    """Jalankan operasi morfologi opsional lalu filter komponen kecil."""
    binary = to_binary(mask)
    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("kernel_size harus ganjil positif.")
    if iterations < 1:
        raise ValueError("iterations minimal 1.")
    if morphology not in {"none", "open", "close"}:
        raise ValueError("morphology harus none, open, atau close.")

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    if morphology == "open":
        morphed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=iterations)
    elif morphology == "close":
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=iterations)
    else:
        morphed = binary.copy()

    filtered = connected_component_filter(morphed, min_area=min_component_area)
    return {
        "input_mask": binary, "morphology_mask": morphed, "refined_mask": filtered["mask"],
        "component_count": filtered["component_count"], "components": filtered["components"],
        "summary": {
            "input_foreground_ratio": float(np.count_nonzero(binary) / binary.size),
            "morphology_foreground_ratio": float(np.count_nonzero(morphed) / morphed.size),
            "refined_foreground_ratio": float(np.count_nonzero(filtered["mask"]) / filtered["mask"].size),
        },
        "settings": {"min_component_area": min_component_area, "morphology": morphology,
                     "kernel_size": kernel_size, "iterations": iterations}
    }


def create_overlay(image: np.ndarray, mask: np.ndarray, alpha: float = 0.40) -> np.ndarray:
    """Overlay mask foreground dengan warna merah pada citra grayscale."""
    gray = image
    if gray.ndim == 3:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    if gray.dtype != np.uint8:
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    binary = to_binary(mask)
    if gray.shape != binary.shape:
        raise ValueError("Ukuran citra dan mask harus sama.")
    if not 0 <= alpha <= 1:
        raise ValueError("alpha harus antara 0 dan 1.")
    base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    color = base.copy()
    color[binary > 0] = (0, 0, 255)
    return cv2.addWeighted(base, 1 - alpha, color, alpha, 0)


def save_refinement_results(
    image: np.ndarray, result: Dict[str, Any], output_dir: str | Path = "outputs/refinement"
) -> Dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    overlay = create_overlay(image, result["refined_mask"])
    items = {
        "input_mask.png": result["input_mask"],
        "morphology_mask.png": result["morphology_mask"],
        "refined_mask.png": result["refined_mask"],
        "overlay.png": overlay,
    }
    paths = {}
    for name, arr in items.items():
        path = out / name
        if not cv2.imwrite(str(path), arr):
            raise IOError(f"Gagal menyimpan {path}")
        paths[name] = path.as_posix()
    return paths
