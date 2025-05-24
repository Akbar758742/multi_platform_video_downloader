"""
URL Parser module for identifying and validating video URLs from different platforms.
"""
import re
import validators
from urllib.parse import urlparse, parse_qs

class URLParser:
    """
    Class for parsing and identifying video URLs from different platforms.
    """
    
    # Platform identification patterns
    PATTERNS = {
        'youtube': [
            r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})'
        ],
        'facebook': [
            r'(?:https?:\/\/)?(?:www\.|web\.|m\.)?facebook\.com\/(?:watch\/\?v=|video\.php\?v=|video\/video\.php\?v=|.*?\/videos\/|reel\/)(\d+)',
            r'(?:https?:\/\/)?(?:www\.|web\.|m\.)?fb\.watch\/([a-zA-Z0-9_-]+)'
        ],
        'tiktok': [
            r'(?:https?:\/\/)?(?:www\.)?tiktok\.com\/@[^\/]+\/video\/(\d+)',
            r'(?:https?:\/\/)?(?:www\.)?vm\.tiktok\.com\/([a-zA-Z0-9_-]+)'
        ],
        'instagram': [
            r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel)\/([a-zA-Z0-9_-]+)',
            r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/tv\/([a-zA-Z0-9_-]+)'
        ],
        'twitter': [
            r'(?:https?:\/\/)?(?:www\.)?twitter\.com\/(?:\w+)\/status\/(\d+)',
            r'(?:https?:\/\/)?(?:www\.)?x\.com\/(?:\w+)\/status\/(\d+)'
        ],
        'vimeo': [
            r'(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(\d+)'
        ],
        'dailymotion': [
            r'(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/video\/([a-zA-Z0-9]+)'
        ]
    }
    
    @staticmethod
    def validate_url(url):
        """
        Validate if the provided string is a valid URL.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if valid URL, False otherwise
        """
        return validators.url(url) is True
    
    @staticmethod
    def identify_platform(url):
        """
        Identify the platform from the given URL.
        
        Args:
            url (str): URL to identify
            
        Returns:
            tuple: (platform_name, video_id) or (None, None) if not identified
        """
        if not URLParser.validate_url(url):
            return None, None
        
        # Check each platform's patterns
        for platform, patterns in URLParser.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return platform, match.group(1)
        
        # If no specific pattern matches, try to determine from domain
        domain = urlparse(url).netloc
        
        # Extract base domain (e.g., youtube.com from www.youtube.com)
        base_domain = '.'.join(domain.split('.')[-2:]) if len(domain.split('.')) > 1 else domain
        
        # Check if base domain matches any platform
        for platform in URLParser.PATTERNS.keys():
            if platform in base_domain:
                return platform, None
        
        # If no platform identified, return generic
        return 'generic', None
    
    @staticmethod
    def extract_query_params(url):
        """
        Extract query parameters from URL.
        
        Args:
            url (str): URL to extract parameters from
            
        Returns:
            dict: Dictionary of query parameters
        """
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query)
    
    @staticmethod
    def normalize_url(url, platform=None):
        """
        Normalize URL for consistent processing.
        
        Args:
            url (str): URL to normalize
            platform (str, optional): Platform if already identified
            
        Returns:
            str: Normalized URL
        """
        if not platform:
            platform, _ = URLParser.identify_platform(url)
        
        # Platform-specific normalization
        if platform == 'youtube':
            # Convert youtu.be to youtube.com
            if 'youtu.be' in url:
                video_id = url.split('/')[-1].split('?')[0]
                return f"https://www.youtube.com/watch?v={video_id}"
            
            # Convert shorts to regular video URL
            if '/shorts/' in url:
                video_id = url.split('/shorts/')[1].split('?')[0]
                return f"https://www.youtube.com/watch?v={video_id}"
        
        # Add more platform-specific normalizations as needed
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        return url
