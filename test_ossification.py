"""
Uji kandidat area osifikasi di dalam mask tulang karpal.

1) Buat mask karpal terlebih dahulu:
python annotate_carpal_mask.py "outputs/roi/carpal_roi.png"

2) Jalankan:
python test_ossification.py "outputs/roi/carpal_roi.png" "outputs/roi/carpal_bone_mask.png"
"""
import argparse
from pathlib import Path
import cv2
from ml.ossification_segmentation import (
    segment_ossification_candidates, save_ossification_results
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("roi")
    parser.add_argument("bone_mask")
    parser.add_argument("--method", choices=["percentile", "otsu"], default="percentile")
    parser.add_argument("--percentile", type=float, default=70.0)
    parser.add_argument("--min-area", type=int, default=3)
    parser.add_argument("--morphology", choices=["none", "open", "close"], default="none")
    parser.add_argument("--dark-foreground", action="store_true")
    args = parser.parse_args()

    roi_path, mask_path = Path(args.roi), Path(args.bone_mask)
    roi = cv2.imread(str(roi_path), cv2.IMREAD_GRAYSCALE)
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if roi is None:
        raise SystemExit(f"ROI tidak terbaca: {roi_path}")
    if mask is None:
        raise SystemExit(f"Mask karpal tidak terbaca: {mask_path}")

    result = segment_ossification_candidates(
        roi, mask,
        method=args.method,
        percentile=args.percentile,
        bright_foreground=not args.dark_foreground,
        min_component_area=args.min_area,
        morphology=args.morphology,
    )
    saved = save_ossification_results(result)
    print("\nKANDIDAT SEGMENTASI OSIFIKASI SELESAI")
    print(f"Metode: {result['method']}")
    print(f"Threshold: {result['threshold']:.2f}")
    for key, value in result["statistics"].items():
        print(f"{key}: {value}")
    print("\nFile hasil:")
    for name, path in saved.items():
        print(f"{name}: {path}")
    print(
        "\nPERINGATAN: kandidat berbasis intensitas bukan segmentasi osifikasi "
        "yang tervalidasi. Tinjau mask karpal dan kandidat dengan anotasi referensi."
    )


if __name__ == "__main__":
    main()
