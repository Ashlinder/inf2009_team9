import json
import cv2
import time
import os
import numpy as np

LOG_FILE = "log.json"
LOW_BRIGHTNESS_THRESHOLD = 50  # Adjust as needed
LOW_CONTRAST_THRESHOLD = 20
HIGH_NOISE_THRESHOLD = 10
BLUR_THRESHOLD = 100  # Adjust based on testing

def get_video_warnings():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return {"error": "Camera not accessible"}

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return ["Camera frame not available"]

    warnings = []

    # Convert to grayscale for analysis
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 1️⃣ Low Brightness Check
    brightness = np.mean(gray)
    if brightness < LOW_BRIGHTNESS_THRESHOLD:
        warnings.append("Low brightness detected")

    # 2️⃣ Low Contrast Check
    contrast = gray.std()  # Standard deviation of pixel intensities
    if contrast < LOW_CONTRAST_THRESHOLD:
        warnings.append("Low contrast detected")

    # 3️⃣ High Noise Check
    noise = np.var(gray)  # Variance of pixel intensities
    if noise > HIGH_NOISE_THRESHOLD:
        warnings.append("High noise detected")

    # 4️⃣ Black Screen Check
    if np.all(gray < 10):  # Checks if almost all pixels are dark
        warnings.append("Camera might be obstructed or turned off")

    # 5️⃣ Blurry Video Check (Using Laplacian Variance)
    blur_value = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_value < BLUR_THRESHOLD:
        warnings.append("Blurry video detected")

    return warnings

def update_warnings():
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    warnings = get_video_warnings()

    if not warnings:
        return  # No warnings, nothing to log

    # Read existing log data if available
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    # Append new warning entry
    log_entry = {
        "Timestamp": timestamp,
        "Warnings": warnings
    }

    logs.append(log_entry)

    # Save updated log file
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

    print("Log updated:", log_entry)

# Run the warning check
update_warnings()
