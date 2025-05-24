// Main JavaScript for Video Downloader

// DOM Elements
const videoUrlInput = document.getElementById('video-url');
const extractBtn = document.getElementById('extract-btn');
const platformIndicator = document.getElementById('platform-indicator');
const platformIcon = document.querySelector('.platform-icon i');
const platformText = document.querySelector('.platform-text');
const videoInfoSection = document.getElementById('video-info-section');
const infoLoader = document.getElementById('info-loader');
const videoDetails = document.getElementById('video-details');
const videoThumbnail = document.getElementById('video-thumbnail');
const videoTitle = document.getElementById('video-title');
const videoUploader = document.getElementById('video-uploader').querySelector('span');
const videoDuration = document.getElementById('video-duration').querySelector('span');
const formatSelect = document.getElementById('format-select');
const downloadBtn = document.getElementById('download-btn');
const downloadStatusSection = document.getElementById('download-status-section');
const downloadProgressBar = document.getElementById('download-progress-bar');
const downloadProgressText = document.getElementById('download-progress-text');
const downloadStatusMessage = document.getElementById('download-status-message');
const cancelBtn = document.getElementById('cancel-btn');
const downloadLink = document.getElementById('download-link');

// Global variables
let currentVideoInfo = null;
let currentTaskId = null;
let statusCheckInterval = null;

// Platform icons mapping
const platformIcons = {
    'youtube': 'fab fa-youtube',
    'facebook': 'fab fa-facebook',
    'tiktok': 'fab fa-tiktok',
    'instagram': 'fab fa-instagram',
    'twitter': 'fab fa-twitter',
    'vimeo': 'fab fa-vimeo',
    'dailymotion': 'fas fa-play-circle',
    'generic': 'fas fa-globe'
};

// Initialize the application
function init() {
    // Hide sections initially
    videoInfoSection.style.display = 'none';
    downloadStatusSection.style.display = 'none';
    videoDetails.style.display = 'none';
    infoLoader.style.display = 'none';
    downloadLink.style.display = 'none';
    
    // Add event listeners
    videoUrlInput.addEventListener('input', handleUrlInput);
    extractBtn.addEventListener('click', extractVideoInfo);
    downloadBtn.addEventListener('click', startDownload);
    cancelBtn.addEventListener('click', cancelDownload);
    
    // Focus on URL input
    videoUrlInput.focus();
}

// Handle URL input for platform detection
function handleUrlInput() {
    const url = videoUrlInput.value.trim();
    
    if (url) {
        // Simple platform detection based on URL
        if (url.includes('youtube.com') || url.includes('youtu.be')) {
            updatePlatformIndicator('youtube', 'YouTube');
        } else if (url.includes('facebook.com') || url.includes('fb.watch')) {
            updatePlatformIndicator('facebook', 'Facebook');
        } else if (url.includes('tiktok.com')) {
            updatePlatformIndicator('tiktok', 'TikTok');
        } else if (url.includes('instagram.com')) {
            updatePlatformIndicator('instagram', 'Instagram');
        } else if (url.includes('twitter.com') || url.includes('x.com')) {
            updatePlatformIndicator('twitter', 'Twitter/X');
        } else if (url.includes('vimeo.com')) {
            updatePlatformIndicator('vimeo', 'Vimeo');
        } else if (url.includes('dailymotion.com')) {
            updatePlatformIndicator('dailymotion', 'Dailymotion');
        } else if (url.startsWith('http')) {
            updatePlatformIndicator('generic', 'Other Platform');
        } else {
            updatePlatformIndicator('generic', 'Waiting for URL...');
        }
    } else {
        updatePlatformIndicator('generic', 'Waiting for URL...');
    }
}

// Update platform indicator
function updatePlatformIndicator(platform, text) {
    platformIcon.className = platformIcons[platform] || 'fas fa-globe';
    platformText.textContent = text;
}

// Extract video information
async function extractVideoInfo() {
    const url = videoUrlInput.value.trim();
    
    if (!url) {
        showError('Please enter a video URL');
        return;
    }
    
    // Show video info section and loader
    videoInfoSection.style.display = 'block';
    infoLoader.style.display = 'flex';
    videoDetails.style.display = 'none';
    
    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Store video info
            currentVideoInfo = data;
            
            // Display video information
            displayVideoInfo(data);
        } else {
            showError(data.error || 'Failed to extract video information');
            infoLoader.style.display = 'none';
        }
    } catch (error) {
        showError('Error connecting to server');
        infoLoader.style.display = 'none';
    }
}

// Display video information
function displayVideoInfo(info) {
    // Hide loader and show details
    infoLoader.style.display = 'none';
    videoDetails.style.display = 'flex';
    
    // Set thumbnail
    if (info.thumbnail) {
        videoThumbnail.src = info.thumbnail;
        videoThumbnail.alt = info.title || 'Video Thumbnail';
    } else {
        videoThumbnail.src = '/static/img/no-thumbnail.jpg';
        videoThumbnail.alt = 'No Thumbnail Available';
    }
    
    // Set title and metadata
    videoTitle.textContent = info.title || 'Unknown Title';
    videoUploader.textContent = info.uploader || 'Unknown';
    
    // Format duration
    if (info.duration) {
        const minutes = Math.floor(info.duration / 60);
        const seconds = info.duration % 60;
        videoDuration.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    } else {
        videoDuration.textContent = 'Unknown';
    }
    
    // Populate format select
    formatSelect.innerHTML = '<option value="">Best Quality (Default)</option>';
    
    if (info.formats && info.formats.length > 0) {
        // Add formats to select
        info.formats.forEach(format => {
            const option = document.createElement('option');
            option.value = format.format_id;
            option.textContent = format.description || `Format ${format.format_id}`;
            formatSelect.appendChild(option);
        });
    }
    
    // Update platform indicator with more accurate info
    updatePlatformIndicator(info.platform || 'generic', info.platform ? info.platform.charAt(0).toUpperCase() + info.platform.slice(1) : 'Unknown Platform');
}

// Start download
async function startDownload() {
    if (!currentVideoInfo) {
        showError('Please extract video information first');
        return;
    }
    
    const url = currentVideoInfo.url;
    const formatId = formatSelect.value || null;
    
    // Show download status section
    downloadStatusSection.style.display = 'block';
    downloadProgressBar.style.width = '0%';
    downloadProgressText.textContent = '0%';
    downloadStatusMessage.textContent = 'Starting download...';
    downloadLink.style.display = 'none';
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url, format_id: formatId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentTaskId = data.task_id;
            downloadStatusMessage.textContent = 'Download initiated. Processing...';
            
            // Start checking status
            startStatusCheck();
        } else {
            downloadStatusMessage.textContent = `Error: ${data.error || 'Failed to start download'}`;
        }
    } catch (error) {
        downloadStatusMessage.textContent = 'Error connecting to server';
    }
}

// Start checking download status
function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    // Check immediately
    checkDownloadStatus();
    
    // Then check every 2 seconds
    statusCheckInterval = setInterval(checkDownloadStatus, 2000);
}

// Check download status
async function checkDownloadStatus() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/status/${currentTaskId}`);
        const data = await response.json();
        
        if (data.success && data.task) {
            updateDownloadStatus(data.task);
        } else {
            downloadStatusMessage.textContent = 'Error: Could not retrieve download status';
        }
    } catch (error) {
        downloadStatusMessage.textContent = 'Error connecting to server';
    }
}

// Update download status display
function updateDownloadStatus(task) {
    const status = task.status;
    
    // Update status message
    switch (status) {
        case 'created':
            downloadStatusMessage.textContent = 'Download created, waiting to start...';
            break;
        case 'starting':
            downloadStatusMessage.textContent = 'Starting download process...';
            break;
        case 'extracting':
            downloadStatusMessage.textContent = 'Extracting video information...';
            break;
        case 'downloading':
            downloadStatusMessage.textContent = 'Downloading video...';
            break;
        case 'completed':
            downloadStatusMessage.textContent = 'Download completed successfully!';
            clearInterval(statusCheckInterval);
            showDownloadLink(task);
            break;
        case 'failed':
            downloadStatusMessage.textContent = `Download failed: ${task.error || 'Unknown error'}`;
            clearInterval(statusCheckInterval);
            break;
        case 'cancelled':
            downloadStatusMessage.textContent = 'Download was cancelled';
            clearInterval(statusCheckInterval);
            break;
        default:
            downloadStatusMessage.textContent = `Status: ${status}`;
    }
    
    // Update progress bar for downloading status
    if (status === 'downloading') {
        // For now, we don't have real-time progress, so use a simulated progress
        // In a real implementation, the backend would provide actual progress
        const progress = task.progress || 0;
        downloadProgressBar.style.width = `${progress}%`;
        downloadProgressText.textContent = `${progress}%`;
    } else if (status === 'completed') {
        downloadProgressBar.style.width = '100%';
        downloadProgressText.textContent = '100%';
    }
}

// Show download link
function showDownloadLink(task) {
    if (task.file_path) {
        downloadLink.href = `/api/download/${task.id}`;
        downloadLink.style.display = 'flex';
    }
}

// Cancel download
async function cancelDownload() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/cancel/${currentTaskId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            downloadStatusMessage.textContent = 'Download cancelled';
            clearInterval(statusCheckInterval);
        } else {
            downloadStatusMessage.textContent = `Error: ${data.error || 'Failed to cancel download'}`;
        }
    } catch (error) {
        downloadStatusMessage.textContent = 'Error connecting to server';
    }
}

// Show error message
function showError(message) {
    alert(message);
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
