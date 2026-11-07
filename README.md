# BoneCare RSUD Haji (prototipe UI)

Prototipe antarmuka web untuk estimasi usia tulang (bone age) dan skrining awal
keterlambatan pertumbuhan. Murni HTML + CSS + JavaScript, tanpa build step.

> Hasil analisis di prototipe ini **simulasi** (lihat `simulateAnalysis` di `js/logic.js`).
> Data disimpan di `localStorage` browser, hanya untuk demo.

## Struktur

```
index.html
css/style.css
js/logic.js     usia, aturan skrining (ambang batas di CONFIG), fungsi analisis simulasi
js/chatbot.js   asisten edukasi berbasis kata kunci
js/app.js       tampilan: login, beranda, riwayat, pemeriksaan baru, antrean verifikasi, chat
```

## Menjalankan di VS Code

1. Buka folder ini di VS Code (File > Open Folder).
2. Pasang ekstensi **Live Server** (Ritwick Dey).
3. Klik kanan `index.html` > **Open with Live Server**.

Akun demo:
- Pasien: `RM-001001` + tanggal lahir `12-03-2017` (hasil terverifikasi)
- Pasien: `RM-001002` + tanggal lahir `05-06-2018` (hasil masih menunggu verifikasi)
- Petugas: isi nama apa saja

Alur demo: petugas buat **Pemeriksaan baru**, lalu **Antrean verifikasi** > Tinjau > Verifikasi.
Setelah itu pasien yang bersangkutan bisa melihat hasilnya.

## GitHub

```bash
git init
git add .
git commit -m "Prototipe UI BoneCare"
git branch -M main
git remote add origin https://github.com/USERNAME/rsud-boneage-web.git
git push -u origin main
```

## Deploy ke Cloudflare Pages

1. Dashboard Cloudflare > **Workers & Pages** > **Create** > tab **Pages** > **Connect to Git**.
2. Pilih repo `rsud-boneage-web`.
3. Framework preset: **None**. Build command: kosongkan. Build output directory: `/` (atau kosongkan).
4. **Save and Deploy**. Setiap `git push` ke `main` akan otomatis deploy ulang.

## Langkah berikutnya (setelah UI disetujui)

- Ganti `simulateAnalysis` dengan analisis rasio luas osifikasi karpal yang asli.
- Pindahkan data dari `localStorage` ke backend (mis. Cloudflare Workers + D1, gambar di R2).
- Login sungguhan, enkripsi, dan izin etik sebelum memakai data pasien nyata.
- Konfirmasi ambang batas `CONFIG` dengan dokter radiologi/anak.
