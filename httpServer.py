from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
import os
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'videos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed video extensions
ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov'}

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get file extension
    ext = os.path.splitext(file.filename)[1].lower()

    # Rename file using timestamp
    new_filename = f"{timestamp}{ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    file.save(file_path)

    # Generate a thumbnail if the file is a video
    if allowed_file(new_filename):
        thumb_filename = f"{timestamp}.jpg"
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
        
        # Extract a frame at 1 second as thumbnail using FFmpeg
        subprocess.call([
            'ffmpeg', '-i', file_path, '-ss', '00:00:01.000', '-vframes', '1', thumb_path
        ])

    return jsonify({"message": f"File uploaded successfully as {new_filename}!"})

@app.route('/')
def dashboard():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    videos = []
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            thumb_filename = os.path.splitext(file)[0] + '.jpg'
            thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
            thumbnail_exists = os.path.exists(thumb_path)
            videos.append({
                'video': file,
                'thumbnail': thumb_filename if thumbnail_exists else None
            })
    return render_template('index.html', videos=videos)

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
