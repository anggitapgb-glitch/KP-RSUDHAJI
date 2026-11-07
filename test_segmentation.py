"""Uji deteksi tepi konservatif pada ROI karpal."""
import argparse
from pathlib import Path
import cv2
from ml.segmentation import segment_roi, save_segmentation_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--low", type=int, default=60)
    parser.add_argument("--high", type=int, default=150)
    parser.add_argument("--min-fragment", type=int, default=22)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    path = Path(args.image)
    if not path.is_file():
        raise SystemExit(f"File tidak ditemukan: {path}")
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit("Citra tidak dapat dibaca.")

    result = segment_roi(
        image,
        canny_low=args.low,
        canny_high=args.high,
        min_component_pixels=args.min_fragment,
    )
    saved = save_segmentation_results(image, result)

    print(f"ROI: {image.shape[1]} x {image.shape[0]}")
    print("Tepi mentah :", result["raw_summary"])
    print("Tepi bersih :", result["summary"])
    print("Pengaturan  :", result["settings"])
    print("Catatan     :", result["warning"])
    print("\\nFile hasil:")
    for key, value in saved.items():
        print(f"{key}: {value}")

    if args.show:
        cv2.imshow("Input ROI", result["gray_image"])
        cv2.imshow("Filtered stronger", result["filtered_image"])
        cv2.imshow("Canny raw", result["raw_edges"])
        cv2.imshow("Canny clean candidate", result["edges"])
        cv2.imshow("Clean edge overlay", result["overlay"])
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
