from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import cv2
import numpy as np
import base64

# Impor modul klinis buatanmu
from ml.growth_assessment import assess_growth


# ==========================================
# KONFIGURASI OSSIA
# ==========================================

ROOT = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(ROOT),
    static_url_path=""
)

MAX_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


# ==========================================
# HALAMAN UTAMA
# ==========================================

@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


# ==========================================
# HEALTH CHECK BACKEND
# ==========================================

@app.get("/health")
def health():
    return jsonify(
        ok=True,
        service="OSSIA image preprocessing and Otsu"
    )


# ==========================================
# KONVERSI GAMBAR KE BASE64
# ==========================================

def png_data_uri(image):
    ok, buffer = cv2.imencode(".png", image)

    if not ok:
        raise ValueError("Gagal membuat gambar hasil.")

    return (
        "data:image/png;base64,"
        + base64.b64encode(buffer).decode("ascii")
    )


# ==========================================
# API ANALISIS X-RAY
# ==========================================

@app.post("/api/analyze")
def analyze():

    # Ambil file dari frontend
    upload = request.files.get("image")

    if not upload:
        return jsonify(
            error="File X-ray tidak ditemukan."
        ), 400

    # Validasi format
    if Path(upload.filename or "").suffix.lower() not in ALLOWED_EXTENSIONS:
        return jsonify(
            error="Format harus PNG atau JPG."
        ), 400

    # Validasi ukuran file
    raw = upload.read(MAX_BYTES + 1)

    if len(raw) > MAX_BYTES:
        return jsonify(
            error="Ukuran file maksimal 10 MB."
        ), 400

    # Decode gambar
    image = cv2.imdecode(
        np.frombuffer(raw, np.uint8),
        cv2.IMREAD_UNCHANGED
    )

    if image is None:
        return jsonify(
            error="File citra tidak valid atau tidak dapat dibaca."
        ), 400

    # ======================================
    # KONVERSI GRAYSCALE
    # ======================================

    if image.ndim == 3:
        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGRA2GRAY
            if image.shape[2] == 4
            else cv2.COLOR_BGR2GRAY
        )

    gray = cv2.normalize(
        image,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    ).astype(np.uint8)

    height, width = gray.shape

    # ======================================
    # REGION OF INTEREST (ROI)
    # ======================================

    x0 = int(width * 0.22)
    x1 = int(width * 0.78)

    y0 = int(height * 0.48)
    y1 = int(height * 0.83)

    roi = gray[y0:y1, x0:x1]

    if roi.size == 0:
        return jsonify(
            error="ROI tidak valid untuk citra ini."
        ), 400

    # ======================================
    # IMAGE ENHANCEMENT
    # ======================================

    enhanced = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    ).apply(roi)

    # Median filtering
    denoised = cv2.medianBlur(
        enhanced,
        3
    )

    # Gaussian filtering
    denoised = cv2.GaussianBlur(
        denoised,
        (5, 5),
        0
    )

    # ======================================
    # SEGMENTASI OTSU
    # ======================================

    threshold, mask = cv2.threshold(
        denoised,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    foreground = cv2.countNonZero(mask) / mask.size

    if not 0.08 <= foreground <= 0.75:
        mask = cv2.bitwise_not(mask)

    # ======================================
    # PEMBERSIHAN NOISE
    # ======================================

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (3, 3)
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    # ======================================
    # CONNECTED COMPONENTS
    # ======================================

    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask,
        8
    )

    clean = np.zeros_like(mask)

    min_area = max(
        8,
        int(mask.size * 0.001)
    )

    for index in range(1, count):
        if stats[index, cv2.CC_STAT_AREA] >= min_area:
            clean[labels == index] = 255

    mask = clean

    foreground_ratio = (
        cv2.countNonZero(mask) / mask.size
    )

    # ======================================
    # ESTIMASI USIA & PENILAIAN KLINIS (ML)
    # ======================================
    
    # Rumus regresi polinomial derajat 2 dari train_model.py
    intercept = 16.3313
    coef_1 = 494.4149
    coef_2 = -528.8530
    
    estimasi_bulan_raw = intercept + (coef_1 * foreground_ratio) + (coef_2 * (foreground_ratio ** 2))
    estimasi_bulan = max(0, int(round(estimasi_bulan_raw)))
    estimasi_tahun = round(estimasi_bulan / 12, 1)

    # Simulasi usia kronologis default 120 bulan (10 tahun) untuk penilaian awal
    usia_asli_pasien = 120
    
    # Panggil modul growth_assessment.py
    hasil_klinis = assess_growth(estimasi_bulan, usia_asli_pasien)
    kriteria_klinis = hasil_klinis["kriteria"]
    penjelasan_klinis = hasil_klinis["penjelasan"]

    # ======================================
    # OVERLAY HASIL SEGMENTASI
    # ======================================

    overlay = cv2.cvtColor(
        gray,
        cv2.COLOR_GRAY2BGR
    )

    roi_overlay = overlay[y0:y1, x0:x1]

    selected = mask > 0

    roi_overlay[selected] = (
        0.35 * roi_overlay[selected]
        + 0.65 * np.array([35, 40, 235])
    ).astype(np.uint8)

    # Tandai area ROI
    cv2.rectangle(
        overlay,
        (x0, y0),
        (x1, y1),
        (0, 210, 180),
        2
    )

    # ======================================
    # STATUS KUALITAS MASK
    # ======================================

    status = (
        "Perlu peninjauan"
        if foreground_ratio < 0.10
        or foreground_ratio > 0.70
        else "Normal"
    )

    # ======================================
    # RESPONSE API (MENGIRIM DATA KE FRONTEND)
    # ======================================

    return jsonify(
        ok=True,
        overlay=png_data_uri(overlay),
        mask=png_data_uri(mask),
        threshold=float(threshold),
        foreground_ratio=float(foreground_ratio),
        estimasi_bulan=estimasi_bulan,
        estimasi_tahun=estimasi_tahun,
        kriteria=kriteria_klinis,
        status=status,
        explanation=penjelasan_klinis,
        limitation=(
            "Estimasi didasarkan pada perhitungan regresi luas osifikasi "
            "dan bukan diagnosis medis mutlak."
        )
    )


# ==========================================
# MENJALANKAN FLASK SECARA LOKAL
# ==========================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )