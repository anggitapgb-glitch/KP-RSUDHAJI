# OSSIA - Optimasi Eksploratif Segmentasi dan Mask Refinement

## File baru / diperbarui
- `ml/segmentation.py` diperbarui: denoising none/median/gaussian/bilateral; Otsu; adaptive mean; adaptive Gaussian.
- `ml/mask_refinement.py` baru: morphological opening/closing, connected-component filtering, overlay.
- `test_mask_refinement.py` baru: mencoba kombinasi parameter dan menyimpan CSV perbandingan.
- `test_segmentation.py` diperbarui: pilihan denoise, block size, C, dan invert.

## Instalasi
```bash
pip install opencv-python numpy
```

## Uji segmentasi awal
```bash
python test_segmentation.py "outputs/roi/carpal_roi.png"
```

## Jalankan pencarian parameter eksploratif
```bash
python test_mask_refinement.py "outputs/roi/carpal_roi.png"
```

Pencarian ini menghasilkan banyak varian (folder `outputs/refinement/`) dan `parameter_comparison.csv`.
Buka beberapa `overlay.png` dan `refined_mask.png` yang representatif untuk pemeriksaan visual.

## Penting secara metodologis
Tidak ada parameter yang dapat disebut paling akurat hanya dari foreground ratio atau jumlah komponen. Tanpa ground-truth mask yang dibuat/ditinjau ahli, hasil hanya eksplorasi pemrosesan intensitas. Untuk memilih parameter final diperlukan anotasi referensi dan evaluasi Dice, IoU, serta pemeriksaan apakah struktur tulang karpal yang ditargetkan benar-benar tersegmentasi. Filter komponen kecil dapat menghapus struktur tulang kecil, sedangkan closing dapat menyatukan tulang yang seharusnya terpisah. Karena itu, parameter default dibuat konservatif dan seluruh varian disimpan untuk dibandingkan.
