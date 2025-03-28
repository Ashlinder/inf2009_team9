import json
import cv2
import time
import os
import numpy as np
import psutil

LOG_FILE = "log.json"

# Raspberry Pi-Specific Thresholds
LOW_BRIGHTNESS_THRESHOLD = 40  # Adjusted for Pi Camera
LOW_CONTRAST_THRESHOLD = 15
HIGH_NOISE_THRESHOLD = 8
BLUR_THRESHOLD = 80
HIGH_CPU_USAGE = 75  # Adjusted due to lower CPU power
HIGH_TEMP_THRESHOLD = 65  # °C threshold for Raspberry Pi
HIGH_RAM_USAGE = 85  # Lowered to avoid Pi crashes
HIGH_DISK_USAGE = 85  # Adjusted for small SD card storage

def get_video_warnings():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Ensures compatibility with Pi Camera
    if not cap.isOpened():
        return ["Camera not accessible"]

    ret, frame = cap.read()
    cap.release()
    if not ret:
        return ["Camera frame not available"]

    warnings = []

    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 1️⃣ Low Brightness Check
    brightness = np.mean(gray)
    if brightness < LOW_BRIGHTNESS_THRESHOLD:
        warnings.append("Low brightness detected")

    # 2️⃣ Low Contrast Check
    contrast = gray.std()
    if contrast < LOW_CONTRAST_THRESHOLD:
        warnings.append("Low contrast detected")

    # 3️⃣ High Noise Check
    noise = np.var(gray)
    if noise > HIGH_NOISE_THRESHOLD:
        warnings.append("High noise detected")

    # 4️⃣ Black Screen Check
    if np.all(gray < 10):
        warnings.append("Camera might be obstructed or turned off")

    # 5️⃣ Blurry Video Check
    blur_value = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_value < BLUR_THRESHOLD:
        warnings.append("Blurry video detected")

    return warnings

def get_system_warnings():
    warnings = []

    # 1️⃣ High CPU Usage
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > HIGH_CPU_USAGE:
        warnings.append(f"High CPU usage: {cpu_usage}%")

    # 2️⃣ High CPU Temperature (For Raspberry Pi)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp = int(f.read().strip()) / 1000  # Convert from millidegree Celsius
        if cpu_temp > HIGH_TEMP_THRESHOLD:
            warnings.append(f"High CPU temperature: {cpu_temp:.1f}°C")
    except FileNotFoundError:
        warnings.append("CPU temperature monitoring not available")

    # 3️⃣ High RAM Usage
    ram_usage = psutil.virtual_memory().percent
    if ram_usage > HIGH_RAM_USAGE:
        warnings.append(f"High RAM usage: {ram_usage}%")

    # 4️⃣ High Disk Usage
    disk_usage = psutil.disk_usage("/").percent
    if disk_usage > HIGH_DISK_USAGE:
        warnings.append(f"High disk usage: {disk_usage}%")

    return warnings

def update_warnings():
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    video_warnings = get_video_warnings()
    system_warnings = get_system_warnings()

    all_warnings = video_warnings + system_warnings
    if not all_warnings:
        return  # No warnings, nothing to log

    # Read existing log data if available
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                pass  # Ignore corrupted logs

    # Append new warning entry
    log_entry = {
        "Timestamp": timestamp,
        "Warnings": all_warnings
    }
    logs.append(log_entry)

    # Save updated log file
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

    print("Log updated:", log_entry)

# Run the warning check
update_warnings()
