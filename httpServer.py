from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
import os
import subprocess
import logging
import json

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)

UPLOAD_FOLDER = 'videos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed video extensions
ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed video extension."""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def generate_thumbnail(video_path, thumbnail_path):
    """Generate a thumbnail using FFmpeg."""
    try:
        subprocess.run(
            ['ffmpeg', '-i', video_path, '-ss', '00:00:01.000', '-vframes', '1', thumbnail_path],
            check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        logger.info(f"Thumbnail generated: {thumbnail_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}" )  # Debugging output
        return False

def get_next_filename():
    """Find the next available integer filename, only for MP4 uploads."""
    existing_files = [int(os.path.splitext(f)[0]) for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.mp4') and f.split('.')[0].isdigit()]
    next_number = max(existing_files) + 1 if existing_files else 1
    return str(next_number)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads, rename them to an incrementing integer (for MP4 only), and generate a thumbnail."""
    if 'file' not in request.files:
        logger.error("No file part in the request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if not allowed_file(file.filename):
        logger.error(f"File type {ext} is not allowed")
        return jsonify({"error": f"File type {ext} is not allowed"}), 400

    if ext == '.mp4':
        new_filename = f"{get_next_filename()}{ext}"
    else:
        new_filename = file.filename  # Keep original name for non-MP4 files
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    
    try:
        file.save(file_path)
        logger.info(f"File saved: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {str(e)}")
        return jsonify({"error": "Failed to save file"}), 500

    # Generate a thumbnail if the uploaded file is an MP4 video
    if ext == '.mp4':
        thumb_filename = f"{os.path.splitext(new_filename)[0]}.jpg"
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
        
        success = generate_thumbnail(file_path, thumb_path)
        if not success:
            return jsonify({"error": "Failed to generate thumbnail"}), 500

    return jsonify({"message": f"File uploaded successfully as {new_filename}!"})

@app.route('/upload_json', methods=['POST'])
def upload_json():
    """Handle JSON uploads and save them as a file in the upload folder."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        json_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        
        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        logger.info(f"JSON file saved: {json_path}")
        return jsonify({"message": f"JSON uploaded successfully as {json_filename}!"})
    except Exception as e:
        logger.error(f"Failed to save JSON file: {str(e)}")
        return jsonify({"error": "Failed to save JSON file"}), 500

@app.route('/')
def dashboard():
    """Render the dashboard with the list of uploaded videos and their thumbnails."""
    videos = []
    
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
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
    """Serve uploaded video files."""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error serving video {filename}: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    """Serve generated thumbnails."""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error serving thumbnail {filename}: {str(e)}")
        return jsonify({"error": "Thumbnail not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
