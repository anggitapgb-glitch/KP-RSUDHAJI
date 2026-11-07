# OSSIA — Perbaikan Header, Upload, dan Navigasi

Paket ini memperbaiki tampilan Home dan Riwayat berdasarkan CSS yang kamu unggah.

## File
- `home.html`: menghapus badge "Uji upload", mengganti label tombol, menghapus teks UI-only.
- `home.css`: merapikan header dan kartu upload.
- `riwayat.html`: memakai HTML Riwayat yang kamu unggah.
- `riwayat.css`: menyamakan header dan frame Riwayat dengan Home.
- `style.css`: memperbaiki navigasi bawah agar hanya satu lapisan dan sejajar di frame HP.

## Cara memasang
1. Ekstrak ZIP.
2. Backup folder proyek `RSUDHaji`.
3. Salin file di dalam ZIP ke folder proyek dan izinkan replace untuk lima file yang sama.
4. Pastikan `home.html` memanggil `home.css`, `riwayat.html` memanggil `riwayat.css`, dan keduanya memanggil `style.css`.
5. Refresh browser dengan Ctrl+F5.

## Catatan fungsi
Paket ini adalah revisi tampilan HTML/CSS. `home.js` dan `riwayat.js` tidak ditimpa agar fungsi yang ada tidak tertimpa tanpa audit. Tombol Home masih mengikuti perilaku JavaScript yang sedang terpasang. Backend analisis dan estimasi usia tulang belum diubah oleh paket UI ini.
