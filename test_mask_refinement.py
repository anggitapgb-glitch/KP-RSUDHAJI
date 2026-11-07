"""
Uji refinement beberapa kombinasi parameter pada semua mask threshold.

Jalankan:
python test_mask_refinement.py "outputs/roi/carpal_roi.png"

Output:
outputs/refinement/<metode>_<varian>/
"""

import argparse
from pathlib import Path
import cv2

from ml.segmentation import segment_roi
from ml.mask_refinement import refine_mask, save_refinement_results


def main():
    parser = argparse.ArgumentParser(description="Optimasi eksploratif mask OSSIA")
    parser.add_argument("image", help="Path carpal_roi.png")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        raise SystemExit(f"File tidak ditemukan: {image_path}")
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit("Gambar ROI tidak dapat dibaca.")

    # Kandidat parameter kecil agar detail anatomi tidak langsung terkikis.
    denoise_options = ["none", "median", "bilateral"]
    block_options = [21, 31, 41]
    c_options = [3, 5, 7]
    morphology_options = [("none", 1), ("open", 3), ("close", 3)]
    min_areas = [5, 12, 25]

    out_root = Path("outputs/refinement")
    out_root.mkdir(parents=True, exist_ok=True)
    records = []

    for denoise in denoise_options:
        for block in block_options:
            for c_value in c_options:
                segmentation = segment_roi(
                    image,
                    denoise=denoise,
                    denoise_strength=3,
                    invert=False,
                    adaptive_block_size=block,
                    adaptive_c=c_value,
                )
                for method, mask in segmentation["masks"].items():
                    # Refinement kandidat untuk perbandingan; tidak mengasumsikan satu terbaik.
                    for morph, kernel in morphology_options:
                        for min_area in min_areas:
                            result = refine_mask(
                                mask,
                                min_component_area=min_area,
                                morphology=morph,
                                kernel_size=kernel,
                                iterations=1,
                            )
                            key = f"{denoise}_{method}_b{block}_c{c_value}_{morph}_a{min_area}"
                            target = out_root / key
                            target.mkdir(parents=True, exist_ok=True)
                            save_refinement_results(image, result, target)

                            records.append({
                                "variant": key,
                                "denoise": denoise,
                                "method": method,
                                "block_size": block,
                                "c_value": c_value,
                                "morphology": morph,
                                "min_component_area": min_area,
                                **result["summary"],
                                "components": result["component_count"],
                            })

    csv_path = out_root / "parameter_comparison.csv"
    columns = list(records[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        import csv
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

    print("EVALUASI PARAMETER SELESAI")
    print(f"Jumlah variasi: {len(records)}")
    print(f"File perbandingan: {csv_path}")
    print(f"Folder hasil: {out_root.resolve()}")
    print(
        "PENTING: daftar variasi ini adalah pencarian parameter eksploratif. "
        "CSV tidak memberi peringkat akurasi anatomis karena belum ada ground-truth mask."
    )


if __name__ == "__main__":
    main()
