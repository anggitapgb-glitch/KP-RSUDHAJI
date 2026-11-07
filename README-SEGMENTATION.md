# OSSIA - Modul Segmentasi Thresholding

## File tambahan
- `ml/segmentation.py`
- `test_segmentation.py`

## Instalasi
```bash
pip install opencv-python numpy
```

## Jalankan
Pastikan ROI sudah tersimpan di `outputs/roi/carpal_roi.png`:

```bash
python test_segmentation.py "outputs/roi/carpal_roi.png"
```

Eksperimen dengan polaritas mask:
```bash
python test_segmentation.py "outputs/roi/carpal_roi.png" --invert
```

Eksperimen operasi morfologi:
```bash
python test_segmentation.py "outputs/roi/carpal_roi.png" --morphology open
```

## Output
Disimpan di `outputs/segmentation/`:
- `roi_input.png`
- `mask_otsu.png`
- `mask_adaptive_mean.png`
- `mask_adaptive_gaussian.png`

## Interpretasi dan batasan
Metode Otsu dan adaptive threshold memisahkan piksel berdasarkan intensitas. Hasilnya dapat memasukkan jaringan lunak, latar, tepi tulang, atau noise. Mask bukan identifikasi tulang karpal dan tidak boleh langsung dipakai untuk menyatakan rasio luas osifikasi klinis. Diperlukan definisi objek, anotasi referensi, pemeriksaan visual, serta evaluasi (misalnya Dice/IoU terhadap ground-truth mask) sebelum pengukuran.
