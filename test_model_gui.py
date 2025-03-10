import gradio as gr
import torch
import torchvision.transforms as transforms
from PIL import Image
import cv2
import numpy as np
import onnxruntime as ort

# Paths
QUANTIZED_ONNX_MODEL_PATH = "model_quantized.onnx"
ACTIVITIES = ['Abuse', 'Arrest', 'Arson', 'Assault', 'Burglary', 'Explosion', 'Fighting', 'Robbery', 'Shooting', 'Shoplifting', 'Stealing', 'Vandalism']  # Update with your activity names

# Load the ONNX model
ort_session = ort.InferenceSession(QUANTIZED_ONNX_MODEL_PATH, providers=['CPUExecutionProvider'])

# Preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def preprocess_video(video_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise ValueError(f"Failed to read frame from {video_path}")
    frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    frame = transform(frame)
    return frame.unsqueeze(0).numpy()

def predict(video_path):
    # Preprocess the video
    input_tensor = preprocess_video(video_path)

    # Run inference
    ort_inputs = {ort_session.get_inputs()[0].name: input_tensor}
    ort_outs = ort_session.run(None, ort_inputs)
    binary_output, multi_output = ort_outs

    # Determine if the activity is suspicious
    is_suspicious = binary_output[0][0] > 0.5

    if is_suspicious:
        # Get the multi-class classification result
        activity_index = np.argmax(multi_output[0])
        activity_name = ACTIVITIES[activity_index]
        return f"Suspicious activity detected: {activity_name}"
    else:
        return "No suspicious activity detected."

# Create Gradio interface
iface = gr.Interface(
    fn=predict,
    inputs=gr.Video(),
    outputs="text",
    title="Activity Detection",
    description="Upload or record a video to detect suspicious activities."
)

if __name__ == "__main__":
    iface.launch()