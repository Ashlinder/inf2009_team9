from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Set the folder where you want to save the files received from Rasberry Pi
UPLOAD_FOLDER = 'C:/Users/Sujan/Downloads/received_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    return jsonify({"message": f"File {file.filename} uploaded successfully!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Open the server on port 5000
