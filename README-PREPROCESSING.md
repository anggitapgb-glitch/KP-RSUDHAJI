# OSSIA - Modul Preprocessing Citra

## File yang ditambahkan
- `ml/preprocessing.py`: fungsi preprocessing citra X-ray.
- `test_preprocessing.py`: skrip uji dengan gambar lokal.

## Instalasi
Di terminal pada folder utama proyek:

```bash
pip install opencv-python numpy
```

## Menjalankan
Pastikan gambar uji berada di `samples/xray/contoh.png`, lalu:

```bash
python test_preprocessing.py "samples/xray/contoh.png"
```

Hasil citra disimpan pada `outputs/preprocessing/`.

## Pipeline default
1. Grayscale.
2. Normalisasi intensitas ke uint8 (0-255).
3. CLAHE aktif.
4. Median filtering nonaktif.
5. Gaussian filtering nonaktif.

Median dan Gaussian sengaja nonaktif secara default. Keduanya dapat menghaluskan detail tulang, sehingga harus dibandingkan dan dievaluasi sebelum dipakai pada pipeline utama. CLAHE juga perlu diperiksa secara visual pada beberapa citra.

Modul ini hanya melakukan preprocessing teknis, bukan segmentasi anatomi, pengukuran rasio osifikasi, atau diagnosis klinis.
