"""
OSSIA - segmentasi eksploratif area karpal untuk citra X-ray tangan anak.

Metode:
- ROI karpal dipilih sebelumnya (manual/semi-manual).
- CLAHE opsional untuk kontras lokal.
- Otsu dihitung pada ROI, dengan dua polaritas kandidat.
- Filter komponen berdasarkan ukuran dan batas area.
- Kandidat radiopak dihitung hanya di dalam mask wilayah hasil segmentasi.

PENTING:
RSNA Pediatric Bone Age menyediakan label usia tulang, bukan ground-truth
pixel mask. Keluaran modul ini adalah baseline image processing, bukan
segmentasi anatomi/osisfikasi tervalidasi. Jangan menyebut label komponen
sebagai nama tulang karpal dan jangan memakai rasio sebagai hasil klinis.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import json

import cv2
import numpy as np


def _to_gray_u8(image: np.ndarray) -> np.ndarray:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Citra kosong atau tidak valid.")

    if image.ndim == 3:
        if image.shape[2] == 1:
            image = image[:, :, 0]
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError("Jumlah channel citra tidak didukung.")
    elif image.ndim != 2:
        raise ValueError("Citra harus grayscale, BGR, atau BGRA.")

    if not np.issubdtype(image.dtype, np.number):
        raise ValueError("Datatype citra harus numerik.")

    data = np.nan_to_num(image.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    lo, hi = float(data.min()), float(data.max())
    if hi <= lo:
        raise ValueError("Citra memiliki intensitas konstan.")
    if image.dtype == np.uint8:
        return image.copy()
    return np.clip((data - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)


def _validate_fraction(name: str, value: float) -> None:
    if not 0.0 < float(value) <= 1.0:
        raise ValueError(f"{name} harus berada pada rentang (0, 1].")


def _component_filter(
    binary: np.ndarray,
    *,
    min_area: int,
    max_area_fraction: float,
    max_components: int,
) -> tuple[np.ndarray, list[dict[str, int]]]:
    if min_area < 1 or max_components < 1:
        raise ValueError("min_area dan max_components harus minimal 1.")
    if not 0 < max_area_fraction <= 1:
        raise ValueError("max_area_fraction harus berada pada rentang (0, 1].")

    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (binary > 0).astype(np.uint8), connectivity=8
    )
    image_area = binary.shape[0] * binary.shape[1]
    max_area = int(round(image_area * max_area_fraction))
    candidates = []
    for label in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[label])
        if min_area <= area <= max_area:
            candidates.append((area, label, x, y, w, h))

    candidates.sort(key=lambda item: item[0], reverse=True)
    output = np.zeros_like(binary, dtype=np.uint8)
    details: list[dict[str, int]] = []
    for instance_id, (area, label, x, y, w, h) in enumerate(
        candidates[:max_components], start=1
    ):
        output[labels == label] = 255
        details.append({
            "component_id": instance_id,
            "area_px": area,
            "x": x, "y": y, "width": w, "height": h,
        })
    return output, details


def _make_overlay(gray: np.ndarray, mask: np.ndarray, color=(0, 255, 0),
                  alpha: float = 0.35) -> np.ndarray:
    base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    tint = base.copy()
    tint[mask > 0] = color
    return cv2.addWeighted(base, 1.0 - alpha, tint, alpha, 0)


def segment_carpal_bones_and_ossification(
    image: np.ndarray,
    *,
    roi_top_fraction: float = 0.0,
    roi_bottom_fraction: float = 1.0,
    bone_percentile: float = 42.0,  # retained for backward compatibility; not used
    ossification_percentile: float = 72.0,
    close_kernel: int = 3,
    min_bone_area: int = 30,
    min_instance_area: int = 30,  # retained for backward compatibility
    min_seed_distance: int = 22,  # retained for backward compatibility
    max_instances: int = 8,
    clahe_clip: float = 1.5,
    use_clahe: bool = True,
    polarity: str = "bright",
    min_foreground_fraction: float = 0.005,
    max_foreground_fraction: float = 0.70,
) -> dict[str, Any]:
    """
    Segmentasi baseline pada ROI yang sudah dicrop ke area karpal.

    polarity:
      - "bright": piksel di atas threshold Otsu menjadi foreground.
      - "dark": piksel di bawah/sama dengan threshold menjadi foreground.
      - "auto": memilih polaritas dengan fraksi foreground yang memenuhi batas.

    Perlu diperhatikan: auto hanya memilih berdasarkan batas fraksi area,
    bukan mengenali anatomi. `bone_percentile`, `min_instance_area`, dan
    `min_seed_distance` diterima agar pemanggil versi lama tidak langsung rusak.
    """
    gray = _to_gray_u8(image)
    h, w = gray.shape

    if not (0 <= roi_top_fraction < roi_bottom_fraction <= 1):
        raise ValueError("Batas ROI vertikal tidak valid.")
    if close_kernel < 1 or close_kernel % 2 == 0:
        raise ValueError("close_kernel harus ganjil positif.")
    if not 0 < ossification_percentile < 100:
        raise ValueError("ossification_percentile harus antara 0 dan 100.")
    if polarity not in {"bright", "dark", "auto"}:
        raise ValueError("polarity harus bright, dark, atau auto.")
    if not 0 < min_foreground_fraction < max_foreground_fraction < 1:
        raise ValueError("Batas foreground fraction tidak valid.")
    if clahe_clip <= 0:
        raise ValueError("clahe_clip harus lebih besar dari 0.")

    y0 = int(round(h * roi_top_fraction))
    y1 = int(round(h * roi_bottom_fraction))
    analysis = np.zeros((h, w), dtype=np.uint8)
    analysis[y0:y1, :] = 255

    crop = gray[y0:y1, :]
    if crop.size < 32 or min(crop.shape) < 3:
        raise ValueError("ROI analisis terlalu kecil.")

    filtered = cv2.bilateralFilter(crop, d=5, sigmaColor=25, sigmaSpace=25)
    enhanced_crop = (
        cv2.createCLAHE(clipLimit=float(clahe_clip), tileGridSize=(8, 8)).apply(filtered)
        if use_clahe else filtered
    )
    enhanced = gray.copy()
    enhanced[y0:y1, :] = enhanced_crop

    # Otsu hanya dihitung pada crop ROI, bukan pada area di luar ROI.
    threshold, bright_crop = cv2.threshold(
        enhanced_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    _, dark_crop = cv2.threshold(
        enhanced_crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    def fraction(mask_crop: np.ndarray) -> float:
        return float(np.count_nonzero(mask_crop) / mask_crop.size)

    bright_fraction = fraction(bright_crop)
    dark_fraction = fraction(dark_crop)

    if polarity == "bright":
        chosen = bright_crop
        chosen_polarity = "bright"
    elif polarity == "dark":
        chosen = dark_crop
        chosen_polarity = "dark"
    else:
        options = [
            (bright_fraction, "bright", bright_crop),
            (dark_fraction, "dark", dark_crop),
        ]
        valid = [x for x in options
                 if min_foreground_fraction <= x[0] <= max_foreground_fraction]
        if not valid:
            chosen = min(options, key=lambda x: abs(x[0] - 0.15))[2]
            chosen_polarity = min(options, key=lambda x: abs(x[0] - 0.15))[1]
        else:
            # Prefer mask yang lebih kecil bila keduanya valid untuk mengurangi
            # kecenderungan background menjadi foreground.
            chosen_fraction, chosen_polarity, chosen = min(valid, key=lambda x: x[0])

    # Hindari closing besar yang dapat menyatukan tulang berbeda.
    raw = np.zeros((h, w), dtype=np.uint8)
    raw[y0:y1, :] = chosen
    if close_kernel > 1:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (close_kernel, close_kernel)
        )
        raw = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, kernel, iterations=1)
    raw[analysis == 0] = 0

    bone_mask, components = _component_filter(
        raw,
        min_area=min_bone_area,
        max_area_fraction=max_foreground_fraction,
        max_components=max_instances,
    )
    bone_mask[analysis == 0] = 0

    # Label komponen yang lolos filter. Bukan label anatomis tulang.
    n_labels, labels = cv2.connectedComponents(
        (bone_mask > 0).astype(np.uint8), connectivity=8
    )
    labels = labels.astype(np.int32)
    detected = max(0, n_labels - 1)

    # Kandidat intensitas radiopak hanya dihitung di dalam mask.
    values = enhanced[bone_mask > 0]
    candidate_mask = np.zeros_like(gray, dtype=np.uint8)
    per_bone: list[dict[str, Any]] = []
    if values.size:
        # Threshold global dalam mask agar rasio per komponen memakai ambang sama.
        oss_thr = float(np.percentile(values, ossification_percentile))
        candidate_mask[(enhanced >= oss_thr) & (bone_mask > 0)] = 255
        for component_id in range(1, n_labels):
            region = labels == component_id
            bone_area = int(np.count_nonzero(region))
            oss_area = int(np.count_nonzero((candidate_mask > 0) & region))
            per_bone.append({
                "instance_id": component_id,
                "bone_area_px": bone_area,
                "candidate_ossification_area_px": oss_area,
                "candidate_ratio_percent": round(100.0 * oss_area / bone_area, 3)
                    if bone_area else 0.0,
                "label_type": "algorithmic_component_not_anatomical_name",
            })

    total_bone = int(np.count_nonzero(bone_mask))
    total_candidate = int(np.count_nonzero(candidate_mask))
    total_ratio = 100.0 * total_candidate / total_bone if total_bone else 0.0

    warnings = [
        "RSNA menyediakan label usia tulang, bukan ground-truth mask segmentasi piksel.",
        "Komponen bernomor adalah komponen algoritmik, bukan identitas tulang karpal.",
        "Mask Otsu dan kandidat intensitas bukan anotasi anatomi atau pusat osifikasi tervalidasi.",
        "Rasio kandidat hanya deskripsi intensitas dalam mask; bukan rasio osifikasi klinis.",
    ]
    if total_bone == 0:
        warnings.append("Tidak ada komponen yang lolos filter; periksa ROI dan polaritas.")
    elif total_bone / float(analysis.sum() / 255) < min_foreground_fraction:
        warnings.append("Foreground sangat kecil dibanding area analisis; kemungkinan under-segmentation.")
    if total_bone / float(analysis.sum() / 255) > max_foreground_fraction:
        warnings.append("Foreground terlalu luas; kemungkinan background/struktur lain ikut tersegmentasi.")
    if detected != 8:
        warnings.append(
            f"Terdeteksi {detected} komponen; jumlah ini tidak boleh ditafsirkan sebagai jumlah tulang karpal."
        )

    # Rebuild overlay dan image labels for visual inspection.
    instance_overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    palette = [
        (255, 120, 50), (50, 200, 255), (120, 255, 80), (220, 80, 220),
        (50, 220, 180), (180, 180, 50), (80, 120, 255), (200, 100, 100),
    ]
    color_layer = np.zeros_like(instance_overlay)
    for component_id in range(1, n_labels):
        color_layer[labels == component_id] = palette[(component_id - 1) % len(palette)]
    instance_overlay = cv2.addWeighted(instance_overlay, 0.60, color_layer, 0.40, 0)

    oss_overlay = _make_overlay(gray, candidate_mask, color=(0, 0, 255), alpha=0.40)
    bone_overlay = _make_overlay(gray, bone_mask, color=(0, 255, 0), alpha=0.35)

    summary = {
        "detected_instances": detected,
        "total_bone_area_px": total_bone,
        "total_candidate_ossification_area_px": total_candidate,
        "total_candidate_ratio_percent": round(total_ratio, 3),
        "otsu_threshold": round(float(threshold), 3),
        "selected_polarity": chosen_polarity,
        "bright_foreground_fraction": round(bright_fraction, 6),
        "dark_foreground_fraction": round(dark_fraction, 6),
        "bone_foreground_fraction_of_analysis": round(
            total_bone / max(1, int(np.count_nonzero(analysis))), 6
        ),
    }

    return {
        "gray_image": gray,
        "enhanced_image": enhanced,
        "analysis_window_mask": analysis,
        "threshold_mask": raw,
        "bone_mask": bone_mask,
        "instance_labels": labels,
        "instance_overlay": instance_overlay,
        "bone_overlay": bone_overlay,
        "ossification_candidate_mask": candidate_mask,
        "ossification_overlay": oss_overlay,
        "per_bone": per_bone,
        "summary": summary,
        "warnings": warnings,
        "settings": {
            "polarity": polarity,
            "selected_polarity": chosen_polarity,
            "min_bone_area": min_bone_area,
            "max_instances": max_instances,
            "ossification_percentile": ossification_percentile,
            "close_kernel": close_kernel,
            "use_clahe": use_clahe,
        },
    }


def save_results(
    result: dict[str, Any],
    output_dir: str | Path = "outputs/carpal_instances",
) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    images = {
        "01_enhanced.png": result["enhanced_image"],
        "02_analysis_window.png": result["analysis_window_mask"],
        "03_threshold_candidate.png": result["threshold_mask"],
        "04_total_bone_mask.png": result["bone_mask"],
        "05_bone_overlay.png": result["bone_overlay"],
        "06_instance_overlay.png": result["instance_overlay"],
        "07_ossification_candidate_mask.png": result["ossification_candidate_mask"],
        "08_ossification_overlay.png": result["ossification_overlay"],
    }
    paths: dict[str, str] = {}
    for filename, array in images.items():
        path = out / filename
        if not cv2.imwrite(str(path), array):
            raise IOError(f"Gagal menyimpan gambar: {path}")
        paths[filename] = str(path)

    csv_path = out / "per_component_measurements.csv"
    fields = [
        "instance_id", "bone_area_px",
        "candidate_ossification_area_px", "candidate_ratio_percent", "label_type",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["per_bone"])
    paths[csv_path.name] = str(csv_path)

    summary_path = out / "summary.json"
    summary_path.write_text(
        json.dumps(
            {"summary": result["summary"], "settings": result["settings"],
             "warnings": result["warnings"]},
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    paths[summary_path.name] = str(summary_path)
    return paths
