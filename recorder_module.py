# File: modules/recorder_module.py
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

class RecorderModule:
    def __init__(self, save_dir="/home/pi/recordings", max_storage_gb=5, ai_model_path="/home/pi/models/model.pt"):
        self.save_dir = Path(save_dir)
        self.max_storage_bytes = max_storage_gb * (1024 ** 3)
        self.ai_model_path = ai_model_path
        self.recording_process = None
        self.current_file = None

        self.save_dir.mkdir(parents=True, exist_ok=True)

    def start_recording(self):
        if self.recording_process:
            print("Recording already in progress.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.save_dir / f"recording_{timestamp}.mp4"
        #change here as necessary
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "v4l2",
            "-framerate", "30",
            "-video_size", "640x480",
            "-i", "/dev/video0",
            "-f", "alsa",
            "-i", "hw:1",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            str(self.current_file)
        ]
        self.recording_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Recording started: {self.current_file}")

    def stop_recording(self):
        if not self.recording_process:
            print("No recording in progress.")
            return

        self.recording_process.terminate()
        self.recording_process.wait()
        self.recording_process = None
        print(f"Recording stopped: {self.current_file}")

    def is_recording(self):
        return self.recording_process is not None

    def run_inference(self, file_path):
        print(f"Running inference on {file_path} using model at {self.ai_model_path}")
        result = {"label": "example", "confidence": 0.95}
        return result

    def check_storage(self):
        total, used, free = shutil.disk_usage(self.save_dir)
        print(f"Storage - Total: {total}, Used: {used}, Free: {free}")
        return free

    def delete_old_recordings(self):
        free_space = self.check_storage()
        if free_space > self.max_storage_bytes:
            return

        files = sorted(self.save_dir.glob("*.mp4"), key=os.path.getctime)
        for file in files:
            os.remove(file)
            print(f"Deleted old recording: {file}")
            free_space = self.check_storage()
            if free_space > self.max_storage_bytes:
                break

# Example usage:
# recorder = RecorderModule()
# recorder.start_recording()
# time.sleep(10)
# recorder.stop_recording()
# result = recorder.run_inference(recorder.current_file)
# recorder.delete_old_recordings()
