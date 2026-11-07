"""
Segmentasi kandidat tepi yang lebih konservatif untuk ROI karpal OSSIA.

Catatan:
- Citra X-ray memiliki tekstur trabekular nyata; tidak mungkin menjamin edge map
  benar-benar bebas noise hanya dengan filter.
- Output adalah kandidat garis tepi untuk inspeksi, bukan mask tulang/osifikasi
  dan bukan segmentasi anatomi tervalidasi.
"""

from pathlib import Path
from typing import Dict, Any
import cv2
import numpy as np


def prepare_grayscale(image: np.ndarray) -> np.ndarray:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Citra kosong atau tidak valid.")
    if image.ndim == 3:
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif image.shape[2] == 1:
            image = image[:, :, 0]
        else:
            raise ValueError("Jumlah channel tidak didukung.")
    elif image.ndim != 2:
        raise ValueError("Citra harus grayscale atau BGR/BGRA.")
    if image.dtype != np.uint8:
        image = np.nan_to_num(image, nan=0, posinf=255, neginf=0)
        if image.max() == image.min():
            return np.zeros(image.shape, dtype=np.uint8)
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return image


def denoise_for_edges(image: np.ndarray, bilateral_d: int = 9,
                      sigma_color: float = 65, sigma_space: float = 65,
                      gaussian_ksize: int = 5) -> np.ndarray:
    """Reduksi tekstur berfrekuensi tinggi sebelum deteksi tepi."""
    gray = prepare_grayscale(image)
    if bilateral_d < 1:
        raise ValueError("bilateral_d harus positif.")
    if gaussian_ksize < 1 or gaussian_ksize % 2 == 0:
        raise ValueError("gaussian_ksize harus ganjil positif.")
    smooth = cv2.bilateralFilter(
        gray, d=bilateral_d, sigmaColor=sigma_color, sigmaSpace=sigma_space
    )
    if gaussian_ksize > 1:
        smooth = cv2.GaussianBlur(smooth, (gaussian_ksize, gaussian_ksize), 1.0)
    return smooth


def remove_short_edge_fragments(edges: np.ndarray, min_component_pixels: int = 22,
                                min_span: int = 7) -> np.ndarray:
    """Buang fragmen garis sangat pendek; tidak menghapus semua tekstur anatomis."""
    binary = (edges > 0).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    output = np.zeros_like(edges)
    for idx in range(1, count):
        area = int(stats[idx, cv2.CC_STAT_AREA])
        width = int(stats[idx, cv2.CC_STAT_WIDTH])
        height = int(stats[idx, cv2.CC_STAT_HEIGHT])
        if area >= min_component_pixels and max(width, height) >= min_span:
            output[labels == idx] = 255
    return output


def suppress_roi_border(edges: np.ndarray, margin: int = 5) -> np.ndarray:
    """Hilangkan garis tepi hasil crop ROI yang sering terdeteksi sebagai edge."""
    if margin <= 0:
        return edges.copy()
    out = edges.copy()
    m = min(margin, max(1, min(out.shape) // 4))
    out[:m, :] = 0
    out[-m:, :] = 0
    out[:, :m] = 0
    out[:, -m:] = 0
    return out


def make_overlay(gray: np.ndarray, edges: np.ndarray) -> np.ndarray:
    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    overlay[edges > 0] = (0, 0, 255)
    return overlay


def edge_summary(edges: np.ndarray) -> Dict[str, float]:
    total = int(edges.size)
    count = int(np.count_nonzero(edges))
    return {
        "total_pixels": total,
        "edge_pixels": count,
        "edge_percent": 100.0 * count / total if total else 0.0,
    }


def segment_roi(image: np.ndarray, *,
                bilateral_d: int = 9,
                sigma_color: float = 65,
                sigma_space: float = 65,
                gaussian_ksize: int = 5,
                canny_low: int = 60,
                canny_high: int = 150,
                min_component_pixels: int = 22,
                min_span: int = 7,
                border_margin: int = 5) -> Dict[str, Any]:
    gray = prepare_grayscale(image)
    if not (0 <= canny_low < canny_high <= 255):
        raise ValueError("Canny harus memenuhi 0 <= low < high <= 255.")

    filtered = denoise_for_edges(
        gray, bilateral_d, sigma_color, sigma_space, gaussian_ksize
    )
    # Edge mentah tetap disimpan untuk perbandingan.
    raw_edges = cv2.Canny(filtered, canny_low, canny_high, L2gradient=True)
    no_border = suppress_roi_border(raw_edges, border_margin)
    clean_edges = remove_short_edge_fragments(
        no_border, min_component_pixels, min_span
    )
    # Tidak melakukan dilation/closing: keduanya dapat menyatukan garis
    # dari tekstur trabekular dan menghasilkan kontur palsu.
    return {
        "gray_image": gray,
        "filtered_image": filtered,
        "raw_edges": raw_edges,
        "edges": clean_edges,
        "overlay": make_overlay(gray, clean_edges),
        "raw_summary": edge_summary(raw_edges),
        "summary": edge_summary(clean_edges),
        "settings": {
            "bilateral_d": bilateral_d,
            "sigma_color": sigma_color,
            "sigma_space": sigma_space,
            "gaussian_ksize": gaussian_ksize,
            "canny_low": canny_low,
            "canny_high": canny_high,
            "min_component_pixels": min_component_pixels,
            "min_span": min_span,
            "border_margin": border_margin,
        },
        "warning": (
            "Garis yang tersisa adalah kandidat tepi. Tekstur trabekular dapat "
            "tetap terdeteksi; hasil tidak boleh dianggap sebagai batas tulang "
            "atau segmentasi osifikasi yang tervalidasi."
        ),
    }


def save_segmentation_results(image: np.ndarray, result: Dict[str, Any],
                              output_dir: str = "outputs/segmentation_clean"):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    images = {
        "01_roi_input": result["gray_image"],
        "02_filtered_stronger": result["filtered_image"],
        "03_canny_raw": result["raw_edges"],
        "04_canny_clean": result["edges"],
        "05_clean_edge_overlay": result["overlay"],
    }
    saved = {}
    for name, array in images.items():
        path = out / f"{name}.png"
        if not cv2.imwrite(str(path), array):
            raise IOError(f"Gagal menyimpan {path}")
        saved[name] = path.as_posix()
    return saved
