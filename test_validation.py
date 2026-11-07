"""Tes sederhana modul validasi citra OSSIA.

Cara menjalankan:
    python test_validation.py "samples/xray/contoh.png"
"""
import sys
from pathlib import Path

from ml.image_validation import validate_xray

if len(sys.argv) != 2:
    raise SystemExit(
        'Gunakan: python test_validation.py "lokasi/gambar.png"'
    )

image_path = Path(sys.argv[1])

if not image_path.is_file():
    raise SystemExit(f"File tidak ditemukan: {image_path}")

file_bytes = image_path.read_bytes()

try:
    result = validate_xray(image_path.name, file_bytes)
except ValueError as error:
    raise SystemExit(f"VALIDASI GAGAL: {error}")

print("VALIDASI BERHASIL")
print(f"Status   : {result['validation_status']}")
print(f"Resolusi : {result['width']} x {result['height']}")
print(f"Channel  : {result['channels']}")
print(f"Datatype : {result['dtype']}")
print(f"Format   : {result['format']}")
print(f"Ukuran   : {result['file_size']} bytes")
