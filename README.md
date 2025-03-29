inf2009_team9
# Automated Suspicious Activity Detection for Small Businesses
Download data from (https://drive.google.com/drive/folders/1--psd0P2rjJabOcuD-JOBLBS8lTvMXOA?usp=sharing):
<br>
Raw data folder: DCSASS_Dataset
<br>
Split datasets folder: data 


## Setup:

To run, create a virtual environment, install Flask to run.

1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip3 install -r requirements.txt`
4. `python3 httpServer.py` 



Welcome to the Automated Suspicious Activity Detection for Small Businesses Project!

This project is designed to help small businesses detect suspicious activity using a Raspberry Pi and a camera module. 
In this guide, we will walk you through the steps to set up and run the project.

Hardware Requirements:
1. Raspberry Pi (with camera module)
2. Laptop or server for data processing and storage

Software Requirements:
1. Python 3.x
2. Flask
3. FFmpeg
4. OpenCV
5. NumPy
6. psutil

Project Structure:
- static: contains static files, including CSS, JavaScript, and images
- templates: contains HTML templates for the web interface
- uploads: contains uploaded video files
- [Sensor Input Module](#sensor-input-module)  
- [Raspberry Pi Processing Module](#raspberry-pi-processing-module)  
- [PC Model Training & Deployment Module](#pc-model-training--deployment-module)  
- [Communication Module](#communication-module)  
- [Dashboard Module](#dashboard-module)  

## Sensor Input Module

## Raspberry Pi Processing Module

## PC Model Training & Deployment Module
**📂 PC Model Training & Deployment Module**  <br>
├── **📂 DCSASS_Dataset** - Contains raw data <br>
├── **split_dataset.py** - Splits dataset into training, validation and testing sets <br>
├── **custom_dataset.py** - Defines a custom dataset class for loading data  <br>
├── **multitask_model.py** - Implements a multi-task learning model for activity detection   <br>
├── **train_model.py** - Trains the AI model using the dataset   <br>
├── **activity_detection_model.pth** - Saved trained model in PyTorch format   <br>
├── **training_log.txt** - Logs the training progress and metrics   <br>
├── **evaluate_model.py** - Evaluates the trained model on validation data  <br>
├── **evaluation_results.txt** - Stores evaluation results such as accuracy and loss   <br>
├── **convert_onnx_and_quantize.py** - Converts the trained model to ONNX and applies quantization for optimization   <br>
├── **model.onnx** - AI model converted to ONNX format for lightweight deployment   <br>
├── **model_qunatized.onnx** - Quantized ONNX model for improved efficiency   <br>
└── **inference.py** - Runs inference on new video data using the trained model  <br>

**Steps**
1. Download Raw Data (https://drive.google.com/drive/folders/1--psd0P2rjJabOcuD-JOBLBS8lTvMXOA?usp=sharing)
2. Execute the scripts below sequentially to generate model_quantize.onnx:  <br>
   a. split_dataset.py  <br>
   b. train_model.py  <br>
   c. evaluate_model.py  <br>
   d. convert_onnx_and_quantize.py  <br>

**Dependencies** <br>
Before running the scripts, ensure you have the following dependencies installed:  <br>
- `pandas`
- `sklearn`
- `torch`
- `torchvision`
- `cv2`
- `onnx`
- `onnxruntime`

**Test Model** <br>
1. Run `inference.py` to launch the Gradio interface. <br>
2. Upload a video or record using the webcam, then click submit. <br>
3. The result will indicate if suspicious activity is detected. If detected, the category of suspicious activity (either Violence or Theft) and the probability will be shown. <br>

## Communication Module

## Dashboard Module


Future Development:
1. Improve the accuracy of the object detection module using more advanced machine learning models and audio analysis
3. Implement additional features, such as motion detection and facial recognition.
4. Develop a mobile app for users to receive notifications and view video footage on-the-go.
