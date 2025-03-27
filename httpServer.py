from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
import os
import subprocess
import logging

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

# Check if file extension is allowed
def allowed_file(filename):
    """Check if the uploaded file has an allowed video extension."""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# Generate thumbnail from video using FFmpeg
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
        logger.error(f"FFmpeg error: {e.stderr.decode()}")  # Debugging output
        return False

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads, rename them, and generate a thumbnail."""
    if 'file' not in request.files:
        logger.error("No file part in the request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    # Generate a readable timestamp for the filename
    timestamp = datetime.now().strftime("%d-%m-%y %I-%M-%S %p")
    
    # Get file extension and rename it
    ext = os.path.splitext(file.filename)[1].lower()
    if not allowed_file(file.filename):
        logger.error(f"File type {ext} is not allowed")
        return jsonify({"error": f"File type {ext} is not allowed"}), 400

    new_filename = f"{timestamp}{ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    
    try:
        file.save(file_path)
        logger.info(f"File saved: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {str(e)}")
        return jsonify({"error": "Failed to save file"}), 500

    # Generate a thumbnail if the uploaded file is a video
    thumb_filename = f"{timestamp}.jpg"
    thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
    
    if allowed_file(new_filename):
        success = generate_thumbnail(file_path, thumb_path)
        if not success:
            return jsonify({"error": "Failed to generate thumbnail"}), 500

    return jsonify({"message": f"File uploaded successfully as {new_filename}!"})

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
