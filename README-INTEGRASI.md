# Integrasi OSSIA existing UI + backend Otsu

File ini disusun untuk dipasang di folder root proyek OSSIA yang sudah ada (sejajar dengan `index.html`, `home.html`, `riwayat.html`, `home.js`, `riwayat.js`, `style.css`, `home.css`, dan `riwayat.css`).

## File dalam ZIP
- `home.js`: mempertahankan ID HTML Home saat ini (`homeXrayFile`, `homeDropzone`, `homeTestUpload`, dll), mengirim upload ke `/api/analyze`, lalu menyimpan hasil ke `localStorage` dan membuka `riwayat.html`.
- `riwayat.js`: memakai ID HTML Riwayat saat ini (`historyList`, `historySearch`, `historyTotal`, `historyAttention`, `historyDetailDialog`) dan membaca record yang sama.
- `app.py`: backend Flask diletakkan di root, melayani `index.html` yang sudah ada dan endpoint `/api/analyze`. Tidak memakai frontend demo.
- `requirements.txt`: dependencies Python.

## Pasang dan jalankan
1. Backup folder proyek.
2. Ekstrak ZIP, salin ke folder root OSSIA, replace `home.js` dan `riwayat.js`; tambahkan `app.py` dan `requirements.txt`.
3. Di terminal pada folder root:
```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python app.py
```
4. Buka `http://127.0.0.1:5000`. Jangan buka `index.html` lewat `file://` atau Live Server, sebab API menggunakan same-origin `/api/analyze`.
5. Dari Home, pilih PNG/JPG maksimal 10 MB, lalu tekan tombol. Setelah analisis sukses, hasil tersimpan dan halaman berpindah ke Riwayat.

## Catatan kompatibilitas
HTML Home yang dirujuk menggunakan ID `homeXrayFile`, `homeDropzone`, `homeFilePreview`, `homePreviewImage`, `homeFileName`, `homeFileSize`, `homeUploadTitle`, `homeUploadHint`, `homeTestUpload`, `homeUploadMessage`. HTML Riwayat menggunakan `historyTotal`, `historyAttention`, `historySearch`, `historyClear`, `historyList`, `historyDetailDialog`, `historyDetailContent`, dan tombol filter `data-history-filter`. CSS yang sudah ada dipertahankan.

## Batasan teknis dan klinis
ROI backend masih berupa perkiraan koordinat tengah-bawah gambar, bukan ROI anatomi karpal yang otomatis akurat. Status adalah pemeriksaan teknis mask, bukan "normal" secara klinis. Usia tulang belum diprediksi. Data riwayat tersimpan di localStorage browser, bukan database cloud; untuk penggunaan pasien nyata dibutuhkan penyimpanan backend yang aman, kontrol akses, persetujuan, anonimisasi, dan validasi klinis.
