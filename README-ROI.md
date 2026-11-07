# OSSIA - Pemilihan ROI Semi-Manual

## File tambahan
- `ml/roi_detection.py`
- `test_roi_detection.py`

## Jalankan
Pastikan preprocessing sudah menghasilkan `outputs/preprocessing/03_preprocessed.png`.

```bash
python test_roi_detection.py "outputs/preprocessing/03_preprocessed.png"
```

Pada jendela OpenCV, tarik kotak pada area pergelangan/tulang karpal, lalu tekan ENTER atau SPACE. Tekan C/ESC untuk membatalkan.

## Output
Hasil disimpan di `outputs/roi/`:
- `carpal_roi.png`: crop ROI.
- `roi_preview.png`: citra dengan kotak ROI.
- `roi_coordinates.json`: koordinat ROI.

## Catatan metode
Pemilihan ini semi-manual. Operator harus mengikuti definisi batas ROI yang disepakati dalam protokol penelitian. ROI yang dipilih belum otomatis menjamin seluruh tulang karpal tersegmentasi atau anatomisnya benar. Jangan menganggap crop ini sebagai segmentasi tulang.
