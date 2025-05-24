"""
Main Flask application for the video downloader website.
"""
import os
import sys
import json
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import services
from src.utils.url_parser import URLParser
from src.services.platform_factory import PlatformFactory
from src.services.download_manager import DownloadManager

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure app
app.config['DOWNLOAD_DIR'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'downloads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Create download directory if it doesn't exist
os.makedirs(app.config['DOWNLOAD_DIR'], exist_ok=True)

# Initialize download manager
download_manager = DownloadManager(app.config['DOWNLOAD_DIR'])

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/extract', methods=['POST'])
def extract_video_info():
    """
    Extract video information from URL.
    
    Request JSON:
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
    """
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    url = data['url']
    
    # Validate URL
    if not URLParser.validate_url(url):
        return jsonify({'success': False, 'error': 'Invalid URL'}), 400
    
    # Identify platform
    platform, video_id = URLParser.identify_platform(url)
    
    # Normalize URL
    url = URLParser.normalize_url(url, platform)
    
    # Create platform handler
    handler = PlatformFactory.create_handler(platform)
    try:
        # Extract video information
        info = handler.extract_info(url)
        return jsonify(info)
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def start_download():
    """
    Start video download.
    
    Request JSON:
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID",
        "format_id": "22"  # Optional
    }
    """
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    url = data['url']
    format_id = data.get('format_id')
    
    # Validate URL
    if not URLParser.validate_url(url):
        return jsonify({'success': False, 'error': 'Invalid URL'}), 400
    
    # Identify platform
    platform, video_id = URLParser.identify_platform(url)
    
    # Normalize URL
    url = URLParser.normalize_url(url, platform)
    
    # Create task
    task_id = download_manager.create_task(url, platform, format_id)
    
    # Create platform handler
    handler = PlatformFactory.create_handler(platform)
    
    # Start download
    download_manager.start_download(task_id, handler)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': 'Download started'
    })

@app.route('/api/status/<task_id>', methods=['GET'])
def get_download_status(task_id):
    """Get download status for a specific task."""
    task = download_manager.get_task(task_id)
    
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    
    return jsonify({
        'success': True,
        'task': task
    })

@app.route('/api/downloads', methods=['GET'])
def get_all_downloads():
    """Get all download tasks."""
    tasks = download_manager.get_all_tasks()
    
    return jsonify({
        'success': True,
        'tasks': tasks
    })

@app.route('/api/cancel/<task_id>', methods=['POST'])
def cancel_download(task_id):
    """Cancel a download task."""
    result = download_manager.cancel_task(task_id)
    
    if result:
        return jsonify({
            'success': True,
            'message': 'Download cancelled'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to cancel download or task not found'
        }), 400

@app.route('/api/download/<task_id>', methods=['GET'])
def download_file(task_id):
    """Download the completed file."""
    task = download_manager.get_task(task_id)
    
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    
    if task['status'] != 'completed':
        return jsonify({'success': False, 'error': 'Download not completed'}), 400
    
    if not task['file_path'] or not os.path.exists(task['file_path']):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    directory = os.path.dirname(task['file_path'])
    filename = os.path.basename(task['file_path'])
    
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/api/formats', methods=['POST'])
def get_available_formats():
    """
    Get available formats for a video.
    
    Request JSON:
    {
        "url": "https://www.youtube.com/watch?v=VIDEO_ID"
    }
    """
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    url = data['url']
    
    # Validate URL
    if not URLParser.validate_url(url):
        return jsonify({'success': False, 'error': 'Invalid URL'}), 400
    
    # Identify platform
    platform, video_id = URLParser.identify_platform(url)
    
    # Normalize URL
    url = URLParser.normalize_url(url, platform)
    
    # Create platform handler
    handler = PlatformFactory.create_handler(platform)
    
    # Get available formats
    formats = handler.get_available_formats(url)
    
    return jsonify({
        'success': True,
        'formats': formats
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
