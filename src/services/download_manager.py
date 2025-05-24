"""
Download Manager for handling video downloads.
"""
import os
import uuid
import time
from threading import Thread, Lock
from datetime import datetime

class DownloadManager:
    """
    Manager for handling video downloads, tracking progress, and managing download tasks.
    """
    
    def __init__(self, download_dir):
        """
        Initialize the download manager.
        
        Args:
            download_dir (str): Directory to store downloaded videos
        """
        self.download_dir = download_dir
        self.tasks = {}  # Dictionary to store download tasks
        self.tasks_lock = Lock()  # Lock for thread-safe operations on tasks
        
        # Ensure download directory exists
        os.makedirs(download_dir, exist_ok=True)
    
    def create_task(self, url, platform, format_id=None):
        """
        Create a new download task.
        
        Args:
            url (str): URL of the video to download
            platform (str): Platform of the video (youtube, facebook, etc.)
            format_id (str, optional): Specific format ID to download
            
        Returns:
            str: Task ID for tracking the download
        """
        task_id = str(uuid.uuid4())
        
        with self.tasks_lock:
            self.tasks[task_id] = {
                'id': task_id,
                'url': url,
                'platform': platform,
                'format_id': format_id,
                'status': 'created',
                'progress': 0,
                'created_at': datetime.now().isoformat(),
                'started_at': None,
                'completed_at': None,
                'file_path': None,
                'error': None
            }
        
        return task_id
    
    def start_download(self, task_id, platform_handler):
        """
        Start a download task in a separate thread.
        
        Args:
            task_id (str): ID of the task to start
            platform_handler (BasePlatformHandler): Handler for the specific platform
            
        Returns:
            bool: True if task started successfully, False otherwise
        """
        if task_id not in self.tasks:
            return False
        
        # Update task status
        with self.tasks_lock:
            self.tasks[task_id]['status'] = 'starting'
            self.tasks[task_id]['started_at'] = datetime.now().isoformat()
        
        # Start download in a separate thread
        thread = Thread(target=self._download_thread, args=(task_id, platform_handler))
        thread.daemon = True
        thread.start()
        
        return True
    
    def _download_thread(self, task_id, platform_handler):
        """
        Thread function for downloading a video.
        
        Args:
            task_id (str): ID of the task
            platform_handler (BasePlatformHandler): Handler for the specific platform
        """
        try:
            # Get task information
            with self.tasks_lock:
                task = self.tasks[task_id]
                url = task['url']
                format_id = task['format_id']
                self.tasks[task_id]['status'] = 'extracting'
            
            # Extract video information
            info = platform_handler.extract_info(url)
            
            if not info['success']:
                with self.tasks_lock:
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['error'] = info.get('error', 'Failed to extract video information')
                    self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
                return
            
            # Generate output path
            title = info.get('title', 'video')
            # Clean title for filename
            title = ''.join(c for c in title if c.isalnum() or c in ' ._-').strip()
            title = title[:50]  # Limit title length
            
            timestamp = int(time.time())
            filename = f"{title}_{timestamp}.mp4"
            output_path = os.path.join(self.download_dir, filename)
            
            # Update task status
            with self.tasks_lock:
                self.tasks[task_id]['status'] = 'downloading'
                self.tasks[task_id]['title'] = info.get('title')
                self.tasks[task_id]['thumbnail'] = info.get('thumbnail')
            
            # Download the video
            result = platform_handler.download(url, output_path, format_id)
            
            # Update task status based on download result
            with self.tasks_lock:
                if result['success']:
                    self.tasks[task_id]['status'] = 'completed'
                    self.tasks[task_id]['file_path'] = result['file_path']
                    self.tasks[task_id]['progress'] = 100
                else:
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['error'] = result.get('error', 'Download failed')
                
                self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
        
        except Exception as e:
            # Handle any unexpected errors
            with self.tasks_lock:
                self.tasks[task_id]['status'] = 'failed'
                self.tasks[task_id]['error'] = str(e)
                self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
    
    def get_task(self, task_id):
        """
        Get information about a specific task.
        
        Args:
            task_id (str): ID of the task
            
        Returns:
            dict: Task information or None if task not found
        """
        with self.tasks_lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self):
        """
        Get information about all tasks.
        
        Returns:
            list: List of all tasks
        """
        with self.tasks_lock:
            return list(self.tasks.values())
    
    def clean_old_tasks(self, max_age_hours=24):
        """
        Clean up old completed or failed tasks.
        
        Args:
            max_age_hours (int): Maximum age of tasks to keep in hours
            
        Returns:
            int: Number of tasks cleaned
        """
        current_time = datetime.now()
        cleaned_count = 0
        
        with self.tasks_lock:
            task_ids = list(self.tasks.keys())
            
            for task_id in task_ids:
                task = self.tasks[task_id]
                
                # Skip tasks that are not completed or failed
                if task['status'] not in ['completed', 'failed']:
                    continue
                
                # Check if task is old enough to clean
                completed_at = datetime.fromisoformat(task['completed_at']) if task['completed_at'] else None
                
                if completed_at and (current_time - completed_at).total_seconds() > max_age_hours * 3600:
                    del self.tasks[task_id]
                    cleaned_count += 1
        
        return cleaned_count
    
    def cancel_task(self, task_id):
        """
        Cancel a download task.
        
        Args:
            task_id (str): ID of the task to cancel
            
        Returns:
            bool: True if task was cancelled, False otherwise
        """
        with self.tasks_lock:
            if task_id in self.tasks and self.tasks[task_id]['status'] in ['created', 'starting', 'extracting', 'downloading']:
                self.tasks[task_id]['status'] = 'cancelled'
                self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
                return True
            return False
