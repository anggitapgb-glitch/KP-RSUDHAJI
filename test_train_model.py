import os
import cv2
import numpy as np
from ml.growth_assessment import assess_growth

# 1. Tentukan path sampel gambar X-ray (Target: 1408.png - aktual 126 bulan)
SAMPLE_IMAGE_PATH = "dataset_training/images/images/1487.png"

def main():
    print(f"Memuat sampel gambar dari: {SAMPLE_IMAGE_PATH}")
    image = cv2.imread(SAMPLE_IMAGE_PATH, cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise SystemExit("Gagal memuat gambar! Pastikan path file sudah benar.")
        
    print("Berhasil memuat gambar. Mengekstrak fitur dengan Otsu mandiri...")
    
    height, width = image.shape
    
    # 2. Pemotongan ROI (Fokus ke area tulang karpal)
    roi = image[int(height*0.48):int(height*0.83), int(width*0.22):int(width*0.78)]
    if roi.size == 0:
        raise SystemExit("Gagal memotong ROI.")
    
    # 3. Preprocessing & Otsu Thresholding (Bebas dari error Canny)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(roi)
    denoised = cv2.GaussianBlur(enhanced, (5, 5), 0)
    _, mask = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 4. Hitung Rasio Osifikasi (Blok area utuh, bukan cuma garis tepi)
    ratio = float(cv2.countNonZero(mask) / mask.size)
    print(f"Nilai Foreground Ratio: {ratio:.4f}")
    
    # 5. Hitung Estimasi Usia Tulang (Regresi Derajat 2)
    # --- PENTING: GANTI ANGKA 0.0 DI BAWAH INI DENGAN HASIL DARI train_model.py ---
    intercept = 16.3313
    coef_1 = 494.4149
    coef_2 = -528.8530
    
    estimated_age_months = intercept + (coef_1 * ratio) + (coef_2 * (ratio ** 2))
    estimated_age_years = estimated_age_months / 12
    
    print("\n--- HASIL ESTIMASI MODEL ---")
    print(f"Estimasi Usia Tulang : {estimated_age_years:.1f} Tahun ({max(0, int(estimated_age_months))} Bulan)")
    print("Status Pengujian     : BERHASIL ✔")

    # Simulasi Usia Kronologis (Misal pasien umurnya 10 tahun / 120 bulan)
    usia_asli_pasien = 120 
    
    # Panggil modul penilaian pertumbuhan
    hasil_klinis = assess_growth(estimated_age_months, usia_asli_pasien)
    
    print(f"\n--- PENILAIAN KLINIS PERTUMBUHAN ---")
    print(f"Usia Asli Pasien  : {usia_asli_pasien / 12:.1f} Tahun ({usia_asli_pasien} Bulan)")
    print(f"Selisih           : {hasil_klinis['selisih_bulan']:.1f} Bulan")
    print(f"Kriteria          : {hasil_klinis['kriteria']}")
    print(f"Penjelasan        : {hasil_klinis['penjelasan']}")
if __name__ == "__main__":
    main()