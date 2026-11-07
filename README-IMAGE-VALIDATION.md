# OSSIA - Image Validation

File yang ditambahkan:
- `ml/__init__.py`
- `ml/image_validation.py`
- `test_validation.py`

## Kebutuhan
Pastikan dependency pada `requirements.txt` sudah terpasang, terutama:
- opencv-python
- numpy

## Cara menguji
Dari folder utama proyek:

```powershell
python test_validation.py "samples/xray/contoh.png"
```

Ganti lokasi gambar dengan file uji milik sendiri.

## Integrasi berikutnya
Backend dapat memanggil:

```python
from ml.image_validation import validate_xray

result = validate_xray(filename, file_bytes)
```

Modul ini hanya melakukan validasi teknis dasar. Ia belum memeriksa apakah gambar benar-benar X-ray pergelangan tangan kiri atau apakah kualitasnya layak untuk interpretasi klinis.
