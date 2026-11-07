"""Tes sederhana preprocessing citra OSSIA.

Jalankan:
python test_preprocessing.py "samples/xray/contoh.png"
"""

import sys
from pathlib import Path

import cv2

from ml.preprocessing import preprocess_xray


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            'Gunakan: python test_preprocessing.py "samples/xray/contoh.png"'
        )

    image_path = Path(sys.argv[1])
    if not image_path.is_file():
        raise SystemExit(f"File tidak ditemukan: {image_path}")

    image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise SystemExit("Gambar tidak dapat dibaca oleh OpenCV.")

    result = preprocess_xray(
        image,
        use_clahe=True,
        use_median=False,
        use_gaussian=False,
    )

    output_dir = Path("outputs/preprocessing")
    output_dir.mkdir(parents=True, exist_ok=True)

    stages = {
        "01_gray.png": result["gray_image"],
        "02_normalized.png": result["normalized_image"],
        "03_preprocessed.png": result["preprocessed_image"],
    }

    if result["clahe_image"] is not None:
        stages["04_clahe.png"] = result["clahe_image"]
    if result["median_image"] is not None:
        stages["05_median.png"] = result["median_image"]
    if result["gaussian_image"] is not None:
        stages["06_gaussian.png"] = result["gaussian_image"]

    for filename, output_image in stages.items():
        cv2.imwrite(str(output_dir / filename), output_image)

    print("PREPROCESSING BERHASIL")
    print(f"Resolusi : {result['metadata']['width']} x {result['metadata']['height']}")
    print(f"Datatype : {result['metadata']['dtype']}")
    print(
        "Rentang intensitas : "
        f"{result['metadata']['min_intensity']} - "
        f"{result['metadata']['max_intensity']}"
    )
    print(f"CLAHE    : {'Aktif' if result['metadata']['clahe_enabled'] else 'Nonaktif'}")
    print(f"Median   : {'Aktif' if result['metadata']['median_enabled'] else 'Nonaktif'}")
    print(f"Gaussian : {'Aktif' if result['metadata']['gaussian_enabled'] else 'Nonaktif'}")
    print(f"Hasil disimpan di: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
