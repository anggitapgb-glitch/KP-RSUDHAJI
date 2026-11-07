"""
Validasi input citra untuk pipeline image processing OSSIA.

Fungsi utama:
    validate_xray(filename, file_bytes)

Catatan:
- Modul ini memeriksa validitas file dan karakteristik dasar citra.
- Modul ini TIDAK memastikan bahwa gambar benar-benar X-ray tangan kiri,
  bukan memastikan kualitas diagnostik, dan bukan melakukan diagnosis.
- Format yang diterima: PNG, JPG, JPEG.
"""

from pathlib import Path
from typing import Any

import cv2
import numpy as np


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100


def validate_extension(filename: str) -> tuple[bool, str]:
    """Memastikan ekstensi file termasuk PNG/JPG/JPEG."""
    if not filename or not str(filename).strip():
        return False, "Nama file tidak ditemukan."

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False, "Format file harus PNG, JPG, atau JPEG."

    return True, "Format file valid."


def validate_file_size(file_bytes: bytes) -> tuple[bool, str]:
    """Memastikan file tidak kosong dan tidak melebihi batas ukuran."""
    if not file_bytes:
        return False, "File kosong."

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return False, "Ukuran file maksimal 10 MB."

    return True, "Ukuran file valid."


def read_image(file_bytes: bytes) -> np.ndarray:
    """Mendekode bytes menjadi citra OpenCV."""
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise ValueError("Data file harus berupa bytes.")

    image_array = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)

    if image is None or image.size == 0:
        raise ValueError("File tidak dapat dibaca sebagai citra.")

    return image


def validate_dimensions(image: np.ndarray) -> tuple[bool, str]:
    """Memeriksa dimensi dan jumlah channel citra."""
    if image is None or not isinstance(image, np.ndarray):
        return False, "Citra tidak ditemukan atau tidak valid."

    if image.ndim not in (2, 3):
        return False, "Dimensi citra tidak didukung."

    height, width = image.shape[:2]

    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
        return False, (
            f"Resolusi citra terlalu kecil. Minimal "
            f"{MIN_IMAGE_WIDTH} x {MIN_IMAGE_HEIGHT} piksel."
        )

    if image.ndim == 3 and image.shape[2] not in (3, 4):
        return False, "Jumlah channel citra tidak didukung."

    return True, "Dimensi citra valid."


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Mengubah citra grayscale/RGB/RGBA OpenCV menjadi grayscale."""
    if image.ndim == 2:
        gray = image.copy()
    elif image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        raise ValueError("Format channel citra tidak dikenali.")

    return gray


def validate_intensity(gray: np.ndarray) -> tuple[bool, str]:
    """Memeriksa apakah citra memiliki data piksel yang dapat diproses."""
    if gray is None or gray.size == 0:
        return False, "Citra tidak memiliki piksel."

    if not np.isfinite(gray).all():
        return False, "Citra memiliki nilai piksel tidak valid."

    if np.min(gray) == np.max(gray):
        return False, "Citra memiliki intensitas konstan."

    return True, "Intensitas citra valid."


def validate_xray(filename: str, file_bytes: bytes) -> dict[str, Any]:
    """
    Menjalankan validasi input secara berurutan.

    Returns:
        dict berisi original_image, gray_image, metadata, dan status validasi.

    Raises:
        ValueError jika file atau citra tidak memenuhi pemeriksaan dasar.
    """
    valid, message = validate_extension(filename)
    if not valid:
        raise ValueError(message)

    valid, message = validate_file_size(file_bytes)
    if not valid:
        raise ValueError(message)

    image = read_image(file_bytes)

    valid, message = validate_dimensions(image)
    if not valid:
        raise ValueError(message)

    gray = convert_to_grayscale(image)

    valid, message = validate_intensity(gray)
    if not valid:
        raise ValueError(message)

    height, width = gray.shape
    channels = 1 if image.ndim == 2 else int(image.shape[2])

    return {
        "original_image": image,
        "gray_image": gray,
        "width": int(width),
        "height": int(height),
        "channels": channels,
        "dtype": str(image.dtype),
        "file_size": int(len(file_bytes)),
        "format": Path(filename).suffix.lower(),
        "validation_status": "valid",
        "validation_message": "Citra lolos validasi dasar."
    }
