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
📂 PC Model Training & Deployment Module  <br>
├── 📂 DCSASS_Dataset <br>
├── split_dataset.py  <br>
├── custom_dataset.py  <br>
├── multitask_model.py  <br>
├── train_model.py  <br>
├── activity_detection_model.pth  <br>
├── training_log.txt  <br>
├── evaluate_model.py  <br>
├── evaluation_results.txt  <br>
├── convert_onnx_and_quantize.py  <br>
├── model.onnx  <br>
├── model_qunatized.onnx  <br>
└── inference.py <br>

## Communication Module

## Dashboard Module


Future Development:
1. Improve the accuracy of the object detection module using more advanced machine learning models and audio analysis
3. Implement additional features, such as motion detection and facial recognition.
4. Develop a mobile app for users to receive notifications and view video footage on-the-go.
