"""
Pengujian pemilihan ROI poligon OSSIA.

Jalankan dari root project:
python test_roi_detection.py "outputs/preprocessing/03_preprocessed.png"

Cara memilih:
- Klik kiri beberapa titik mengelilingi kumpulan tulang karpal.
- Jangan masukkan radius/ulna sebanyak mungkin.
- ENTER/SPACE: selesai.
- BACKSPACE: hapus titik terakhir.
- R: ulangi pemilihan.
- ESC: batalkan.
"""

import sys
from pathlib import Path

from ml.roi_detection import (
    load_grayscale_image,
    select_carpal_roi_interactively,
    save_roi_result,
)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            'Gunakan: python test_roi_detection.py "outputs/preprocessing/03_preprocessed.png"'
        )

    image_path = Path(sys.argv[1])
    image = load_grayscale_image(image_path)

    print("Citra berhasil dibaca.")
    print(f"Resolusi: {image.shape[1]} x {image.shape[0]}")
    print("Tandai poligon yang mengelilingi kumpulan tulang karpal.")
    print("Usahakan tidak memasukkan radius dan ulna.")

    roi, polygon = select_carpal_roi_interactively(image)
    result = save_roi_result(
        image,
        roi,
        output_dir="outputs/roi",
        source_image=str(image_path),
        polygon=polygon,
    )

    metadata = result["metadata"]
    print("\nROI POLIGON BERHASIL DISIMPAN")
    print(f"Koordinat bounding box : x={metadata['x']}, y={metadata['y']}")
    print(f"Ukuran ROI             : {metadata['width']} x {metadata['height']}")
    print(f"Jumlah titik poligon   : {len(polygon)}")
    print(f"Citra ROI              : {result['roi_path']}")
    print(f"Mask ROI               : {result['mask_path']}")
    print(f"Preview                : {result['preview_path']}")
    print(f"Koordinat JSON         : {result['metadata_path']}")
    print("\nCatatan: area di luar poligon pada carpal_roi.png dibuat hitam.")


if __name__ == "__main__":
    main()
