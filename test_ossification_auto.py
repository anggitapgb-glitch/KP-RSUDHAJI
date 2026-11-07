"""
Uji pipeline otomatis dari ROI karpal (tanpa menggambar mask manual).

Jalankan:
python test_ossification_auto.py "outputs/roi/carpal_roi.png"

Opsional:
python test_ossification_auto.py "outputs/roi/carpal_roi.png" --region-percentile 55 --candidate-percentile 75
"""
import argparse
from pathlib import Path
import cv2
from ml.auto_ossification import (
    automatic_carpal_region_mask, segment_bright_candidates, save_auto_results
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("roi")
    parser.add_argument("--region-percentile", type=float, default=58.0)
    parser.add_argument("--candidate-percentile", type=float, default=72.0)
    parser.add_argument("--min-area", type=int, default=3)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    image = cv2.imread(str(Path(args.roi)), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit(f"ROI tidak terbaca: {args.roi}")

    region = automatic_carpal_region_mask(
        image, threshold_percentile=args.region_percentile
    )
    candidates = segment_bright_candidates(
        image, region["carpal_region_mask"],
        percentile=args.candidate_percentile,
        min_component_area=args.min_area,
    )
    paths = save_auto_results(region, candidates)

    print("\nPIPELINE OTOMATIS SELESAI")
    print(f"Threshold wilayah: {region['threshold']:.2f}")
    print(f"Statistik wilayah: {region['statistics']}")
    print(f"Threshold kandidat: {candidates['threshold']:.2f}")
    print(f"Statistik kandidat: {candidates['statistics']}")
    print("\nFile hasil:")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print("\nPERINGATAN:")
    for warning in region["warnings"]:
        print(f"- {warning}")
    print("- Kandidat intensitas terang bukan label osifikasi klinis tervalidasi.")

    if args.show:
        for name, path in paths.items():
            view = cv2.imread(path)
            cv2.imshow(name, view)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
