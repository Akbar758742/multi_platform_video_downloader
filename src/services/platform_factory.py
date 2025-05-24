"""
Platform factory for creating appropriate platform handlers.
"""
from .platforms.youtube import YouTubeHandler
from .platforms.facebook import FacebookHandler
from .platforms.tiktok import TikTokHandler
from .platforms.generic import GenericHandler

class PlatformFactory:
    """
    Factory class for creating platform-specific handlers.
    """
    
    @staticmethod
    def create_handler(platform):
        """
        Create and return a handler for the specified platform.
        
        Args:
            platform (str): Platform identifier (youtube, facebook, tiktok, etc.)
            
        Returns:
            BasePlatformHandler: Platform-specific handler instance
        """
        platform = platform.lower() if platform else 'generic'
        
        if platform == 'youtube':
            return YouTubeHandler()
        elif platform == 'facebook':
            return FacebookHandler()
        elif platform == 'tiktok':
            return TikTokHandler()
        else:
            # Use generic handler for unsupported platforms
            return GenericHandler()
