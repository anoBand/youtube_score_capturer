import os
import tempfile
import shutil
import traceback
from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS

# Import custom modules
from modules.youtube_downloader import download_youtube_video
from modules.image_processor import process_video_frames
from modules.pdf_generator import create_pdf_from_images

# Beanstalk looks for a variable named 'application'.
application = Flask(__name__)
CORS(application)

# Define a base temp directory within the project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_BASE_DIR = os.path.join(PROJECT_ROOT, 'temp')

@application.route('/')
def index():
    # Renders the main page.
    return render_template('index.html')

def time_to_seconds(time_str):
    """Converts time string in HH:MM:SS or MM:SS to seconds."""
    if not time_str:
        return None
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]
    except (ValueError, IndexError):
        # Return None or raise an error if format is invalid
        return None

@application.route('/execute', methods=['POST'])
def execute():
    # Clean up old temp directories first, then create the base temp dir
    if os.path.exists(TEMP_BASE_DIR):
        shutil.rmtree(TEMP_BASE_DIR)
    os.makedirs(TEMP_BASE_DIR)
    
    # Create a unique temporary directory for this request
    temp_dir = tempfile.mkdtemp(dir=TEMP_BASE_DIR)
    print(f"Created temporary directory: {temp_dir}")

    try:
        data = request.form
        youtube_url = data.get('url')
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required.'}), 400

        # Extract and convert parameters, handling empty strings
        start_time = time_to_seconds(data.get('start_time'))
        end_time = time_to_seconds(data.get('end_time'))
        
        x_start = int(data.get('x_start') or 0)
        x_end = int(data.get('x_end') or 100)
        y_start = int(data.get('y_start') or 0)
        y_end = int(data.get('y_end') or 100)
        threshold = float(data.get('threshold') or 5.0)
        transition_sec = float(data.get('transition_sec') or 2.0)
        frame_interval_sec = float(data.get('frame_interval_sec') or 0.5)

        # 1. Download YouTube video
        video_path = download_youtube_video(youtube_url, temp_dir, start_time, end_time)
        
        # 2. Process video frames with OpenCV
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)
        processed_image_paths = process_video_frames(
            video_path, 
            image_output_dir, 
            x_start, x_end, y_start, y_end, 
            threshold, transition_sec, frame_interval_sec
        )
        
        if not processed_image_paths:
            raise ValueError("Could not extract sheet music images from the video.")

        # 3. Create PDF in memory
        pdf_io = create_pdf_from_images(processed_image_paths)
        
        # 4. Send the generated PDF file from memory
        return send_file(
            pdf_io,
            as_attachment=True,
            download_name='sheet_music.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        # 5. Clean up the temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")

if __name__ == '__main__':
    # Run the server for local testing
    application.run(host='0.0.0.0', port=5000, debug=True)
