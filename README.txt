REVISI ROI DAN SEGMENTASI OSSIA

Isi:
- ml/roi_detection.py dan ml/__init__.py
- test_roi_detection.py
- ml/segmentation.py
- test_segmentation.py

Jalankan dari root project yang memiliki folder ml:
1) Pilih ROI dari citra hasil preprocessing:
   python test_roi_detection.py "outputs/preprocessing/03_preprocessed.png"
2) Segmentasi kandidat dari ROI:
   python test_segmentation.py "outputs/roi/carpal_roi.png" --show

Output segmentasi tersimpan di outputs/segmentation:
01_roi_input.png
02_enhanced.png
03_analysis_mask.png
04_threshold_candidate.png
05_bone_candidate_mask.png
06_segmentation_overlay.png
summary.json

Catatan:
- ROI masih dipilih manual dengan kotak; pastikan kotak mencakup tulang karpal dan seminimal mungkin radius/ulna.
- Analysis mask berbentuk elips sebagai pembatas awal, bukan batas anatomi otomatis. Jika area karpal tidak berada di tengah ROI, pilih ROI lebih rapat dan terpusat.
- Segmentasi adalah kandidat berbasis adaptive threshold lokal. Ini belum segmentasi anatomi tervalidasi.
- Jangan gunakan luas mask sebagai rasio osifikasi klinis sebelum tersedia ground-truth mask.
- Modul validasi tidak disertakan/diubah.
