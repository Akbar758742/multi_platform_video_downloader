"""
Facebook platform handler for video downloading.
"""
import os
import re
import requests
from bs4 import BeautifulSoup
import yt_dlp
from .base import BasePlatformHandler

class FacebookHandler(BasePlatformHandler):
    """
    Handler for Facebook video downloading.
    """
    
    def __init__(self):
        """Initialize Facebook handler with default options."""
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': False,
        }
        
        # Headers for requests to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    def extract_info(self, url):
        """
        Extract video information from Facebook URL.
        
        Args:
            url (str): Facebook video URL
            
        Returns:
            dict: Video information including title, thumbnail, formats, etc.
        """
        try:
            # Use yt-dlp for extraction as it handles Facebook well
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
                        'formats': self._process_formats(info.get('formats', [])),
                        'platform': 'facebook',
                        'url': url,
                        'success': True
                    }
                else:
                    # Fallback to custom extraction if yt-dlp fails
                    return self._fallback_extract(url)
        except Exception as e:
            # Try fallback method if yt-dlp fails
            try:
                return self._fallback_extract(url)
            except Exception as inner_e:
                return {'success': False, 'error': f"Primary extraction failed: {str(e)}. Fallback failed: {str(inner_e)}"}
    
    def _fallback_extract(self, url):
        """
        Fallback method to extract video information using requests and BeautifulSoup.
        
        Args:
            url (str): Facebook video URL
            
        Returns:
            dict: Video information
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to extract title
            title = soup.find('title').text if soup.find('title') else 'Facebook Video'
            
            # Try to extract video ID from URL
            video_id = None
            if 'watch' in url:
                video_id = re.search(r'v=(\d+)', url)
                if video_id:
                    video_id = video_id.group(1)
            elif 'videos' in url:
                video_id = url.split('/')[-1].split('?')[0]
            
            return {
                'id': video_id,
                'title': title,
                'description': 'No description available',
                'thumbnail': None,
                'platform': 'facebook',
                'url': url,
                'formats': [],  # No formats available in fallback mode
                'success': True,
                'fallback': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download(self, url, output_path, format_id=None):
        """
        Download video from Facebook URL.
        
        Args:
            url (str): Facebook video URL
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
                        'platform': 'facebook'
                    }
                else:
                    return {'success': False, 'error': 'Download failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_available_formats(self, url):
        """
        Get available formats for the Facebook video.
        
        Args:
            url (str): Facebook video URL
            
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
