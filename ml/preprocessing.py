"""
Preprocessing citra X-ray untuk OSSIA.

Pipeline:
1. Memastikan citra menjadi grayscale.
2. Normalisasi intensitas ke rentang uint8 (0-255).
3. CLAHE untuk peningkatan kontras lokal (opsional).
4. Median filtering (opsional).
5. Gaussian filtering (opsional).

Catatan:
- Fungsi ini tidak melakukan deteksi anatomi atau diagnosis.
- Parameter perlu dievaluasi pada dataset X-ray yang digunakan.
"""

from __future__ import annotations

from typing import Any, Dict
import cv2
import numpy as np


def _ensure_image(image: np.ndarray) -> np.ndarray:
    """Validasi input array citra dan kembalikan array yang aman diproses."""
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Citra kosong atau bukan numpy.ndarray.")

    if image.dtype == object:
        raise ValueError("Tipe data citra tidak didukung.")

    return image


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Konversi citra 1/3/4 kanal menjadi grayscale uint8."""
    image = _ensure_image(image)

    if image.ndim == 2:
        gray = image
    elif image.ndim == 3:
        channels = image.shape[2]
        if channels == 1:
            gray = image[:, :, 0]
        elif channels == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif channels == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError(f"Jumlah channel tidak didukung: {channels}")
    else:
        raise ValueError(f"Dimensi citra tidak didukung: {image.ndim}")

    return normalize_image(gray)


def normalize_image(gray: np.ndarray) -> np.ndarray:
    """Normalisasi intensitas ke uint8 0-255."""
    gray = _ensure_image(gray)
    if gray.ndim != 2:
        raise ValueError("normalize_image membutuhkan citra grayscale 2D.")

    if gray.dtype == np.uint8:
        return gray.copy()

    data = gray.astype(np.float32)
    finite = np.isfinite(data)
    if not finite.any():
        raise ValueError("Citra tidak memiliki nilai piksel valid.")

    min_value = float(data[finite].min())
    max_value = float(data[finite].max())

    safe = np.zeros(data.shape, dtype=np.float32)
    safe[finite] = data[finite]

    if max_value <= min_value:
        return np.zeros(gray.shape, dtype=np.uint8)

    scaled = (safe - min_value) * (255.0 / (max_value - min_value))
    scaled[~finite] = 0
    return np.clip(scaled, 0, 255).astype(np.uint8)


def apply_clahe(
    gray: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """Peningkatan kontras lokal menggunakan CLAHE."""
    gray = normalize_image(gray)
    if clip_limit <= 0:
        raise ValueError("clip_limit harus lebih besar dari 0.")
    if len(tile_grid_size) != 2 or min(tile_grid_size) < 1:
        raise ValueError("tile_grid_size harus berupa pasangan bilangan positif.")

    clahe = cv2.createCLAHE(
        clipLimit=float(clip_limit),
        tileGridSize=(int(tile_grid_size[0]), int(tile_grid_size[1])),
    )
    return clahe.apply(gray)


def median_filter(gray: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Reduksi noise impuls dengan median blur."""
    gray = normalize_image(gray)
    if kernel_size < 3 or kernel_size % 2 == 0:
        raise ValueError("kernel_size median harus bilangan ganjil >= 3.")
    return cv2.medianBlur(gray, int(kernel_size))


def gaussian_filter(
    gray: np.ndarray,
    kernel_size: int = 3,
    sigma: float = 0,
) -> np.ndarray:
    """Penghalusan citra menggunakan Gaussian blur."""
    gray = normalize_image(gray)
    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("kernel_size Gaussian harus bilangan ganjil positif.")
    if sigma < 0:
        raise ValueError("sigma tidak boleh negatif.")

    return cv2.GaussianBlur(
        gray,
        (int(kernel_size), int(kernel_size)),
        sigmaX=float(sigma),
    )


def preprocess_xray(
    image: np.ndarray,
    *,
    use_clahe: bool = True,
    use_median: bool = False,
    use_gaussian: bool = False,
    clahe_clip_limit: float = 2.0,
    clahe_tile_grid_size: tuple[int, int] = (8, 8),
    median_kernel: int = 3,
    gaussian_kernel: int = 3,
    gaussian_sigma: float = 0,
) -> Dict[str, Any]:
    """
    Jalankan pipeline preprocessing dan kembalikan seluruh tahap.

    Median dan Gaussian filter default nonaktif agar detail korteks dan
    struktur tulang tidak dihaluskan tanpa evaluasi.
    """
    original = _ensure_image(image).copy()
    gray = to_grayscale(original)
    normalized = normalize_image(gray)

    current = normalized.copy()
    clahe_image = None
    median_image = None
    gaussian_image = None

    if use_clahe:
        clahe_image = apply_clahe(
            current,
            clip_limit=clahe_clip_limit,
            tile_grid_size=clahe_tile_grid_size,
        )
        current = clahe_image.copy()

    if use_median:
        median_image = median_filter(current, kernel_size=median_kernel)
        current = median_image.copy()

    if use_gaussian:
        gaussian_image = gaussian_filter(
            current,
            kernel_size=gaussian_kernel,
            sigma=gaussian_sigma,
        )
        current = gaussian_image.copy()

    return {
        "original_image": original,
        "gray_image": gray,
        "normalized_image": normalized,
        "clahe_image": clahe_image,
        "median_image": median_image,
        "gaussian_image": gaussian_image,
        "preprocessed_image": current,
        "metadata": {
            "height": int(current.shape[0]),
            "width": int(current.shape[1]),
            "dtype": str(current.dtype),
            "min_intensity": int(current.min()),
            "max_intensity": int(current.max()),
            "clahe_enabled": bool(use_clahe),
            "median_enabled": bool(use_median),
            "gaussian_enabled": bool(use_gaussian),
        },
    }
