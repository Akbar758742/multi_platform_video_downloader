"""
Base platform handler interface for video downloading.
"""
from abc import ABC, abstractmethod

class BasePlatformHandler(ABC):
    """
    Abstract base class for all platform-specific video handlers.
    """
    
    @abstractmethod
    def extract_info(self, url):
        """
        Extract video information from the URL.
        
        Args:
            url (str): URL of the video
            
        Returns:
            dict: Video information including title, thumbnail, formats, etc.
        """
        pass
    
    @abstractmethod
    def download(self, url, output_path, format_id=None):
        """
        Download video from the URL.
        
        Args:
            url (str): URL of the video
            output_path (str): Path to save the downloaded video
            format_id (str, optional): Specific format ID to download
            
        Returns:
            dict: Download result information
        """
        pass
    
    @abstractmethod
    def get_available_formats(self, url):
        """
        Get available formats for the video.
        
        Args:
            url (str): URL of the video
            
        Returns:
            list: List of available formats
        """
        pass
