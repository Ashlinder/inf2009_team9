import os
import pandas as pd
import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms
from PIL import Image
import cv2

class CustomDataset(Dataset):
    def __init__(self, data_path, labels_path, activities, transform):
        self.data = []
        self.labels_binary = []  # Suspicious (1) or Not (0)
        self.labels_multi = []   # Multi-class labels (activity classification)
        self.transform = transform

        # Create a mapping from activity names to indices
        activity_to_index = {activity: idx for idx, activity in enumerate(activities)}
        print(activities)

        for label_file in os.listdir(labels_path):
            if label_file.endswith(".csv"):
                activity = label_file.split('.')[0]
                activity_index = activity_to_index[activity]
                df = pd.read_csv(os.path.join(labels_path, label_file), sep=',', header=None)
                df.columns = ['filename', 'activity', 'label']

                for _, row in df.iterrows():
                    video_file = os.path.join(data_path, row['filename'] + ".mp4")
                    if os.path.exists(video_file):
                        if pd.isna(row['label']):
                            print(f"Found NaN label in file: {label_file}, row: {row}")
                        else:
                            label_binary = 1 if activity != "Normal" else 0  # Binary classification
                            label_multi = activity_index  # Multi-class classification
                            self.data.append(video_file)
                            self.labels_binary.append(label_binary)
                            self.labels_multi.append(label_multi)

        print(f"Loaded {len(self.data)} samples from {data_path}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        video_file = self.data[idx]
        label_binary = self.labels_binary[idx]
        label_multi = self.labels_multi[idx]

        # Extract a single frame from the video for simplicity
        frame = self.extract_frame(video_file)

        if self.transform:
            frame = self.transform(frame)

        return frame, torch.tensor(label_binary, dtype=torch.long), torch.tensor(label_multi, dtype=torch.long)

    def extract_frame(self, video_file):
        # Use OpenCV to extract a single frame from the video
        cap = cv2.VideoCapture(video_file)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise ValueError(f"Failed to read frame from {video_file}")
        frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        return frame