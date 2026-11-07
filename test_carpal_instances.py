"""Pengujian segmentasi baseline OSSIA pada ROI karpal.

Jalankan dari root project:
python test_carpal_instances.py "outputs/roi/carpal_roi.png"

Opsi:
--polarity bright|dark|auto
--output outputs/carpal_instances
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from ml.carpal_instances import segment_carpal_bones_and_ossification, save_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Uji baseline segmentasi area karpal OSSIA."
    )
    parser.add_argument("image", help="Path citra ROI karpal grayscale")
    parser.add_argument("--output", default="outputs/carpal_instances")
    parser.add_argument("--polarity", choices=["bright", "dark", "auto"], default="auto")
    parser.add_argument("--bone-percentile", type=float, default=42.0,
                        help="Argumen kompatibilitas versi lama; tidak digunakan pada Otsu.")
    parser.add_argument("--ossification-percentile", type=float, default=72.0)
    parser.add_argument("--bottom-fraction", type=float, default=1.0,
                        help="Batas bawah ROI analisis (fraksi tinggi citra).")
    parser.add_argument("--top-fraction", type=float, default=0.0,
                        help="Batas atas ROI analisis (fraksi tinggi citra).")
    parser.add_argument("--min-area", type=int, default=30)
    parser.add_argument("--close-kernel", type=int, default=3)
    parser.add_argument("--max-instances", type=int, default=8)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        raise SystemExit(f"File tidak ditemukan: {image_path}")

    image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise SystemExit(f"Gagal membaca citra: {image_path}")

    try:
        result = segment_carpal_bones_and_ossification(
            image,
            roi_top_fraction=args.top_fraction,
            roi_bottom_fraction=args.bottom_fraction,
            bone_percentile=args.bone_percentile,
            ossification_percentile=args.ossification_percentile,
            close_kernel=args.close_kernel,
            min_bone_area=args.min_area,
            min_instance_area=args.min_area,
            max_instances=args.max_instances,
            polarity=args.polarity,
        )
    except (ValueError, cv2.error) as exc:
        raise SystemExit(f"SEGMENTASI GAGAL: {exc}") from exc

    paths = save_results(result, args.output)
    summary = result["summary"]

    print("\nBASELINE SEGMENTASI OSSIA SELESAI")
    print(f"Ukuran ROI: {image.shape[1]} x {image.shape[0]}")
    print(f"Polaritas terpilih: {summary['selected_polarity']}")
    print(f"Threshold Otsu: {summary['otsu_threshold']}")
    print(f"Komponen algoritmik: {summary['detected_instances']}")
    print(f"Luas mask kandidat: {summary['total_bone_area_px']} px")
    print(f"Luas kandidat intensitas tinggi: {summary['total_candidate_ossification_area_px']} px")
    print(f"Rasio kandidat intensitas: {summary['total_candidate_ratio_percent']}%")
    print("\nCatatan per komponen:")
    for row in result["per_bone"]:
        print(
            f"  Komponen {row['instance_id']}: "
            f"area={row['bone_area_px']} px | "
            f"kandidat={row['candidate_ossification_area_px']} px | "
            f"rasio intensitas={row['candidate_ratio_percent']}%"
        )

    print("\nFile hasil:")
    for name, path in paths.items():
        print(f"  {name}: {path}")

    print("\nPERINGATAN:")
    for warning in result["warnings"]:
        print(f"  - {warning}")

    if args.show:
        for name in (
            "04_total_bone_mask.png",
            "05_bone_overlay.png",
            "06_instance_overlay.png",
            "07_ossification_candidate_mask.png",
            "08_ossification_overlay.png",
        ):
            view = cv2.imread(str(Path(args.output) / name), cv2.IMREAD_UNCHANGED)
            if view is not None:
                cv2.imshow(name, view)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
