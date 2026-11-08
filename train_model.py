import os
import cv2
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

CSV_PATH = "dataset_training/boneage_train.csv"
IMAGES_DIR = "dataset_training/images/images"

def extract_ratio(img_path):
    """Ekstraksi rasio tangguh menggunakan metode Otsu mandiri (Tanpa Canny)."""
    image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if image is None: return None
    
    height, width = image.shape
    roi = image[int(height*0.48):int(height*0.83), int(width*0.22):int(width*0.78)]
    if roi.size == 0: return None
    
    # Preprocessing mandiri untuk citra X-ray RSUD
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(roi)
    denoised = cv2.GaussianBlur(enhanced, (5, 5), 0)
    
    # Otsu Thresholding untuk memblok area tulang secara utuh
    _, mask = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return float(cv2.countNonZero(mask) / mask.size)

def main():
    print("Mengekstrak fitur dengan Otsu mandiri (Loading...)...\n")
    df = pd.read_csv(CSV_PATH)
    
    X_data, y_data = [], []
    for index, row in df.head(12600).iterrows():
        img_path = os.path.join(IMAGES_DIR, f"{row['ID']}.png")
        if not os.path.exists(img_path): continue
        
        ratio = extract_ratio(img_path)
        if ratio is not None and 0.05 < ratio < 0.85: # Filter rasio ekstrem
            X_data.append([ratio])
            y_data.append(row['Boneage'])

    # Modeling - Kembalikan ke Polynomial Degree 2
    X = np.array(X_data)
    y = np.array(y_data)
    
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)
    
    print("--- HASIL TRAINING OTSU (DEGREE 2) ---")
    print(f"Intercept : {model.intercept_:.4f}")
    print(f"Coef 1    : {model.coef_[1]:.4f}")
    print(f"Coef 2    : {model.coef_[2]:.4f}")

if __name__ == "__main__":
    main()