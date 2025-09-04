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

@application.route('/')
def index():
    # Renders the main page.
    return render_template('index.html')

@application.route('/process', methods=['POST'])
def process_video():
    # Executes the sheet music extraction process from a YouTube URL.
    # Extract parameters from the request
    params = request.form.to_dict()
    youtube_url = params.get('url')

    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required.'}), 400

    # Create a temporary directory for each request
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")

    try:
        # 1. Download YouTube video
        video_path = download_youtube_video(youtube_url, temp_dir)
        
        # 2. Process video frames with OpenCV
        # Specify output_dir under temp_dir to save intermediate images
        image_output_dir = os.path.join(temp_dir, 'images')
        os.makedirs(image_output_dir)
        processed_image_paths = process_video_frames(video_path, image_output_dir, params)
        
        if not processed_image_paths:
            raise ValueError("Could not extract sheet music images from the video.")

        # 3. Create PDF
        pdf_path = create_pdf_from_images(processed_image_paths, temp_dir, filename="sheet_music.pdf")
        
        # 4. Send the generated PDF file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name='sheet_music.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        # Log the error
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        # 5. Clean up the temporary directory after all operations are complete
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")

if __name__ == '__main__':
    # Run the server for local testing
    application.run(host='0.0.0.0', port=5000, debug=True)
