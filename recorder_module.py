import os
import shutil
import time
import subprocess
import threading
import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sensor_input import main as start_sensor
from sendFile import send_file
from inference import predict
from alerts import get_system_warnings

# Suppress ALSA device errors
os.environ["AUDIODEV"] = "null"
sys.stderr = open(os.devnull, 'w')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("recorder.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

INFERENCE_LOG_FILE = "/home/admin/pi/inference_results.json"
WARNING_JSON_DIR = "/home/admin/pi/"
RETRY_LIMIT = 5
RETRY_DELAY = 2  # seconds, exponential backoff applied

class RecorderHandler(FileSystemEventHandler):
    def __init__(self, recorder):
        self.recorder = recorder

    def on_closed(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".mp4"):
            logging.info(f"[Watchdog] New file detected: {event.src_path}")
            self.recorder.queue_file(Path(event.src_path))

class RecorderModule:
    def __init__(self, save_dir="/home/admin/pi/recordings", max_storage_gb=5, ai_model_path="/home/admin/pi/model_quantized.onnx", max_file_age_days=7):
        self.script_start_time = datetime.now()
        self.save_dir = Path(save_dir)
        self.max_storage_bytes = max_storage_gb * (1024 ** 3)
        self.ai_model_path = ai_model_path
        self.max_file_age_days = max_file_age_days
        self.processed_files = {}
        self.pending_files = set()
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.start_watchdog()
        self.new_file_event = threading.Event()
        self.warning_thread = threading.Thread(target=self.start_warning_monitor, daemon=True)
        self.warning_thread.start()
        self.inference_thread = threading.Thread(target=self.process_pending_files, daemon=True)
        self.inference_thread.start()

    def start_watchdog(self):
        event_handler = RecorderHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.save_dir), recursive=False)
        observer.start()
        logging.info("[Watchdog] Started monitoring file changes.")

    #forgot to reimplement this,remove/comment out this and the function in sensor_thread if its not working
    def handle_amplitude(self, amp):
        print(f"[Recorder module] Received amplitude: {amp}")
        if amp > 24999:
            print("[Recorder] Triggering recording!")


    def is_valid_video(self, file_path):
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1", str(file_path)
            ], capture_output=True, text=True)
            return bool(result.stdout.strip())
        except Exception as e:
            logging.error(f"[Validation] Failed to verify video file: {file_path} - {e}")
            return False

    def queue_file(self, file_path):
        if not self.is_valid_video(file_path):
            logging.warning(f"[Validation] {file_path} is not a valid video file. Skipping.")
            return
        logging.info(f"[Queue] Adding {file_path} to pending queue.")
        self.pending_files.add(file_path)
        self.new_file_event.set()

    def process_pending_files(self):
        while True:
            self.new_file_event.wait()
            while self.pending_files:
                file_path = self.pending_files.pop()
                self.process_new_file(file_path)
            self.new_file_event.clear()

    def process_new_file(self, file_path):
        retries = 0
        while retries <= RETRY_LIMIT:
            if self.run_inference(file_path):
                self.processed_files[file_path] = "Success"
                logging.info(f"[Processed] {file_path}")
                return
            retries += 1
            delay = RETRY_DELAY * (2 ** (retries - 1))
            logging.warning(f"[Retry {retries}] {file_path} failed inference. Retrying in {delay} seconds.")
            time.sleep(delay)
        logging.error(f"[Skip] {file_path} failed inference too many times. Adding back to queue.")
        self.queue_file(file_path)

    def run_inference(self, file_path):
        try:
            logging.info(f"[Inference] Running AI on {file_path} with model at {self.ai_model_path}")
            result = predict(str(file_path))
            if not result or "Error" in result:
                logging.error(f"[Error] Inference failed for {file_path}")
                return False
            self.log_inference_result(file_path, result)
            send_file(str(file_path))
            return True
        except Exception as e:
            logging.error(f"[Error] Inference failed on {file_path}: {e}")
            return False

    def log_inference_result(self, file_path, result):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        logs = []
        if os.path.exists(INFERENCE_LOG_FILE):
            with open(INFERENCE_LOG_FILE, "r") as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    pass
        log_entry = {"Timestamp": timestamp, "File": str(file_path), "Result": result}
        logs.append(log_entry)
        with open(INFERENCE_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)
        logging.info(f"[Log] Inference result saved: {log_entry}")

    def save_warnings_to_json(self):
        warnings = get_system_warnings()
        filename = os.path.join(WARNING_JSON_DIR, "system_warnings.json")
        with open(filename, "w") as f:
            json.dump({"warnings": warnings}, f, indent=4)
        logging.info(f"Warnings saved to {filename}")

    def start_warning_monitor(self):
        while True:
            self.save_warnings_to_json()
            time.sleep(30)

if __name__ == "__main__":
    recorder = RecorderModule()
    sensor_thread = threading.Thread(target=start_sensor, args=(recorder.queue_file,handle_amplitude()), daemon=True)
    sensor_thread.start()
    while True:
        time.sleep(1)
