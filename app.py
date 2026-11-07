from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import cv2
import numpy as np
import base64

# Taruh app.py di folder root OSSIA, sejajar dengan index.html, home.html, home.js.
ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
MAX_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")

@app.get("/health")
def health():
    return jsonify(ok=True, service="OSSIA image preprocessing and Otsu")

def png_data_uri(image):
    ok, buffer = cv2.imencode(".png", image)
    if not ok:
        raise ValueError("Gagal membuat gambar hasil.")
    return "data:image/png;base64," + base64.b64encode(buffer).decode("ascii")

@app.post("/api/analyze")
def analyze():
    upload = request.files.get("image")
    if not upload:
        return jsonify(error="File X-ray tidak ditemukan."), 400
    if Path(upload.filename or "").suffix.lower() not in ALLOWED_EXTENSIONS:
        return jsonify(error="Format harus PNG atau JPG."), 400
    raw = upload.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        return jsonify(error="Ukuran file maksimal 10 MB."), 400
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        return jsonify(error="File citra tidak valid atau tidak dapat dibaca."), 400
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    height, width = gray.shape

    # Baseline approximate ROI for a vertically framed wrist X-ray.
    # Not anatomy-aware; replace with manual ROI or a trained model before evaluation.
    x0, x1 = int(width * .22), int(width * .78)
    y0, y1 = int(height * .48), int(height * .83)
    roi = gray[y0:y1, x0:x1]
    if roi.size == 0:
        return jsonify(error="ROI tidak valid untuk citra ini."), 400

    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(roi)
    denoised = cv2.medianBlur(enhanced, 3)
    denoised = cv2.GaussianBlur(denoised, (5, 5), 0)
    threshold, mask = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    foreground = cv2.countNonZero(mask) / mask.size
    if not .08 <= foreground <= .75:
        mask = cv2.bitwise_not(mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    clean = np.zeros_like(mask)
    min_area = max(8, int(mask.size * .001))
    for index in range(1, count):
        if stats[index, cv2.CC_STAT_AREA] >= min_area:
            clean[labels == index] = 255
    mask = clean
    foreground_ratio = cv2.countNonZero(mask) / mask.size

    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    roi_overlay = overlay[y0:y1, x0:x1]
    selected = mask > 0
    roi_overlay[selected] = (0.35 * roi_overlay[selected] + 0.65 * np.array([35, 40, 235])).astype(np.uint8)
    cv2.rectangle(overlay, (x0, y0), (x1, y1), (0, 210, 180), 2)

    # This status describes mask quality heuristically, not clinical normality.
    status = "Perlu peninjauan" if foreground_ratio < .10 or foreground_ratio > .70 else "Perlu verifikasi"
    return jsonify(
        ok=True, overlay=png_data_uri(overlay), mask=png_data_uri(mask),
        threshold=float(threshold), foreground_ratio=float(foreground_ratio),
        status=status,
        explanation="Status ini hanya penanda teknis berdasarkan proporsi area mask. Periksa overlay dan mask secara visual.",
        limitation="Otsu tidak menentukan usia tulang atau diagnosis. Hasil ini bukan penilaian klinis."
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
