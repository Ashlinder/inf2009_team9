# File: modules/recorder_module.py
#!/usr/bin/env python3
import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from sensor_input import main as start_sensor  # Starts sensor input loop

class RecorderModule:
    def __init__(self, save_dir="/home/pi/recordings", max_storage_gb=5, ai_model_path="/home/pi/models/model.pt", max_file_age_days=7):
        self.save_dir = Path(save_dir)
        self.max_storage_bytes = max_storage_gb * (1024 ** 3)
        self.ai_model_path = ai_model_path
        self.max_file_age_days = max_file_age_days
        self.processed_files = set()

        self.save_dir.mkdir(parents=True, exist_ok=True)

    def wait_for_file_stable(self, file_path, timeout=10):
        prev_size = -1
        stable_counter = 0
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                current_size = file_path.stat().st_size
            except FileNotFoundError:
                return False

            if current_size == prev_size:
                stable_counter += 1
                if stable_counter >= 2:
                    print(f"[Stable] File ready: {file_path}")
                    return True
            else:
                stable_counter = 0
            prev_size = current_size
            time.sleep(1)
        print(f"[Timeout] File not stable in time: {file_path}")
        return False

    def run_inference(self, file_path):
        try:
            print(f"[Inference] Running AI on {file_path} with model at {self.ai_model_path}")
            result = {"label": "example", "confidence": 0.95}  # Placeholder
            print(f"[Inference Result] {result}")
            return result
        except Exception as e:
            print(f"[Error] Inference failed on {file_path}: {e}")
            return None

    def check_storage(self):
        total, used, free = shutil.disk_usage(self.save_dir)
        print(f"[Storage] Total: {total}, Used: {used}, Free: {free}")
        return free

    def delete_old_recordings(self):
        now = datetime.now()
        age_limit = now - timedelta(days=self.max_file_age_days)
        free_space = self.check_storage()

        files = sorted(self.save_dir.glob("*.mp4"), key=lambda f: f.stat().st_ctime)
        for file in files:
            file_ctime = datetime.fromtimestamp(file.stat().st_ctime)
            should_delete = False

            if file_ctime < age_limit:
                print(f"[Delete] File {file} is older than {self.max_file_age_days} days")
                should_delete = True
            elif free_space < self.max_storage_bytes:
                print(f"[Delete] Free space below threshold, deleting {file}")
                should_delete = True

            if should_delete:
                try:
                    file.unlink()
                    print(f"[Delete] Removed recording: {file}")
                except Exception as e:
                    print(f"[Error] Could not delete {file}: {e}")
                free_space = self.check_storage()
                if free_space > self.max_storage_bytes:
                    break

    def poll_for_new_files(self):
        print("[Polling] Watching for new recordings...")
        while True:
            files = sorted(self.save_dir.glob("*.mp4"), key=lambda f: f.stat().st_ctime)
            for file in files:
                file_path_str = str(file)
                if file_path_str not in self.processed_files:
                    if self.wait_for_file_stable(file):
                        self.run_inference(file)
                        self.delete_old_recordings()
                        self.processed_files.add(file_path_str)
            time.sleep(2)

if __name__ == "__main__":
    recorder = RecorderModule()

    import threading
    sensor_thread = threading.Thread(target=start_sensor, daemon=True)
    sensor_thread.start()

    recorder.poll_for_new_files()
