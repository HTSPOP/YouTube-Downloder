# YouTube Downloader Pro

A powerful Python application to download YouTube videos and playlists in various formats and qualities.

## Features

- Download videos from YouTube in multiple formats (MP4, MKV, WebM, MP3)
- Choose quality settings (720p, 1080p, Best for videos; 128kbps, 192kbps, 320kbps for audio)
- Download entire playlists with a single command
- User account system with secure login
- Virtual currency system for downloads
- Speed boost option for faster downloads
- Customizable file naming options
- Download history tracking
- Skip previously downloaded files
- Error handling for private or unavailable videos

## File Naming Options

- **Sequential Order**: Files named with sequential numbers - `[1] Title.mp4`
- **Title Only**: Files named using just the video title - `Title.mp4`

## Requirements

- Python 3.6+
- Required packages:
  - yt-dlp
  - pytube
  - colorama
  - mutagen
  - tqdm
  - requests

## Installation

1. Clone or download this repository
2. Install required packages using pip:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python Youtube_Downloder.py
   ```

## Usage

1. **First Launch**: On first launch, you'll be prompted to create a user account
2. **Login**: Enter your username and password to access the application
3. **Main Menu**: Select from available options:
   - Download YouTube Video/Playlist
   - Check Balance Details
   - View Download History
   - Reset Password
   - Remember Me Settings
   - Switch Account
   - Exit

4. **Downloading a Video**:
   - Enter a valid YouTube URL
   - Select format (MP4, MKV, WebM, MP3)
   - Choose quality (720p, 1080p, Best for videos; 128kbps, 192kbps, 320kbps for audio)
   - Select whether to use Speed Boost (costs extra)
   - Choose file naming preference (Sequential Order or Title Only)
   - Confirm download

## Virtual Currency System

The application uses a virtual currency (Rs) for downloads:

- Each new account starts with a balance of 600 Rs
- Download costs vary by format and quality:
  - MP4/MKV/WebM: 40 Rs (720p), 50 Rs (1080p), 60 Rs (Best)
  - MP3: 40 Rs (128kbps), 50 Rs (192kbps), 60 Rs (320kbps), 70 Rs (Any)
- Speed Boost costs an additional 80 Rs per download
- Remember Me (auto-login) feature costs 150 Rs
- **Special Command**: Enter `Bro Please : Add Some Money` in either:
  - The main menu's "Select option:" prompt
  - The URL field when downloading
  This command will add 600 Rs to your account balance

## Security Features

- Password hashing for secure storage
- Previous password tracking to prevent reuse
- Remember Me feature for convenient login

## Author

Created by: HTSPOP0007
Version: 1.0.0

## Disclaimer

This application is for educational purposes only. Always respect YouTube's Terms of Service when downloading content. 