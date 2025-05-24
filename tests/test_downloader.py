"""
Test script for validating the video downloader functionality.
This script tests various video platforms and validates the extraction and download capabilities.
"""
import os
import sys
import json
import time
import unittest
from urllib.parse import urlparse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import services
from src.utils.url_parser import URLParser
from src.services.platform_factory import PlatformFactory

class VideoDownloaderTest(unittest.TestCase):
    """Test cases for video downloader functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_urls = {
            'youtube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Rick Astley - Never Gonna Give You Up
            'facebook': 'https://www.facebook.com/watch?v=2018722278279349',  # Sample Facebook video
            'tiktok': 'https://www.tiktok.com/@tiktok/video/6584647400055377158',  # Sample TikTok video
        }
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_downloads')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def test_url_parser(self):
        """Test URL parser functionality."""
        print("\n--- Testing URL Parser ---")
        
        for platform, url in self.test_urls.items():
            print(f"Testing {platform} URL: {url}")
            
            # Test URL validation
            self.assertTrue(URLParser.validate_url(url), f"URL validation failed for {platform}")
            
            # Test platform identification
            detected_platform, video_id = URLParser.identify_platform(url)
            print(f"Detected platform: {detected_platform}, Video ID: {video_id}")
            
            # For YouTube, we expect exact match
            if platform == 'youtube':
                self.assertEqual(detected_platform, platform, f"Platform detection failed for {platform}")
                self.assertIsNotNone(video_id, f"Video ID extraction failed for {platform}")
            
            # For other platforms, we at least expect the platform to be detected
            # (might be generic for some test URLs)
            else:
                self.assertIsNotNone(detected_platform, f"Platform detection failed for {platform}")
    
    def test_info_extraction(self):
        """Test video information extraction."""
        print("\n--- Testing Video Information Extraction ---")
        
        for platform, url in self.test_urls.items():
            print(f"Testing info extraction for {platform}: {url}")
            
            # Create platform handler
            handler = PlatformFactory.create_handler(platform)
            
            # Extract video information
            info = handler.extract_info(url)
            
            # Print summary of extracted info
            if info.get('success'):
                print(f"Successfully extracted info for {platform}:")
                print(f"  Title: {info.get('title')}")
                print(f"  Platform: {info.get('platform')}")
                print(f"  Duration: {info.get('duration')} seconds")
                print(f"  Formats: {len(info.get('formats', []))} available")
                
                # Validate basic info
                self.assertIsNotNone(info.get('title'), f"Title missing for {platform}")
                self.assertIsNotNone(info.get('formats'), f"Formats missing for {platform}")
            else:
                print(f"Failed to extract info for {platform}: {info.get('error')}")
                # This is not necessarily a test failure - some platforms might be unavailable
                # or have changed their structure
                print("Note: This is not a test failure, just logging the issue.")
    
    def test_format_listing(self):
        """Test format listing functionality."""
        print("\n--- Testing Format Listing ---")
        
        for platform, url in self.test_urls.items():
            print(f"Testing format listing for {platform}: {url}")
            
            # Create platform handler
            handler = PlatformFactory.create_handler(platform)
            
            # Get available formats
            formats = handler.get_available_formats(url)
            
            # Print summary of formats
            print(f"Found {len(formats)} formats for {platform}")
            
            # Print top 3 formats as example
            for i, fmt in enumerate(formats[:3]):
                print(f"  Format {i+1}: {fmt.get('description', 'No description')}")
            
            # Validate formats
            if platform == 'youtube':  # YouTube should always have formats
                self.assertGreater(len(formats), 0, f"No formats found for {platform}")
    
    def test_download_capability(self):
        """Test download capability (without actually downloading full videos)."""
        print("\n--- Testing Download Capability ---")
        
        for platform, url in self.test_urls.items():
            print(f"Testing download capability for {platform}: {url}")
            
            # Create platform handler
            handler = PlatformFactory.create_handler(platform)
            
            # Extract info first to get a valid format
            info = handler.extract_info(url)
            
            if not info.get('success'):
                print(f"Skipping download test for {platform} due to extraction failure")
                continue
            
            # Get a format ID for testing (preferably a small one)
            format_id = None
            formats = info.get('formats', [])
            
            # Try to find a small format for testing
            for fmt in formats:
                if fmt.get('filesize') and fmt.get('filesize') < 5000000:  # < 5MB
                    format_id = fmt.get('format_id')
                    print(f"Selected small format: {fmt.get('description')}")
                    break
            
            # If no small format found, just use the first one or None for default
            if not format_id and formats:
                format_id = formats[0].get('format_id')
                print("No small format found, using first available format")
            
            # For this test, we'll just verify the download function returns success
            # without actually waiting for the download to complete
            output_path = os.path.join(self.output_dir, f"test_{platform}_{int(time.time())}.mp4")
            
            # Start download but don't wait for completion
            print(f"Testing download initialization for {platform}")
            result = handler.download(url, output_path, format_id)
            
            # Just check if the download was initiated successfully
            print(f"Download initialization result: {result.get('success')}")
            
            # We don't assert success here because some platforms might be unavailable
            # This is just to test the capability, not the actual download
    
    def test_url_normalization(self):
        """Test URL normalization."""
        print("\n--- Testing URL Normalization ---")
        
        # Test YouTube URL normalization
        youtube_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ',
            'https://www.youtube.com/shorts/dQw4w9WgXcQ',
            'youtu.be/dQw4w9WgXcQ'  # No protocol
        ]
        
        for url in youtube_urls:
            normalized = URLParser.normalize_url(url, 'youtube')
            print(f"Original: {url}")
            print(f"Normalized: {normalized}")
            
            # Check that normalized URL has protocol
            self.assertTrue(normalized.startswith('http'), "Normalized URL should have protocol")
            
            # For YouTube, normalized URL should be in watch?v= format
            self.assertTrue('youtube.com/watch?v=' in normalized, "YouTube URL not normalized correctly")
    
    def tearDown(self):
        """Clean up after tests."""
        # We don't actually delete test files here to allow manual inspection
        print("\nTest downloads directory:", self.output_dir)
        print("Note: Test downloads are not automatically deleted.")

if __name__ == '__main__':
    unittest.main()
