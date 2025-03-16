#!/usr/bin/env python3
import cv2
import numpy as np
import pyaudio
import wave
import time
import os
import shutil
import multiprocessing

# -----------------------------
# USER CONFIGURATIONS
# -----------------------------
OUTPUT_DIR = "/home/pi/recordings"
OUTPUT_AUDIO_DIR = "/home/pi/audio"
MIN_FREE_MB = 100  # If less than this free, delete oldest files
RECORD_DURATION = 10  # seconds
AUDIO_CHUNK = 512
AUDIO_RATE = 48000
AUDIO_CHANNELS = 1
AUDIO_THRESHOLD = 25000  # Peak amplitude threshold for "loud noise"
MOTION_AREA_THRESHOLD = 900  # Contour area threshold for motion
AUDIO_DEVICE_INDEX = 1 # Audio device index in case default one is wrong

# For debugging or capturing smaller frames:
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Motion detection pause flag
motion_paused = False

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def get_free_space_mb(directory="/"):
    """Returns free disk space in MB for the given directory."""
    stat = shutil.disk_usage(directory)
    # stat => (total, used, free) in bytes
    free_mb = stat.free / (1024 * 1024)
    return free_mb

# Only OUTPUT_DIR
# def ensure_space():
#     """
#     Checks if there's enough free space. If less than MIN_FREE_MB,
#     deletes oldest video files in OUTPUT_DIR until enough space is freed.
#     """
#     while get_free_space_mb(OUTPUT_DIR) < MIN_FREE_MB:
#         # Get list of files sorted by oldest first
#         files = sorted(
#             [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR)
#              if f.lower().endswith(('.mp4', '.avi'))],
#             key=os.path.getmtime
#         )
#         if not files:
#             print("No files left to delete, but space is still low.")
#             return
#         oldest_file = files[0]
#         print(f"Deleting {oldest_file} to free space...")
#         os.remove(oldest_file)

def ensure_space():
    """
    Checks if there's enough free space. If less than MIN_FREE_MB,
    deletes oldest files (video + audio) until enough space is freed.
    """
    while get_free_space_mb("/") < MIN_FREE_MB:  # or get_free_space_mb(OUTPUT_DIR) if on same partition
        # Gather all video/audio files from both directories
        video_files = [
            os.path.join(OUTPUT_DIR, f) 
            for f in os.listdir(OUTPUT_DIR)
            if f.lower().endswith(('.mp4', '.avi'))
        ]
        audio_files = [
            os.path.join(OUTPUT_AUDIO_DIR, f)
            for f in os.listdir(OUTPUT_AUDIO_DIR)
            if f.lower().endswith('.wav')
        ]

        # Combine them all
        all_files = video_files + audio_files
        
        # Sort by oldest first
        all_files.sort(key=os.path.getmtime)
        
        if not all_files:
            print("No files left to delete, but space is still low.")
            return
        
        oldest_file = all_files[0]
        print(f"Deleting {oldest_file} to free space...")
        os.remove(oldest_file)


def record_video(cap, duration=5, fourcc_str='mp4v'):
    """
    Records 'duration' seconds of video from 'cap', saving to a timestamped file.
    """
    # Create unique filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"video_{timestamp}.mp4")

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
    out = cv2.VideoWriter(filename, fourcc, 30.0, (FRAME_WIDTH, FRAME_HEIGHT))

    # PRE-WARM CAMERA: Capture and discard a few frames before recording
    for _ in range(5):
        cap.read()

    frames_recorded = 0
    while frames_recorded < (30 * duration):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frames_recorded += 1
        cv2.imshow("Recording...", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    out.release()
    print(f"Saved video: {filename} ({frames_recorded / 30:.1f} seconds)")

def record_audio(duration=5):
    """Record raw audio for 'duration' seconds, then save it to a .wav file."""
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=AUDIO_CHANNELS,
                        rate=AUDIO_RATE,
                        input=True,
                        input_device_index=AUDIO_DEVICE_INDEX,
                        frames_per_buffer=AUDIO_CHUNK)
    except OSError as e:
        print(f"Error opening audio stream: {e}")
        p.terminate()
        return None

    frames = []
    start_time = time.time()
    while (time.time() - start_time) < duration:
        try:
            data = stream.read(AUDIO_CHUNK, exception_on_overflow=False)
            frames.append(data)
        except OSError as e:
            print(f"Error reading audio: {e}")
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the audio if recording worked
    if frames:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_AUDIO_DIR, f"audio_{timestamp}.wav")
        wf = wave.open(filename, 'wb')
        wf.setnchannels(AUDIO_CHANNELS)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(AUDIO_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"Saved audio: {filename}")
    else:
        print("No audio recorded.")

    return frames

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

    # Convert to int16 numpy array
    audio_data = np.frombuffer(data, dtype=np.int16)
    if audio_data.size == 0:
        return False

    # Peak amplitude: largest absolute sample in this chunk
    peak_amplitude = np.max(np.abs(audio_data))

    # Debug print
    print(f"Peak Amplitude: {peak_amplitude} | Threshold: {threshold}")

    return peak_amplitude > threshold

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    global motion_paused

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(OUTPUT_AUDIO_DIR):
        os.makedirs(OUTPUT_AUDIO_DIR)

    # Initialize video capture
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    # Read two initial frames for motion detection
    _, frame1 = cap.read()
    _, frame2 = cap.read()

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
                # Optionally draw bounding boxes
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame1, "Movement", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            cv2.imshow("Motion Detection", frame1)

            # ---- AUDIO (LOUD NOISE) DETECTION ----
            audio_detected = detect_loud_noise(audio_stream, AUDIO_THRESHOLD)

            # ---- TRIGGER RECORDING ----
            if motion_detected or audio_detected:
                print("Trigger! Recording for 10 seconds...")
                ensure_space()  # Make sure we have enough space before we record
                motion_paused = True

                # Close the detection audio stream
                audio_stream.stop_stream()
                audio_stream.close()
                p.terminate()

                # Record the new audio + video
                record_audio(RECORD_DURATION)
                record_video(cap, RECORD_DURATION)

                # Re-prime the frames for motion detection
                _, frame1 = cap.read()
                _, frame2 = cap.read()

                # Re-open the detection audio stream
                p = pyaudio.PyAudio()
                audio_stream = p.open(format=pyaudio.paInt16,
                                      channels=AUDIO_CHANNELS,
                                      rate=AUDIO_RATE,
                                      input=True,
                                      input_device_index=AUDIO_DEVICE_INDEX,
                                      frames_per_buffer=AUDIO_CHUNK)

                motion_paused = False
                print("Recording complete.")
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
