"""
YouTube platform handler for video downloading.
"""
import os
import yt_dlp
from .base import BasePlatformHandler

class YouTubeHandler(BasePlatformHandler):
    """
    Handler for YouTube video downloading.
    """
    
    def __init__(self):
        """Initialize YouTube handler with default options."""
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': False,
            # Add cookies.txt support
            'cookiefile': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cookies.txt'),
        }
    
    def extract_info(self, url):
        """
        Extract video information from YouTube URL.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            dict: Video information including title, thumbnail, formats, etc.
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Process and clean up the information
                if info:
                    return {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'description': info.get('description'),
                        'thumbnail': info.get('thumbnail'),
                        'duration': info.get('duration'),
                        'uploader': info.get('uploader'),
                        'view_count': info.get('view_count'),
                        'formats': self._process_formats(info.get('formats', [])),
                        'platform': 'youtube',
                        'url': url,
                        'success': True
                    }
                else:
                    return {'success': False, 'error': 'Failed to extract video information'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download(self, url, output_path, format_id=None):
        """
        Download video from YouTube URL.
        
        Args:
            url (str): YouTube video URL
            output_path (str): Path to save the downloaded video
            format_id (str, optional): Specific format ID to download
            
        Returns:
            dict: Download result information
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Set download options
            download_opts = self.ydl_opts.copy()
            download_opts.update({
                'outtmpl': output_path,
                'progress_hooks': [self._progress_hook],
            })
            
            # Add format selection if specified
            if format_id:
                download_opts['format'] = format_id
            else:
                # Default to best video+audio
                download_opts['format'] = 'bestvideo+bestaudio/best'
                
            # Download the video
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    return {
                        'success': True,
                        'file_path': output_path,
                        'title': info.get('title'),
                        'format': format_id or 'best',
                        'platform': 'youtube'
                    }
                else:
                    return {'success': False, 'error': 'Download failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_available_formats(self, url):
        """
        Get available formats for the YouTube video.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            list: List of available formats
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and 'formats' in info:
                    return self._process_formats(info['formats'])
                else:
                    return []
        except Exception:
            return []
    
    def _process_formats(self, formats):
        """
        Process and filter formats for better presentation.
        
        Args:
            formats (list): List of format dictionaries from yt-dlp
            
        Returns:
            list: Processed and filtered format list
        """
        processed_formats = []
        
        # Filter and process formats
        for fmt in formats:
            if not fmt.get('format_id'):
                continue
                
            # Create a clean format entry
            format_entry = {
                'format_id': fmt.get('format_id'),
                'ext': fmt.get('ext'),
                'resolution': fmt.get('resolution', 'unknown'),
                'fps': fmt.get('fps'),
                'vcodec': fmt.get('vcodec'),
                'acodec': fmt.get('acodec'),
                'filesize': fmt.get('filesize'),
                'format_note': fmt.get('format_note', ''),
                'quality': fmt.get('quality', 0),
                'tbr': fmt.get('tbr'),  # Total bitrate
            }
            
            # Add a human-readable description
            format_entry['description'] = self._format_description(fmt)
            
            processed_formats.append(format_entry)
        
        # Sort by quality (higher first)
        return sorted(processed_formats, key=lambda x: x.get('quality', 0), reverse=True)
    
    def _format_description(self, fmt):
        """
        Create a human-readable format description.
        
        Args:
            fmt (dict): Format dictionary from yt-dlp
            
        Returns:
            str: Human-readable description
        """
        parts = []
        
        # Add resolution if available
        if fmt.get('resolution') and fmt.get('resolution') != 'audio only':
            parts.append(fmt.get('resolution'))
        
        # Add format note if available
        if fmt.get('format_note') and fmt.get('format_note') != 'Default':
            parts.append(fmt.get('format_note'))
        
        # Add codec info for video
        if fmt.get('vcodec') and fmt.get('vcodec') != 'none':
            parts.append(f"Video: {fmt.get('vcodec', 'unknown')}")
        
        # Add codec info for audio
        if fmt.get('acodec') and fmt.get('acodec') != 'none':
            parts.append(f"Audio: {fmt.get('acodec', 'unknown')}")
        
        # Add file extension
        if fmt.get('ext'):
            parts.append(f".{fmt.get('ext')}")
        
        # Add filesize if available
        if fmt.get('filesize'):
            size_mb = fmt.get('filesize') / (1024 * 1024)
            parts.append(f"{size_mb:.1f} MB")
        
        return ' - '.join(parts)
    
    def _progress_hook(self, d):
        """
        Progress hook for download tracking.
        
        Args:
            d (dict): Progress information from yt-dlp
        """
        # This can be expanded to track download progress
        # Currently just a placeholder for future implementation
        pass
