from fabric import Connection

# Paths
QUANTIZED_ONNX_MODEL_PATH = "model_quantized.onnx"
REMOTE_PATH = "/home/model_quantized.onnx"

# Raspberry Pi details
PI_HOST = ""  # Replace with your Raspberry Pi's IP address
PI_PASSWORD = ""  # Replace with your Raspberry Pi's password

# Establish connection
conn = Connection(host=PI_HOST, connect_kwargs={"password": PI_PASSWORD})

# Send the quantized ONNX model to Raspberry Pi
conn.put(QUANTIZED_ONNX_MODEL_PATH, remote=REMOTE_PATH)
print("Quantized ONNX model sent to Raspberry Pi.")