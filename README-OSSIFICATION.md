# OSSIA - Kandidat Segmentasi Area Osifikasi Karpal

## Tujuan
Modul ini membatasi analisis intensitas pada mask area tulang karpal, kemudian
menghasilkan kandidat area radiopak/intensitas tinggi. Ini lebih sesuai dengan
target eksplorasi daripada thresholding seluruh ROI, tetapi belum menjadi
segmentasi osifikasi anatomis yang tervalidasi.

## File baru
- `ml/ossification_segmentation.py`
- `annotate_carpal_mask.py`
- `test_ossification.py`

## Instalasi
```bash
pip install opencv-python numpy
```

## Langkah 1: buat mask area tulang karpal
```bash
python annotate_carpal_mask.py "outputs/roi/carpal_roi.png"
```
Klik titik-titik polygon mengelilingi setiap tulang karpal yang tampak. Tekan
`N` untuk polygon berikutnya. Setelah semua selesai, tekan `S` untuk menyimpan.
Tekan `R` untuk mengulang dan `ESC` untuk keluar tanpa menyimpan.

Output default:
`outputs/roi/carpal_bone_mask.png`

Anotasi harus mengikuti batas tulang; hindari memasukkan celah sendi dan jaringan
di luar tulang. Bila batas tidak jelas, minta peninjauan pembimbing/ahli.

## Langkah 2: uji kandidat area osifikasi
```bash
python test_ossification.py "outputs/roi/carpal_roi.png" "outputs/roi/carpal_bone_mask.png"
```

Bandingkan percentile:
```bash
python test_ossification.py "outputs/roi/carpal_roi.png" "outputs/roi/carpal_bone_mask.png" --method percentile --percentile 65
python test_ossification.py "outputs/roi/carpal_roi.png" "outputs/roi/carpal_bone_mask.png" --method percentile --percentile 70
python test_ossification.py "outputs/roi/carpal_roi.png" "outputs/roi/carpal_bone_mask.png" --method percentile --percentile 80
```

Bandingkan Otsu:
```bash
python test_ossification.py "outputs/roi/carpal_roi.png" "outputs/roi/carpal_bone_mask.png" --method otsu
```

## Output
`outputs/ossification/`
- `01_enhanced.png`
- `02_carpal_bone_mask.png`
- `03_ossification_candidate_mask.png`
- `04_ossification_overlay.png`

## Batasan ilmiah
Threshold percentile/Otsu hanya memilih piksel berdasarkan intensitas dalam mask
karpal. Radiopak tidak otomatis berarti pusat osifikasi yang dimaksud. Nilai
candidate_ratio_percent hanya rasio kandidat intensitas terhadap area mask,
bukan hasil klinis. Untuk hasil penelitian, definisi osifikasi dan ground-truth
harus ditetapkan melalui protokol anotasi yang ditinjau ahli. Evaluasi Dice/IoU
membutuhkan mask referensi. Hindari menyebut output ini sebagai diagnosis atau
usia tulang tervalidasi.
