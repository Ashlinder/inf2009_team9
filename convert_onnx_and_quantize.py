import os
import torch
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType
import torchvision.models as models
from multitask_model import MultiTaskModel

# Load the trained model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.mobilenet_v2(pretrained=True)
num_classes = len([folder for folder in os.listdir("DCSASS_Dataset") if os.path.isdir(os.path.join("DCSASS_Dataset", folder)) and folder != 'Labels' and folder != '.ipynb_checkpoints'])
model = MultiTaskModel(model, num_classes)
model.load_state_dict(torch.load('activity_detection_model.pth'))
model = model.to(device)
model.eval()

# Dummy input for the model
dummy_input = torch.randn(1, 3, 224, 224).to(device)

# Export the model to ONNX
torch.onnx.export(model, dummy_input, "model.onnx", export_params=True)

# Load the ONNX model
model_path = 'model.onnx'
onnx_model = onnx.load(model_path)

# Quantize the model
quantized_model_path = 'model_quantized.onnx'
quantize_dynamic(model_path, quantized_model_path, weight_type=QuantType.QUInt8)

print("Model has been converted to ONNX and quantized successfully.")