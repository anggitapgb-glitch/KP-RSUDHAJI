# OSSIA – Segmentasi Instance Tulang Karpal dan Kandidat Osifikasi

## Tujuan
Baseline pengolahan citra untuk:
1. membuat mask kasar area tulang dalam ROI karpal;
2. memisahkan komponen yang menyatu menggunakan distance transform + watershed;
3. mengestimasi kandidat piksel radiopak di setiap instance;
4. menghitung luas kandidat per instance dan gabungan.

## Batasan ilmiah
- `Instance 1..N` adalah label algoritmik, BUKAN nama anatomi (scaphoid, lunate, triquetrum, pisiform, trapezium, trapezoid, capitate, hamate).
- Mask tulang dan kandidat osifikasi masih berbasis intensitas/morfologi, bukan segmentasi anatomi tervalidasi.
- Rasio yang dihasilkan adalah rasio kandidat piksel terhadap mask tulang hasil algoritma; jangan disebut rasio osifikasi klinis sebelum definisi operasional dan ground truth disepakati.
- Untuk validasi, perlu anotasi ahli/radiolog pada citra yang sama, lalu evaluasi Dice, IoU, sensitivitas, dan presisi. Pastikan data citra memiliki izin penggunaan.

## Instalasi
Dari folder utama project:
```bash
pip install opencv-python numpy
```

## Jalankan
```bash
python test_carpal_instances.py "outputs/roi/carpal_roi.png"
```
atau gunakan ROI lain:
```bash
python test_carpal_instances.py "samples/xray/contoh.png" --output outputs/uji_carpal
```

## Parameter eksplorasi
```bash
python test_carpal_instances.py "outputs/roi/carpal_roi.png" --bone-percentile 40 --ossification-percentile 70 --bottom-fraction 0.86 --min-seed-distance 22
```
- `--bone-percentile`: ambang awal mask tulang. Lebih rendah menghasilkan mask lebih luas.
- `--ossification-percentile`: ambang kandidat intensitas dalam tiap instance. Lebih rendah menghasilkan kandidat lebih luas.
- `--bottom-fraction`: batas bawah analisis ROI. Atur agar radius/ulna tidak ikut.
- `--min-seed-distance`: jarak minimum antar seed watershed; naikkan untuk mengurangi pemecahan berlebih.
- `--max-instances`: batas jumlah label yang dipertahankan.

## Output
`outputs/carpal_instances/`
- `01_enhanced.png`
- `02_analysis_window.png`
- `03_total_bone_mask.png`
- `04_instance_labels.png`
- `05_ossification_candidate_mask.png`
- `06_ossification_overlay.png`
- `per_bone_measurements.csv`
- `summary.json`

## Catatan integrasi
Modul ini belum mengubah `app.py`, `home.js`, atau antarmuka OSSIA. Jalankan sebagai pengujian mandiri dahulu.
