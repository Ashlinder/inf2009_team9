#!/usr/bin/env python3
import cv2
import numpy as np
import pyaudio
import wave
import time
import os
import shutil
import subprocess

# -----------------------------
# USER CONFIGURATIONS
# -----------------------------
OUTPUT_DIR = "/home/pi/recordings"
MIN_FREE_MB = 100  # If less than this free, delete oldest files
RECORD_DURATION = 10  # seconds

# Audio settings for *detection only* (via pyaudio)
AUDIO_CHUNK = 512
AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_THRESHOLD = 25000  # Peak amplitude threshold for "loud noise"
AUDIO_DEVICE_INDEX = 1   # Audio device index (for detection)

# Motion detection
MOTION_AREA_THRESHOLD = 8000  # Contour area threshold for motion

# Video capture settings (for detection)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Which ALSA device to use for ffmpeg (replace with your device if needed)
FFMPEG_ALSA_DEVICE = "plughw:2,0"

# Motion detection pause flag
motion_paused = False

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def get_free_space_mb(directory="/"):
    """Returns free disk space in MB for the given directory."""
    stat = shutil.disk_usage(directory)
    free_mb = stat.free / (1024 * 1024)
    return free_mb

def ensure_space():
    """
    Checks if there's enough free space. If less than MIN_FREE_MB,
    deletes oldest files until enough space is freed.
    """
    while get_free_space_mb("/") < MIN_FREE_MB:
        files = [
            os.path.join(OUTPUT_DIR, f)
            for f in os.listdir(OUTPUT_DIR)
            if f.lower().endswith(('.mp4', '.avi', '.wav'))
        ]
        # Sort by oldest first
        files.sort(key=os.path.getmtime)
        
        if not files:
            print("No files left to delete, but space is still low.")
            return
        
        oldest_file = files[0]
        print(f"Deleting {oldest_file} to free space...")
        os.remove(oldest_file)

def detect_loud_noise(stream, threshold=AUDIO_THRESHOLD):
    """
    Reads a chunk of audio from the PyAudio stream and checks for a
    'loud noise' by looking at the peak amplitude in the chunk.
    Returns True if peak amplitude > threshold, else False.
    """
    try:
        data = stream.read(AUDIO_CHUNK, exception_on_overflow=False)
    except OSError as e:
        # If there's an overflow or other read error, treat as no noise
        print(f"Audio read error: {e}")
        return False

    if len(data) < 2:
        # Not enough bytes to form one int16 sample
        return False

    audio_data = np.frombuffer(data, dtype=np.int16)
    if audio_data.size == 0:
        return False

    peak_amplitude = np.max(np.abs(audio_data))
    print(f"Peak Amplitude: {peak_amplitude} | Threshold: {threshold}")
    return peak_amplitude > threshold

def record_with_ffmpeg(duration=5):
    """
    Uses ffmpeg in a subprocess to record both audio and video for 'duration' seconds,
    storing the final file in OUTPUT_DIR.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"record_{timestamp}.mp4")

    # Example ffmpeg command:
    #   - Capture video from /dev/video0
    #   - Capture audio from the ALSA device (set via FFMPEG_ALSA_DEVICE)
    #   - Limit to 'duration' seconds via -t
    #   - Save to MP4 (H.264 video, AAC audio)
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite if file exists
        "-f", "v4l2",
        "-thread_queue_size", "1024",
        "-s", f"{FRAME_WIDTH}x{FRAME_HEIGHT}",  # frame size
        "-i", "/dev/video0",  # Adjust if your webcam is on another device
        "-f", "alsa",
        "-thread_queue_size", "1024",
        "-i", FFMPEG_ALSA_DEVICE,  # ALSA input device
        "-t", str(duration),       # Recording duration
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "128k",
        filename
    ]

    print(f"Starting ffmpeg to record {duration} seconds...")
    subprocess.run(cmd, check=False)
    # Note: check=False so it doesn't crash on ffmpeg return code.
    print(f"Saved recording: {filename}")

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    global motion_paused

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Initialize video capture for motion detection only
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    # Read two initial frames for motion detection
    ret1, frame1 = cap.read()
    ret2, frame2 = cap.read()

    if not ret1 or not ret2:
        print("Error: Could not read initial frames from camera.")
        cap.release()
        return

    # Initialize audio stream for loud-noise detection
    p = pyaudio.PyAudio()
    audio_stream = p.open(format=pyaudio.paInt16,
                          channels=AUDIO_CHANNELS,
                          rate=AUDIO_RATE,
                          input=True,
                          input_device_index=AUDIO_DEVICE_INDEX,
                          frames_per_buffer=AUDIO_CHUNK)

    print("Starting main loop. Press 'q' in video window to quit.")

    try:
        while True:
            if motion_paused:
                # If we are paused (i.e., while recording), just wait
                print("Motion detection paused. Waiting for recording to finish...")
                time.sleep(1)
                continue

            # ---- MOTION DETECTION ----
            diff = cv2.absdiff(frame1, frame2)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) < MOTION_AREA_THRESHOLD:
                    continue
                motion_detected = True
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame1, "Movement", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            cv2.imshow("Motion Detection", frame1)

            # ---- AUDIO (LOUD NOISE) DETECTION ----
            audio_detected = detect_loud_noise(audio_stream, AUDIO_THRESHOLD)

            # ---- TRIGGER RECORDING ----
            if motion_detected or audio_detected:
                print("Trigger! Recording for 10 seconds...")
                ensure_space()

                # 1) Close the detection audio stream so ffmpeg can use the mic
                audio_stream.stop_stream()
                audio_stream.close()
                p.terminate()

                # 2) **Release the webcam** so ffmpeg can grab /dev/video0
                cap.release()

                motion_paused = True
                record_with_ffmpeg(RECORD_DURATION)
                motion_paused = False
                print("Recording complete.")

                # 3) After ffmpeg finishes, **re-open** the webcam
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

                # Re-prime frames for motion detection
                ret1, frame1 = cap.read()
                ret2, frame2 = cap.read()

                # 4) Re-open the PyAudio stream for detection
                p = pyaudio.PyAudio()
                audio_stream = p.open(format=pyaudio.paInt16,
                                    channels=AUDIO_CHANNELS,
                                    rate=AUDIO_RATE,
                                    input=True,
                                    input_device_index=AUDIO_DEVICE_INDEX,
                                    frames_per_buffer=AUDIO_CHUNK)

                continue


            # Update frames for next iteration
            frame1 = frame2
            ret, frame2 = cap.read()
            if not ret:
                break

            # Check for user exit
            if cv2.waitKey(10) & 0xFF == ord('q'):
                print("Exiting main loop.")
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")

    # Cleanup
    audio_stream.stop_stream()
    audio_stream.close()
    p.terminate()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
