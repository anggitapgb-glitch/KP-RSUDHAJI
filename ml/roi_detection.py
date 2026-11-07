"""
Pemilihan ROI tulang karpal berbentuk poligon untuk OSSIA.

Pengguna menandai kontur luar kumpulan tulang karpal dengan klik kiri.
Tekan ENTER/SPACE untuk menyelesaikan, BACKSPACE untuk menghapus titik
terakhir, R untuk mengulang, dan ESC untuk membatalkan.

File carpal_roi.png berisi crop bounding-box dengan area di luar poligon
dihitamkan. carpal_roi_mask.png menyimpan mask poligon (255 = area ROI).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

import cv2
import numpy as np


Point = Tuple[int, int]
Polygon = List[Point]


def load_grayscale_image(image_path: str | Path) -> np.ndarray:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"File citra tidak ditemukan: {path}")
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Citra tidak dapat dibaca: {path}")
    return image


def validate_roi(
    image: np.ndarray,
    roi: Tuple[int, int, int, int],
) -> Tuple[int, int, int, int]:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Citra kosong atau tidak valid.")
    if image.ndim not in (2, 3):
        raise ValueError("Citra harus berupa grayscale atau warna.")
    if len(roi) != 4:
        raise ValueError("ROI harus berupa (x, y, width, height).")

    x, y, width, height = (int(v) for v in roi)
    image_height, image_width = image.shape[:2]
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError("Koordinat dan ukuran ROI harus positif.")
    if x + width > image_width or y + height > image_height:
        raise ValueError("ROI berada di luar batas citra.")
    return x, y, width, height


def crop_roi(image: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
    x, y, width, height = validate_roi(image, roi)
    return image[y:y + height, x:x + width].copy()


def _display_image(image: np.ndarray, max_width: int, max_height: int):
    h, w = image.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    dw, dh = max(1, round(w * scale)), max(1, round(h * scale))
    if scale < 1:
        shown = cv2.resize(image, (dw, dh), interpolation=cv2.INTER_AREA)
    else:
        shown = image.copy()
    return shown, scale


def _draw_polygon_ui(base: np.ndarray, points: Polygon, finished: bool) -> np.ndarray:
    canvas = base.copy()
    for point in points:
        cv2.circle(canvas, point, 4, (0, 255, 255), -1)
    if len(points) >= 2:
        cv2.polylines(
            canvas, [np.asarray(points, dtype=np.int32)],
            finished, (0, 255, 0), 2, cv2.LINE_AA
        )
    if len(points) >= 3 and finished:
        overlay = canvas.copy()
        cv2.fillPoly(overlay, [np.asarray(points, dtype=np.int32)], (0, 180, 0))
        canvas = cv2.addWeighted(overlay, 0.18, canvas, 0.82, 0)
    instructions = [
        "Klik kiri: tambah titik | ENTER: selesai",
        "BACKSPACE: hapus titik | R: ulang | ESC: batal",
        "Tandai batas luar kumpulan tulang karpal; hindari radius/ulna",
    ]
    y = 24
    for line in instructions:
        cv2.putText(canvas, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.52, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(canvas, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.52, (255, 255, 255), 1, cv2.LINE_AA)
        y += 23
    return canvas


def select_roi_interactively(
    image: np.ndarray,
    window_name: str = "Pilih ROI tulang karpal - poligon",
    max_display_width: int = 1200,
    max_display_height: int = 800,
) -> Tuple[int, int, int, int]:
    """
    Kompatibilitas lama: pemilihan poligon dikembalikan sebagai bounding box.
    Gunakan select_carpal_roi_interactively untuk memperoleh poligon juga.
    """
    roi, _polygon = select_carpal_roi_interactively(
        image, window_name, max_display_width, max_display_height
    )
    return roi


def select_carpal_roi_interactively(
    image: np.ndarray,
    window_name: str = "Pilih ROI tulang karpal - poligon",
    max_display_width: int = 1200,
    max_display_height: int = 800,
) -> Tuple[Tuple[int, int, int, int], Polygon]:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Citra kosong atau tidak valid.")
    if image.ndim == 3:
        if image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError("Format channel citra tidak didukung.")
    elif image.ndim == 2:
        gray = image
    else:
        raise ValueError("Citra harus 2D atau 3D.")

    shown, scale = _display_image(gray, max_display_width, max_display_height)
    points_display: Polygon = []
    finished = False
    cancelled = False

    def on_mouse(event, x, y, flags, userdata):
        nonlocal points_display
        if event == cv2.EVENT_LBUTTONDOWN and not finished:
            points_display.append((int(x), int(y)))

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, on_mouse)
    try:
        while True:
            cv2.imshow(window_name, _draw_polygon_ui(shown, points_display, finished))
            key = cv2.waitKey(20) & 0xFF
            if key in (13, 10, 32):  # Enter / Space
                if len(points_display) >= 3:
                    finished = True
                    break
                print("Tambahkan minimal 3 titik untuk membentuk poligon.")
            elif key in (8, 127):  # Backspace / Delete
                if points_display:
                    points_display.pop()
            elif key in (ord("r"), ord("R")):
                points_display.clear()
            elif key == 27:  # ESC
                cancelled = True
                break
    finally:
        cv2.destroyAllWindows()

    if cancelled:
        raise RuntimeError("Pemilihan ROI dibatalkan.")
    if len(points_display) < 3:
        raise RuntimeError("Poligon ROI tidak valid; minimal 3 titik.")

    original_h, original_w = gray.shape[:2]
    points_original = [
        (max(0, min(original_w - 1, int(round(px / scale)))),
         max(0, min(original_h - 1, int(round(py / scale)))))
        for px, py in points_display
    ]

    polygon_array = np.asarray(points_original, dtype=np.int32)
    x, y, w, h = cv2.boundingRect(polygon_array)
    roi = validate_roi(gray, (x, y, w, h))
    return roi, points_original


def create_roi_preview(
    image: np.ndarray,
    roi: Tuple[int, int, int, int],
    polygon: Optional[Polygon] = None,
) -> np.ndarray:
    x, y, width, height = validate_roi(image, roi)
    if image.ndim == 2:
        preview = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        preview = image.copy()

    if polygon and len(polygon) >= 3:
        cv2.polylines(
            preview, [np.asarray(polygon, dtype=np.int32)],
            True, (0, 255, 0), max(2, round(min(image.shape[:2]) / 700))
        )
    else:
        cv2.rectangle(
            preview, (x, y), (x + width - 1, y + height - 1),
            (0, 255, 0), max(2, round(min(image.shape[:2]) / 700))
        )
    return preview


def save_roi_result(
    image: np.ndarray,
    roi: Tuple[int, int, int, int],
    output_dir: str | Path = "outputs/roi",
    source_image: Optional[str] = None,
    polygon: Optional[Polygon] = None,
) -> Dict[str, Any]:
    x, y, width, height = validate_roi(image, roi)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    roi_image = crop_roi(image, roi)
    local_mask = np.ones((height, width), dtype=np.uint8) * 255

    if polygon is not None:
        if len(polygon) < 3:
            raise ValueError("Poligon harus memiliki minimal 3 titik.")
        global_points = np.asarray(polygon, dtype=np.int32)
        local_points = global_points - np.array([x, y], dtype=np.int32)
        local_mask[:] = 0
        cv2.fillPoly(local_mask, [local_points], 255)
        if roi_image.ndim == 2:
            roi_image = cv2.bitwise_and(roi_image, roi_image, mask=local_mask)
        else:
            roi_image = cv2.bitwise_and(roi_image, roi_image, mask=local_mask)

    preview = create_roi_preview(image, roi, polygon)
    roi_file = output_path / "carpal_roi.png"
    mask_file = output_path / "carpal_roi_mask.png"
    preview_file = output_path / "roi_preview.png"
    json_file = output_path / "roi_coordinates.json"

    for path, array in (
        (roi_file, roi_image),
        (mask_file, local_mask),
        (preview_file, preview),
    ):
        if not cv2.imwrite(str(path), array):
            raise IOError(f"Gagal menyimpan: {path}")

    metadata = {
        "source_image": source_image,
        "x": x, "y": y, "width": width, "height": height,
        "image_width": int(image.shape[1]),
        "image_height": int(image.shape[0]),
        "roi_file": roi_file.as_posix(),
        "roi_mask_file": mask_file.as_posix(),
        "preview_file": preview_file.as_posix(),
        "selection_type": "polygon" if polygon else "rectangle",
        "polygon_points_global": polygon or [],
        "coordinate_convention": "pixel; origin top-left; x rightward; y downward",
    }
    json_file.write_text(
        json.dumps(metadata, indent=4, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "roi_image": roi_image,
        "roi_mask": local_mask,
        "preview_image": preview,
        "metadata": metadata,
        "roi_path": roi_file,
        "mask_path": mask_file,
        "preview_path": preview_file,
        "metadata_path": json_file,
    }
