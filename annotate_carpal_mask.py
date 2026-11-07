"""
Buat mask manual area tulang karpal dengan menggambar polygon.

Jalankan:
python annotate_carpal_mask.py "outputs/roi/carpal_roi.png"

Petunjuk:
- Klik titik-titik mengelilingi satu tulang karpal.
- Tekan N untuk menyelesaikan polygon dan mulai polygon berikutnya.
- Ulangi untuk tulang karpal lain.
- Tekan S untuk menyimpan mask.
- Tekan R untuk mengulang seluruh anotasi.
- Tekan ESC untuk keluar tanpa menyimpan.

Gambar mask hanya alat anotasi awal; periksa hasilnya bersama pembimbing/ahli.
"""
import argparse
from pathlib import Path
import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--output", default="outputs/roi/carpal_bone_mask.png")
    args = parser.parse_args()

    path = Path(args.image)
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit(f"Gagal membaca citra: {path}")

    polygons = []
    current = []

    def render():
        canvas = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        for polygon in polygons:
            pts = np.array(polygon, dtype=np.int32)
            cv2.polylines(canvas, [pts], True, (0, 255, 0), 2)
        if current:
            pts = np.array(current, dtype=np.int32)
            for point in current:
                cv2.circle(canvas, point, 3, (0, 0, 255), -1)
            if len(current) > 1:
                cv2.polylines(canvas, [pts], False, (0, 0, 255), 2)
        cv2.putText(canvas, "Click points | N: next polygon | S: save | R: reset | ESC: quit",
                    (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA)
        return canvas

    def on_mouse(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONDOWN:
            current.append((x, y))

    window = "Annotasi mask tulang karpal - OSSIA"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, on_mouse)

    while True:
        cv2.imshow(window, render())
        key = cv2.waitKey(20) & 0xFF
        if key == 27:
            break
        elif key in (ord("n"), ord("N")):
            if len(current) >= 3:
                polygons.append(current.copy())
            current.clear()
        elif key in (ord("r"), ord("R")):
            polygons.clear()
            current.clear()
        elif key in (ord("s"), ord("S")):
            if len(current) >= 3:
                polygons.append(current.copy())
                current.clear()
            if not polygons:
                print("Belum ada polygon valid.")
                continue
            mask = np.zeros(image.shape, dtype=np.uint8)
            for polygon in polygons:
                cv2.fillPoly(mask, [np.array(polygon, dtype=np.int32)], 255)
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output), mask)
            print(f"Mask karpal tersimpan: {output}")
            print(f"Area mask: {np.count_nonzero(mask)} piksel")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
