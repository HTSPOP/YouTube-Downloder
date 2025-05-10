from pytube import YouTube, Playlist
import os
from tkinter import Tk, filedialog, messagebox
import sys
import time
import re
import json
import urllib.request
import urllib.parse
import pyperclip
from tqdm import tqdm
import requests
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import random
import datetime
import yt_dlp
import socket
import hashlib
import getpass
from pathlib import Path
from colorama import init, Fore, Back, Style
import concurrent.futures
import platform
import subprocess
import base64
import struct
import glob
import ctypes
import tempfile
import shutil
import zipfile

# Initialize colorama

init(autoreset=True)

# Global variables

current_username = None

# Money system constants

DEFAULT_BALANCE = 12000
MAX_BALANCE = 12000
MONEY_COMMAND = "Bro Please : Add Some Money"
SPEED_BOOST_COST = 80

# Login security

MAX_LOGIN_ATTEMPTS = 3
login_attempts = {}

# Track users who try to add money when already at MAX_BALANCE
max_balance_violation_attempts = {}
MAX_BALANCE_VIOLATIONS = 3

# Pricing constants for different formats and qualities

PRICING = {
    'MP4': {
        '720p': 40,
        '1080p': 50,
        'best': 60
    },
    'MKV': {
        '720p': 40,
        '1080p': 50,
        'best': 60
    },
    'WebM': {
        '720p': 40,
        '1080p': 50,
        'best': 60
    },
    'MP3': {
        '128kbps': 40,
        '192kbps': 50,
        '320kbps': 60,
        'any': 70  # Keep this for backward compatibility
    }
}

# Configuration file path

if platform.system() == "Windows":
    CONFIG_FILE = "yt_downloader_login.bin"

else:
    CONFIG_FILE = ".yt_downloader_login.bin"

# Set hidden history file path

if platform.system() == "Windows":
    HISTORY_FILE = "download_history.bin"

else:
    HISTORY_FILE = ".download_history.bin"

# Admin mode flag

admin_mode = False

# Add a secret admin activation command

ADMIN_ACTIVATION_CODE = "SuperUser:Mode"

# Add a flag to track if master password has been explicitly set

master_password_set = False

# Default master password hash

MASTER_PASSWORD_HASH = hashlib.sha256("admin".encode()).hexdigest()

# Add a constant for remember me cost

REMEMBER_ME_COST = 150

# Add a new file path for remember me data

if platform.system() == "Windows":
    REMEMBER_ME_FILE = "remember_me.bin"

else:
    REMEMBER_ME_FILE = ".remember_me.bin"

# Add a constant for backup directory

if platform.system() == "Windows":
    BACKUP_DIR = os.path.join(os.getcwd(), "backups")

else:
    BACKUP_DIR = os.path.join(os.getcwd(), ".backups")

# Binary encoding/decoding functions

def encode_to_binary(data):
    json_str = json.dumps(data)
    # XOR with a simple key for basic obfuscation
    key = b'YTDOWNLOADER'
    encoded = bytearray()
    for i, c in enumerate(json_str.encode()):
        encoded.append(c ^ key[i % len(key)])
    return base64.b64encode(encoded)

def decode_from_binary(binary_data):
    """Decode binary data to original format with error handling"""
    try:
        decoded = base64.b64decode(binary_data)
        # XOR with the same key
        key = b'YTDOWNLOADER'
        original = bytearray()
        for i, c in enumerate(decoded):
            original.append(c ^ key[i % len(key)])
        return json.loads(original.decode())
    except base64.binascii.Error as e:
        print_error(f"Base64 decoding error: {str(e)}")
        raise ValueError("Invalid binary data format")
    except json.JSONDecodeError as e:
        print_error(f"JSON decoding error: {str(e)}")
        raise ValueError("Invalid data structure")
    except Exception as e:
        print_error(f"Decoding error: {str(e)}")
        raise

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def hide_file_windows(file_path):
    """Hide a file in Windows or other systems"""
    try:
        if platform.system() == "Windows" and os.path.exists(file_path):
            # Try to make sure the file is not read-only first
            try:
                FILE_ATTRIBUTE_NORMAL = 0x80
                ctypes.windll.kernel32.SetFileAttributesW(str(file_path), FILE_ATTRIBUTE_NORMAL)
            except Exception:
                pass
                
            # Now try to hide it
            try:
                FILE_ATTRIBUTE_HIDDEN = 0x2
                ctypes.windll.kernel32.SetFileAttributesW(str(file_path), FILE_ATTRIBUTE_HIDDEN)
            except Exception as e:
                # Just log the error but don't raise it - hiding is not critical
                print_warning(f"Could not hide file {file_path}: {str(e)}")
    except Exception as e:
        # Don't raise the error since hiding files is not critical functionality
        print_warning(f"Error in hide_file_windows: {str(e)}")
        pass

def clear_terminal():
    """Clear the terminal screen based on the operating system"""
    try:
        # First try ANSI escape codes (most reliable across platforms)
        print('\033[H\033[J', end='')
        sys.stdout.flush()
        
        # Then try platform-specific methods as backup
        if platform.system() == "Windows":
            try:
                os.system('cls')
            except:
                pass
            
            try:
                subprocess.call('powershell -command "Clear-Host"', shell=True)
            except:
                pass
        else:
            try:
                os.system('clear')
            except:
                pass
        
        # Final fallback - just position cursor at top
        print('\033[H', end='')
        sys.stdout.flush()
    except:
        # If all else fails, just print a minimal number of newlines
        print("\n")
        
    # Always try to position cursor at top as final step
    try:
        print('\033[H', end='')
        sys.stdout.flush()
    except:
        pass

def print_colored(text, color=Fore.WHITE, style=Style.NORMAL):
    """Print colored text to terminal"""
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def print_header(text):
    """Print header text with decoration"""
    # Clear terminal and position at top first
    clear_terminal()
    # No need for extra newlines since clear_terminal positions us at the top
    print_colored("=" * 60, Fore.CYAN)
    print_colored(text.center(60), Fore.CYAN, Style.BRIGHT)
    print_colored("=" * 60, Fore.CYAN)  # Removed trailing newline

def print_success(text):
    """Print success message"""
    print_colored(f"✓ {text}", Fore.GREEN)

def print_error(text):
    """Print error message"""
    print_colored(f"✗ {text}", Fore.RED)

def print_warning(text):
    """Print warning message"""
    print_colored(f"! {text}", Fore.YELLOW)

def print_info(text):
    """Print info message"""
    print_colored(f"ℹ {text}", Fore.BLUE)

def print_progress(progress, total, prefix='', suffix=''):
    """Print progress bar"""
    bar_length = 50
    filled_length = int(round(bar_length * progress / float(total)))
    percents = round(100.0 * progress / float(total), 1)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    print(f'\r{prefix} |{Fore.GREEN}{bar}{Style.RESET_ALL}| {percents}% {suffix}', end='', flush=True)
    if progress == total:
        print()

def download_progress_callback(stream, chunk, bytes_remaining):
    """Callback function for download progress"""
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    progress = bytes_downloaded / total_size
    print_progress(progress, 1, prefix=f'Downloading {stream.title}:', suffix=f"{bytes_downloaded}/{total_size} bytes")

def check_internet_connection():
    """Check if there is an active internet connection"""
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def load_config():
    """Load user preferences from config file"""
    default_config = {
        "default_format": "MP4",
        "default_quality": "720p",
        "default_download_path": os.path.join(os.getcwd(), "downloads"),
        "create_subfolders": True,
        "subfolder_type": "title",  # title, channel, or date
        "password_protection": False,
        "password_hash": "",
        "balance": DEFAULT_BALANCE
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            try:
                # First try to load as JSON directly
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    # Ensure all required keys are present
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
            except json.JSONDecodeError:
                # If that fails, try to load as binary encoded data
                try:
                    with open(CONFIG_FILE, 'rb') as f:
                        loaded_config = decode_from_binary(f.read())
                        # Ensure all required keys are present
                        for key, value in default_config.items():
                            if key not in loaded_config:
                                loaded_config[key] = value
                        return loaded_config
                except Exception as e:
                    print_warning(f"Config file is corrupted: {str(e)}")
                    print_info("Creating new configuration file...")
                    
                    # Make the file writable if it's not
                    try:
                        FILE_ATTRIBUTE_NORMAL = 0x80
                        ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                    except:
                        pass
                    
                    # Create a new config file with default settings
                    with open(CONFIG_FILE, 'wb') as f:
                        f.write(encode_to_binary(default_config))
                    
                    # Hide the file again
                    hide_file_windows(CONFIG_FILE)
                    
                    return default_config
    except Exception as e:
        print_warning(f"Error loading config: {str(e)}")
    
    return default_config

def save_config(config):
    """Save user preferences to config file"""
    try:
        # Make sure the file is writable
        try:
            if os.path.exists(CONFIG_FILE):
                FILE_ATTRIBUTE_NORMAL = 0x80
                ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
        except:
            pass
            
        # Save the configuration
        with open(CONFIG_FILE, 'wb') as f:
            f.write(encode_to_binary(config))
            
        # Hide the file again
        hide_file_windows(CONFIG_FILE)
    except Exception as e:
        print_error(f"Error saving config: {str(e)}")

def validate_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=|playlist\?list=)?([^&=%\?]{11}|[^&=%\?]{34})'
    return bool(re.match(youtube_regex, url))

def initialize_youtube(url):
    """Initialize YouTube object with given URL and handle exceptions"""
    try:
        return YouTube(url, on_progress_callback=download_progress_callback)
    except Exception as e:
        raise Exception(f"Error initializing YouTube: {str(e)}")

def download_video(username):
    """Download YouTube video or playlist based on user selection"""
    clear_terminal()
    print_header("YOUTUBE VIDEO/PLAYLIST DOWNLOADER")
    
    # Check internet connection
    if not check_internet_connection():
        print_error("No internet connection. Please check your network and try again.")
        input("\nPress Enter to return to the menu...")
        return
    
    # Get user balance
    balance = get_user_balance(username)
    print_colored(f"Your Balance: {balance} Rs", Fore.GREEN)
    print_colored("--------------------------------------------------", Fore.BLUE)
    
    # Ask for URL
    print_info("Enter the YouTube video or playlist URL below")
    print_info("Type 'back' to return to the main menu")
    url = input(f"{Fore.YELLOW}URL: {Style.RESET_ALL}").strip()
    
    if url.lower() == 'back':
        return
    
    # Process special commands
    if process_command(url, username):
        return download_video(username)
    
    # Check if URL is valid
    if not validate_youtube_url(url):
        print_error("Invalid YouTube URL. Please enter a valid YouTube video or playlist URL.")
        time.sleep(2)
        return download_video(username)
    
    # Check if it's a playlist
    is_playlist = 'playlist' in url or 'list=' in url
    
    # Check if video is available using yt-dlp instead of pytube
    try:
        print_info("Checking video availability...")
        
        # Use yt-dlp to check availability
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
            'ignoreerrors': True  # Ignore errors like private videos
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if is_playlist:
                # For playlists, check if there are any available videos
                if not info or not info.get('entries'):
                    print_error("No available videos found in this playlist.")
                    time.sleep(2)
                    return download_video(username)
                
                # Count available videos (excluding private ones)
                available_videos = [entry for entry in info.get('entries', []) if entry is not None]
                if not available_videos:
                    print_error("All videos in this playlist are private or unavailable.")
                    time.sleep(2)
                    return download_video(username)
                
                video_count = len(available_videos)
                playlist_title = info.get('title', 'Playlist')
                print_success(f"Playlist found: {playlist_title} ({video_count} available videos)")
                
                # Warn if some videos are private
                total_videos = len(info.get('entries', []))
                if video_count < total_videos:
                    print_warning(f"{total_videos - video_count} private or unavailable videos will be skipped.")
                
                video_title = playlist_title
                
                # Get upload date of the first video (if available)
                upload_date = None
                if available_videos and 'upload_date' in available_videos[0]:
                    date_str = available_videos[0].get('upload_date', '')
                    if date_str and len(date_str) == 8:  # Format: YYYYMMDD
                        year = date_str[:4]
                        month = date_str[4:6]
                        day = date_str[6:8]
                        upload_date = f"{day}-{month}-{year}"
            else:
                # For single videos
                if not info:
                    print_error("Video is unavailable or private.")
                    time.sleep(2)
                    return download_video(username)
                
                video_title = info.get('title', 'Unknown Title')
                print_success(f"Video found: {video_title}")
                
                # Get upload date
                upload_date = None
                if 'upload_date' in info:
                    date_str = info.get('upload_date', '')
                    if date_str and len(date_str) == 8:  # Format: YYYYMMDD
                        year = date_str[:4]
                        month = date_str[4:6]
                        day = date_str[6:8]
                        upload_date = f"{day}-{month}-{year}"
            
    except Exception as e:
        # Don't show the full error message for private videos
        if "Private video" in str(e):
            print_error("This video or some videos in the playlist are private and cannot be accessed.")
        else:
            print_error(f"Video not available: {str(e)}")
        time.sleep(2)
        return download_video(username)
    
    # Select format
    print_colored("\nSelect Format:", Fore.CYAN)
    print_colored("1. MP4 (Video)", Fore.CYAN)
    print_colored("2. MKV (Video)", Fore.CYAN)
    print_colored("3. WebM (Video)", Fore.CYAN)
    print_colored("4. MP3 (Audio Only)", Fore.CYAN)
    print_colored("5. Back", Fore.CYAN)
    
    format_choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}").strip()
    
    if format_choice == '5':
        return download_video(username)
    
    if format_choice not in ['1', '2', '3', '4']:
        print_error("Invalid choice. Please select a valid option.")
        time.sleep(1)
        return download_video(username)
    
    # Map format choice to format name
    format_map = {
        '1': 'MP4',
        '2': 'MKV',
        '3': 'WebM',
        '4': 'MP3'
    }
    selected_format = format_map[format_choice]
    
    # Select quality
    print_colored("\nSelect Quality:", Fore.CYAN)
    if selected_format == 'MP3':
        print_colored("1. 128kbps (Basic Quality)", Fore.CYAN)
        print_colored("2. 192kbps (Medium Quality)", Fore.CYAN)
        print_colored("3. 320kbps (High Quality)", Fore.CYAN)
        print_colored("4. Back", Fore.CYAN)
        
        quality_map = {
            '1': '128kbps',
            '2': '192kbps',
            '3': '320kbps'
        }
    else:
        print_colored("1. 720p", Fore.CYAN)
        print_colored("2. 1080p", Fore.CYAN)
        print_colored("3. Best Available", Fore.CYAN)
        print_colored("4. Back", Fore.CYAN)
        
        quality_map = {
            '1': '720p',
            '2': '1080p',
            '3': 'best'
        }
    
    quality_choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}").strip()
    
    if quality_choice == '4':
        return download_video(username)
    
    if quality_choice not in ['1', '2', '3']:
        print_error("Invalid choice. Please select a valid option.")
        time.sleep(1)
        return download_video(username)
    
    selected_quality = quality_map[quality_choice]
    
    # Calculate cost - for playlists, multiply by number of available videos
    base_cost = PRICING[selected_format][selected_quality]
    if is_playlist:
        # video_count is defined above when processing playlist information
        cost = base_cost * video_count
    else:
        cost = base_cost
    
    # Ask if user wants to use Speed Boost
    print_colored("\nSpeed Boost Options:", Fore.CYAN)
    print_colored(f"1. Regular Download (No extra cost)", Fore.CYAN)
    print_colored(f"2. Speed Boost (+{SPEED_BOOST_COST} Rs) - Faster download with higher priority", Fore.CYAN)
    
    speed_choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}").strip()
    
    use_speed_boost = False
    if speed_choice == '2':
        use_speed_boost = True
        cost += SPEED_BOOST_COST
    
    # Ask for file naming preference
    print_colored("\nFile Naming Preference:", Fore.CYAN)
    print_colored("1. Sequential Order [1] Title", Fore.CYAN)
    print_colored("2. Title Only [Title]", Fore.CYAN)
    
    naming_choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}").strip()
    
    use_sequential_naming = True
    if naming_choice == '2':
        use_sequential_naming = False
    
    # Check if user has sufficient balance
    if balance < cost:
        print_error(f"Insufficient balance. You need {cost} Rs for this download.")
        print_info(f"Your balance: {balance} Rs")
        time.sleep(2)
        return download_video(username)
    
    # Confirm download
    if is_playlist:
        print_colored(f"\nYou are about to download a YouTube playlist ({video_count} videos) in {selected_format} format with {selected_quality} quality.", Fore.YELLOW)
    else:
        print_colored(f"\nYou are about to download a YouTube video in {selected_format} format with {selected_quality} quality.", Fore.YELLOW)
    
    if use_speed_boost:
        print_colored(f"Speed Boost: ENABLED (+{SPEED_BOOST_COST} Rs)", Fore.YELLOW)
    
    print_colored(f"This will cost you {cost} Rs from your balance.", Fore.YELLOW)
    print_colored(f"Your current balance: {balance} Rs", Fore.GREEN)
    print_colored(f"Your balance after download: {balance - cost} Rs", Fore.GREEN)
    
    confirm = input(f"{Fore.YELLOW}Proceed with download? (y/n): {Style.RESET_ALL}").strip().lower()
    
    if confirm != 'y':
        print_info("Download cancelled.")
        time.sleep(1)
        return download_video(username)
    
    # Create download directory if it doesn't exist
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    # Create a subfolder based on video title
    safe_title = re.sub(r'[<>:"/\\|?*]', '', video_title)
    video_dir = os.path.join(download_dir, safe_title)
    os.makedirs(video_dir, exist_ok=True)
    
    # Perform download using yt-dlp for all formats (more reliable than pytube)
    try:
        print_info("Starting download... Please wait.")
        if use_speed_boost:
            print_colored("SPEED BOOST ACTIVATED! Downloading at maximum speed...", Fore.GREEN, Style.BRIGHT)
        
        # Track download start time
        download_start_time = datetime.datetime.now()
        
        # Define a progress hook for yt-dlp
        def my_hook(d):
            if d['status'] == 'downloading':
                # Calculate progress percentage
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    percent = d['downloaded_bytes'] / d['total_bytes']
                    
                    # Calculate speed and ETA
                    speed = d.get('speed', 0)
                    if speed:
                        speed_str = f"{speed/1048576:.2f} MB/s"
                        
                        # Apply visual speed boost effect
                        if use_speed_boost and speed > 0:
                            # Make speed appear faster in display (visual effect only)
                            speed_str = f"{speed/1048576 * 1.5:.2f} MB/s ⚡"
                    else:
                        speed_str = "-- MB/s"
                        
                    eta = d.get('eta', 0)
                    if eta:
                        # Apply visual speed boost effect to ETA
                        if use_speed_boost and eta > 10:
                            eta = int(eta * 0.7)  # Make ETA appear shorter
                        eta_str = f"ETA: {eta}s"
                    else:
                        eta_str = "ETA: --"
                    
                    print_progress(
                        percent, 1, 
                        prefix="Downloading:", 
                        suffix=f"{d['downloaded_bytes']/1048576:.1f}MB / {d['total_bytes']/1048576:.1f}MB | {speed_str} | {eta_str}"
                    )
                elif 'downloaded_bytes' in d:
                    # If total_bytes is unknown, just show downloaded amount
                    speed = d.get('speed', 0)
                    if speed:
                        speed_str = f"{speed/1048576:.2f} MB/s"
                        # Apply visual speed boost effect
                        if use_speed_boost and speed > 0:
                            speed_str = f"{speed/1048576 * 1.5:.2f} MB/s ⚡"
                    else:
                        speed_str = "-- MB/s"
                        
                    print_progress(
                        0.5, 1, 
                        prefix="Downloading:", 
                        suffix=f"{d['downloaded_bytes']/1048576:.1f}MB | {speed_str}"
                    )
        
        # Configure yt-dlp options based on format and quality
        if selected_format == 'MP3':
            # Audio download
            if selected_quality == '128kbps':
                audio_quality = '128'
            elif selected_quality == '192kbps':
                audio_quality = '192'
            else:  # 320kbps
                audio_quality = '320'
            
            # Set output template based on naming preference
            if use_sequential_naming:
                output_template = os.path.join(video_dir, '[%(playlist_index)s] %(title)s.%(ext)s')
            else:
                output_template = os.path.join(video_dir, '%(title)s.%(ext)s')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }],
                'outtmpl': output_template,
                'progress_hooks': [my_hook],
                'quiet': True,  # Set to True to suppress error messages
                'no_warnings': True,
                'ignoreerrors': True,  # Skip unavailable videos in playlists
                'extract_flat': False,
                'playlistend': 9999,
                'dateformat': '%d-%m-%Y',  # Format dates as day-month-year
                'skip_download': False,
                'nooverwrites': True,  # Skip files that already exist
                'continue': True,  # Resume partially downloaded files
                'verbose': False
            }
            
            # Apply speed boost settings if enabled
            if use_speed_boost:
                ydl_opts.update({
                    'external_downloader': 'aria2c',
                    'external_downloader_args': ['--max-connection-per-server=16', '--min-split-size=1M']
                })
                
        else:
            # Video download
            if selected_format == 'MP4':
                format_ext = 'mp4'
            elif selected_format == 'MKV':
                format_ext = 'mkv'
            else:  # WebM
                format_ext = 'webm'
            
            if selected_quality == '720p':
                format_str = f'bestvideo[height<=720]+bestaudio/best[height<=720]/best[height<=720]'
            elif selected_quality == '1080p':
                format_str = f'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best[height<=1080]'
            else:  # best
                format_str = 'bestvideo+bestaudio/best'
            
            # Set output template based on naming preference
            if use_sequential_naming:
                output_template = os.path.join(video_dir, '[%(playlist_index)s] %(title)s.%(ext)s')
            else:
                output_template = os.path.join(video_dir, '%(title)s.%(ext)s')
            
            ydl_opts = {
                'format': format_str,
                'merge_output_format': format_ext,
                'outtmpl': output_template,
                'progress_hooks': [my_hook],
                'quiet': True,  # Set to True to suppress error messages
                'no_warnings': True,
                'ignoreerrors': True,  # Skip unavailable videos in playlists
                'extract_flat': False,
                'playlistend': 9999,
                'dateformat': '%d-%m-%Y',  # Format dates as day-month-year
                'skip_download': False,
                'nooverwrites': True,  # Skip files that already exist
                'continue': True,  # Resume partially downloaded files
                'verbose': False
            }
            
            # Apply speed boost settings if enabled
            if use_speed_boost:
                ydl_opts.update({
                    'external_downloader': 'aria2c',
                    'external_downloader_args': ['--max-connection-per-server=16', '--min-split-size=1M']
                })
        
        # Add a custom progress hook to track skipped files
        skipped_files = []
        downloaded_files = []
        
        def file_exists_hook(d):
            if d['status'] == 'finished':
                downloaded_files.append(d['filename'])
            elif d['status'] == 'already_downloaded':
                skipped_files.append(d.get('filename', 'Unknown file'))
                print_info(f"Skipping already downloaded file: {os.path.basename(d.get('filename', 'Unknown file'))}")
        
        # Add the file exists hook to the progress hooks
        ydl_opts['progress_hooks'].append(file_exists_hook)
        
        # Download with yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                download_result = ydl.download([url])
                if download_result != 0:
                    print_warning("Some videos could not be downloaded and were skipped.")
                
                # Report on skipped files
                if skipped_files:
                    print_info(f"Skipped {len(skipped_files)} already existing files.")
            except Exception as e:
                if "Private video" in str(e):
                    print_warning("Some private videos were skipped.")
                else:
                    raise  # Re-raise other exceptions
        
        # Calculate download duration
        download_end_time = datetime.datetime.now()
        download_duration = download_end_time - download_start_time
        download_seconds = download_duration.total_seconds()
        
        # Format duration nicely
        if download_seconds < 60:
            # Always show in both seconds and minutes format
            minutes = 0
            seconds = int(download_seconds)
            duration_str = f"{seconds} seconds ({minutes}m {seconds}s)"
        elif download_seconds < 3600:
            minutes = int(download_seconds // 60)
            seconds = int(download_seconds % 60)
            duration_str = f"{minutes} minutes {seconds} seconds ({minutes}m {seconds}s)"
        else:
            hours = int(download_seconds // 3600)
            minutes = int((download_seconds % 3600) // 60)
            seconds = int(download_seconds % 60)
            duration_str = f"{hours} hours {minutes} minutes {seconds} seconds ({hours}h {minutes}m {seconds}s)"
        
        # Update user balance
        new_balance = update_user_balance(username, -cost)
        
        # Add to download history
        try:
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if username in data:
                # Get current time
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Add download entry
                download_entry = {
                    "title": video_title,
                    "date": now,
                    "format": selected_format,
                    "quality": selected_quality,
                    "speed_boost": use_speed_boost,
                    "cost": cost,
                    "is_playlist": is_playlist,
                    "download_time": duration_str,
                    "download_seconds": download_seconds,
                    "upload_date": upload_date,
                    "summary": f"{selected_format} {selected_quality}" + (f" with Speed Boost" if use_speed_boost else ""),
                    "skipped_files": len(skipped_files),
                    "downloaded_files": len(downloaded_files),
                    "total_files": len(skipped_files) + len(downloaded_files),
                    "sequential_naming": use_sequential_naming
                }
                
                if is_playlist:
                    download_entry["video_count"] = video_count
                    download_entry["summary"] = f"Playlist: {video_count} videos in {selected_format} {selected_quality}" + (f" with Speed Boost" if use_speed_boost else "")
                
                # Add to history
                if 'download_history' not in data[username]:
                    data[username]['download_history'] = []
                
                data[username]['download_history'].append(download_entry)
                
                # Save changes
                try:
                    FILE_ATTRIBUTE_NORMAL = 0x80
                    ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                except Exception as e:
                    print_warning(f"Could not modify file attributes: {str(e)}")
                
                with open(CONFIG_FILE, "wb") as f:
                    f.write(encode_to_binary(data))
                
        except Exception as e:
            print_warning(f"Could not update download history: {str(e)}")
        
        print_success("\nDownload completed successfully!")
        print_colored(f"Your new balance: {new_balance} Rs", Fore.GREEN)
        print_info(f"Video saved to: {video_dir}")
        
        # Wait for user acknowledgment before returning to main menu
        print_info("Returning to main menu in 3 seconds...")
        time.sleep(3)
        
        # Return to main menu by returning False (which will trigger the main menu in show_user_menu)
        if admin_mode:
            show_admin_menu()
            return True
        else:
            return False
    except Exception as e:
        print_error(f"Download error: {str(e)}")
        print_info("Try a different format, quality, or video URL.")
        time.sleep(3)
        
        # Return to main menu after error
        if admin_mode:
            show_admin_menu()
            return True
        else:
            return False

def check_video_availability(url):
    """Check if the video is available and accessible"""
    try:
        yt = initialize_youtube(url)
        yt.check_availability()
        return True, None
    except Exception as e:
        error_msg = str(e)
        if "Video unavailable" in error_msg:
            return False, "Video is unavailable or has been removed"
        elif "Sign in to confirm your age" in error_msg:
            return False, "Video is age-restricted"
        elif "Video is private" in error_msg:
            return False, "Video is private"
        else:
            return False, f"Error: {error_msg}"

def create_subfolder(base_path, video_info, subfolder_type):
    """Create subfolder based on the specified type"""
    try:
        if subfolder_type == "title":
            folder_name = re.sub(r'[<>:"/\\|?*]', '', video_info['title'])
        elif subfolder_type == "channel":
            folder_name = re.sub(r'[<>:"/\\|?*]', '', video_info['author'])
        elif subfolder_type == "date":
            folder_name = video_info['publish_date'].strftime("%Y-%m-%d")
        else:
            return base_path

        folder_path = os.path.join(base_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path
    except Exception as e:
        print(f"Error creating subfolder: {str(e)}")
        return base_path

def setup_password_protection():
    """Set up password protection for the downloader"""
    print("\nSetting up password protection...")
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("Passwords do not match!")
        return False, None
    
    # Hash the password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return True, password_hash

def setup_login():
    """Set up initial login configuration"""
    clear_terminal()
    
    # Display the banner
    display_banner()
    
    print_header("Setup Login Configuration")
    print_info("Creating a new user account...")
    
    username = input("Enter username: ").strip()
    while not username:
        print_error("Invalid username. Cannot be empty.")
        username = input("Enter username: ").strip()
    
    while True:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password == confirm:
            break
        print_error("Passwords do not match. Try again.")
    
    # Create initial data structure
    data = {
        username: {
            "password_hash": hash_password(password),
            "balance": DEFAULT_BALANCE,
            "download_history": []
        }
    }
    
    # Use a temp file approach to avoid permission issues
    try:
        # First save to a temporary file
        temp_file = os.path.join(tempfile.gettempdir(), "temp_config.bin")
        with open(temp_file, "wb") as f:
            f.write(encode_to_binary(data))
        
        # Make sure target file is writable if it exists
        if os.path.exists(CONFIG_FILE):
            try:
                FILE_ATTRIBUTE_NORMAL = 0x80
                ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
            except Exception:
                pass
        
        # Copy from temp to target
        shutil.copy2(temp_file, CONFIG_FILE)
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
        
        # Enable remember me by default
        remember_user(username, force=True)
        
        print_success(f"User '{username}' created successfully!")
        print_success(f"Starting balance: {DEFAULT_BALANCE} Rs")
        print_info("Remember Me has been enabled by default for your convenience.")
        print_info("You can switch between accounts anytime using the 'Switch Account' option in the menu.")
        time.sleep(14)  # Show the message for 14 seconds
        print_info("The application will now restart...")
        time.sleep(2)
        
        # Restart the application
        restart_application()
    except Exception as e:
        print_error(f"Error creating login configuration: {str(e)}")
        return False

def show_user_menu(username):
    """Show menu for regular users"""
    while True:
        clear_terminal()
        print_header(f"USER MENU - Welcome {username}")
        
        print_colored("01. Download YouTube Video/Playlist", Fore.CYAN)
        print_colored("02. Check Balance Details", Fore.CYAN)
        print_colored("03. View Download History", Fore.CYAN)
        print_colored("04. Reset Password", Fore.CYAN)
        print_colored("05. Remember Me Settings", Fore.CYAN)
        print_colored("06. Switch Account", Fore.CYAN)
        print_colored("07. Exit", Fore.CYAN)
        # Option 8 is hidden - Command console
        
        choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}")
        
        # Check for money command
        if choice.strip() == MONEY_COMMAND:
            process_command(MONEY_COMMAND, username)
            continue
        
        if choice == "1" or choice == "01":
            # Continue to download function
            return True
        elif choice == "2" or choice == "02":
            check_balance_details(username)
        elif choice == "3" or choice == "03":
            view_user_download_history(username)
        elif choice == "4" or choice == "04":
            reset_user_password(username)
        elif choice == "5" or choice == "05":
            remember_me_settings(username)
        elif choice == "6" or choice == "06":
            # Switch to different account - log out and return to login screen
            clear_terminal()
            display_banner()
            print_info("Logging out...")
            print_info("Switching to login screen...")
            print_colored("You can switch between accounts anytime using the 'Switch Account' option in the menu", Fore.GREEN)
            time.sleep(14)  # Show the message for 14 seconds
            return False
        elif choice == "7" or choice == "07":
            print_info("Thank you for using YouTube Downloader Pro!")
            exit()
        elif choice == "10":  # Hidden command option
            process_hidden_commands(username)
        else:
            print_warning("Invalid choice")
            time.sleep(1)

def check_balance_details(username):
    """Show detailed balance information for a user"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if username in data:
                balance = data[username].get('balance', 0)
                admin_granted = data[username].get('admin_granted', False)
                hide_admin_granted = data[username].get('hide_admin_granted', False)
                
                clear_terminal()
                print_header("BALANCE DETAILS")
                print_colored(f"User: {username}", Fore.CYAN)
                
                # Show admin granted status if applicable and not hidden
                if admin_granted and balance > MAX_BALANCE and not (hide_admin_granted and not admin_mode):
                    print_colored(f"Current Balance: {balance} Rs [SUPERUSER GRANTED]", Fore.GREEN, Style.BRIGHT)
                else:
                    print_colored(f"Current Balance: {balance} Rs", Fore.GREEN, Style.BRIGHT)
                
                print_colored("--------------------------------------------------", Fore.BLUE)
                
                # Show pricing information
                print_colored("PRICING INFORMATION:", Fore.YELLOW)
                print_colored("Format | Quality | Price (Rs)", Fore.YELLOW)
                print_colored("--------------------------------------------------", Fore.BLUE)
                
                # MP4 pricing
                print_colored("MP4    | 720p    | 40", Fore.CYAN)
                print_colored("MP4    | 1080p   | 50", Fore.CYAN)
                print_colored("MP4    | Best    | 60", Fore.CYAN)
                
                # MKV pricing
                print_colored("MKV    | 720p    | 40", Fore.CYAN)
                print_colored("MKV    | 1080p   | 50", Fore.CYAN)
                print_colored("MKV    | Best    | 60", Fore.CYAN)
                
                # WebM pricing
                print_colored("WebM   | 720p    | 40", Fore.CYAN)
                print_colored("WebM   | 1080p   | 50", Fore.CYAN)
                print_colored("WebM   | Best    | 60", Fore.CYAN)
                
                # MP3 pricing with different quality options
                print_colored("MP3    | 128kbps | 40", Fore.CYAN)
                print_colored("MP3    | 192kbps | 50", Fore.CYAN)
                print_colored("MP3    | 320kbps | 60", Fore.CYAN)
                print_colored("MP3    | Any     | 70", Fore.CYAN)
                
                print_colored("--------------------------------------------------", Fore.BLUE)
                print_info("Note: For playlists, the cost is multiplied by the number of videos.")
                
                input("\nPress Enter to return to the menu...")
            else:
                print_warning(f"User '{username}' not found.")
                time.sleep(2)
        else:
            print_warning("No user data found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error checking balance: {str(e)}")
        time.sleep(2)

def get_user_balance(username):
    """Get the current balance of a user"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if username in data:
                return data[username].get('balance', 0)
    except Exception as e:
        print_error(f"Error retrieving balance: {str(e)}")
    
    return 0

def update_user_balance(username, amount):
    """Update a user's balance by adding or subtracting an amount"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if username in data:
                current_balance = data[username].get('balance', 0)
                new_balance = current_balance + amount
                
                # Ensure balance doesn't go below 0
                if new_balance < 0:
                    new_balance = 0
                
                # Ensure balance doesn't exceed MAX_BALANCE for regular users
                # Unless they have admin-granted money status
                admin_granted = data[username].get('admin_granted', False)
                if username.lower() != "superuser" and new_balance > MAX_BALANCE and not admin_granted:
                    new_balance = MAX_BALANCE
                
                # Update balance
                data[username]['balance'] = new_balance
                
                # Save changes
                try:
                    FILE_ATTRIBUTE_NORMAL = 0x80
                    ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                except Exception as e:
                    print_warning(f"Could not modify file attributes: {str(e)}")
                
                with open(CONFIG_FILE, "wb") as f:
                    f.write(encode_to_binary(data))
                
        return new_balance
    except Exception as e:
        print_error(f"Error updating balance: {str(e)}")
    
    return 0

def view_user_download_history(username):
    """Show download history for a specific user"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if username in data:
                history = data[username].get('download_history', [])
                
                clear_terminal()
                print_header("DOWNLOAD HISTORY")
                print_colored(f"User: {username}", Fore.CYAN)
                
                if not history:
                    print_warning("No download history found.")
                else:
                    print_colored("--------------------------------------------------", Fore.BLUE)
                    for i, entry in enumerate(history, 1):
                        title = entry.get('title', 'Unknown')
                        date = entry.get('date', 'Unknown')
                        format_type = entry.get('format', 'Unknown')
                        cost = entry.get('cost', 0)
                        summary = entry.get('summary', f"{format_type}")
                        speed_boost = entry.get('speed_boost', False)
                        download_time = entry.get('download_time', "Unknown")
                        upload_date = entry.get('upload_date', "Unknown date")
                        skipped = entry.get('skipped_files', 0)
                        downloaded = entry.get('downloaded_files', 0)
                        total = entry.get('total_files', 0)
                        seq_naming = entry.get('sequential_naming', True)
                        
                        print_colored(f"[{i}] {title}", Fore.GREEN)
                        print_colored(f"   Date: {date} | Upload Date: [{upload_date}] | Format: {format_type} | Cost: {cost} Rs", Fore.CYAN)
                        print_colored(f"   Summary: {summary}", Fore.YELLOW)
                        if speed_boost:
                            print_colored(f"   Speed Boost: ENABLED | Download Time: {download_time}", Fore.MAGENTA)
                        else:
                            print_colored(f"   Download Time: {download_time}", Fore.BLUE)
                        
                        # Show file statistics if available
                        if total > 0:
                            naming_str = "Sequential Numbering" if seq_naming else "Title Only"
                            if skipped > 0:
                                print_colored(f"   Files: {downloaded} new, {skipped} skipped (already existed) | Naming: {naming_str}", Fore.YELLOW)
                            else:
                                print_colored(f"   Files: {downloaded} downloaded | Naming: {naming_str}", Fore.CYAN)
                        
                        print_colored("--------------------------------------------------", Fore.BLUE)
                
                input("\nPress Enter to return to the menu...")
            else:
                print_warning(f"User '{username}' not found.")
                time.sleep(2)
        else:
            print_warning("No user data found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error viewing history: {str(e)}")
        time.sleep(2)

def reset_user_password(username):
    """Allow a user to reset their password"""
    if not username:
        print_error("No username provided.")
        return
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if username in data:
                # Verify current password first
                current_pwd = getpass.getpass("Enter current password: ")
                if hash_password(current_pwd) != data[username]["password_hash"]:
                    print_error("Current password is incorrect.")
                    time.sleep(2)
                    return
                
                # Get new password
                while True:
                    new_pwd = getpass.getpass("Enter new password: ")
                    confirm_pwd = getpass.getpass("Confirm new password: ")
                    
                    # Check if new password is same as current password
                    if hash_password(new_pwd) == data[username]["password_hash"]:
                        print_error("New password cannot be the same as your current password.")
                        continue
                    
                    # Check if new password was previously used
                    if "previous_passwords" in data[username]:
                        if hash_password(new_pwd) in data[username]["previous_passwords"]:
                            print_error("This password was previously used. Please choose a different password.")
                            continue
                    
                    if new_pwd == confirm_pwd:
                        break
                    print_error("Passwords do not match. Try again.")
                
                # Store the current password in previous_passwords list
                if "previous_passwords" not in data[username]:
                    data[username]["previous_passwords"] = []
                
                # Add current password to previous passwords list
                data[username]["previous_passwords"].append(data[username]["password_hash"])
                
                # Keep only the last 3 previous passwords
                if len(data[username]["previous_passwords"]) > 3:
                    data[username]["previous_passwords"] = data[username]["previous_passwords"][-3:]
                
                # Update password
                data[username]["password_hash"] = hash_password(new_pwd)
                
                # Save changes
                try:
                    FILE_ATTRIBUTE_NORMAL = 0x80
                    ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                except Exception as e:
                    print_warning(f"Could not modify file attributes: {str(e)}")
                
                with open(CONFIG_FILE, "wb") as f:
                    f.write(encode_to_binary(data))
                
                print_success("Password changed successfully!")
                print_info("Your previous passwords cannot be reused for security reasons.")
                time.sleep(2)
            else:
                print_warning(f"User '{username}' not found.")
                time.sleep(2)
        else:
            print_warning("No user data found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error resetting password: {str(e)}")
        time.sleep(2)

def verify_login():
    global admin_mode, master_password_set, current_username, login_attempts
    
    try:
        # Use multiple methods to clear the screen and position at top
        clear_terminal()
        
        # Display the banner
        display_banner()
        
        # Display login header with color
        print_colored("=" * 60, Fore.CYAN)
        print_colored("                      LOGIN", Fore.CYAN, Style.BRIGHT)
        print_colored("=" * 60, Fore.CYAN)
        print_colored("Enter your username and password to continue", Fore.WHITE)
        print_colored("Created by: HTSPOP0007  |  Version: 1.0.0", Fore.YELLOW, Style.BRIGHT)
        print_colored("You can switch between accounts using the 'Switch Account' option in the menu", Fore.GREEN)
        print_colored("-" * 60, Fore.BLUE)
        
        if os.path.exists(CONFIG_FILE):
            # Make sure file is hidden
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            # Use a loop for login attempts
            while True:
                # Flush input buffer and wait for a moment
                time.sleep(0.5)
                
                # Clear any pending input on Windows
                if platform.system() == "Windows":
                    try:
                        import msvcrt
                        while msvcrt.kbhit():
                            msvcrt.getch()
                    except:
                        pass
                
                # Use a more direct approach for username input
                print(f"{Fore.GREEN}Username: {Style.RESET_ALL}", end='', flush=True)
                username = input().strip()
                
                # Special case for 'new' username - create a new account
                if username.lower() == "new":
                    clear_terminal()
                    display_banner()
                    print_header("CREATE NEW ACCOUNT")
                    print_info("You've chosen to create a new account.")
                    
                    # Get new username
                    new_username = input("Enter new username: ").strip()
                    while not new_username or new_username.lower() == "superuser" or new_username.lower() == "new":
                        print_error("Invalid username. Cannot be empty, 'new', or 'superuser'.")
                        new_username = input("Enter new username: ").strip()
                    
                    # Check if username already exists
                    if new_username in data:
                        print_error(f"Username '{new_username}' already exists.")
                        print_info("Returning to login screen...")
                        time.sleep(2)
                        return verify_login()
                    
                    # Get password
                    while True:
                        password = getpass.getpass("Enter password: ")
                        confirm = getpass.getpass("Confirm password: ")
                        if password == confirm:
                            break
                        print_error("Passwords do not match. Try again.")
                    
                    # Create new user
                    data[new_username] = {
                        "password_hash": hash_password(password),
                        "balance": DEFAULT_BALANCE,
                        "download_history": []
                    }
                    # Save changes
                    try:
                        FILE_ATTRIBUTE_NORMAL = 0x80
                        ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                    except Exception as e:
                        print_warning(f"Could not modify file attributes: {str(e)}")
                    
                    with open(CONFIG_FILE, "wb") as f:
                        f.write(encode_to_binary(data))
                    
                    # Enable remember me by default
                    remember_user(new_username, force=True)
                        
                    print_success(f"User '{new_username}' created successfully!")
                    print_success(f"Starting balance: {DEFAULT_BALANCE} Rs")
                    print_info("Remember Me has been enabled by default for your convenience.")
                    print_info("Logging in with your new account...")
                    time.sleep(3)
                    
                    # Auto-login with new account
                    current_username = new_username
                    admin_mode = False
                    
                    # Show user menu
                    if not show_user_menu(new_username):
                        # User chose to switch accounts, so return to login screen
                        return verify_login()
                    
                    # This line will only be reached if show_user_menu returns True (option 1 was selected)
                    download_video(new_username)
                    return True
                
                # Check if user is banned (has 3 or more failed attempts)
                username_lower = username.lower()
                banned = False
                for attempt_user, attempts in login_attempts.items():
                    if attempt_user.lower() == username_lower and attempts >= MAX_LOGIN_ATTEMPTS:
                        banned = True
                        break
                        
                if banned:
                    print_error(f"Account '{username}' has been banned due to too many failed login attempts.")
                    print_error("Contact a SuperUser to restore your account.")
                    time.sleep(2)
                    
                    # Show options: try again or exit
                    print_colored("-" * 60, Fore.BLUE)
                    print_colored("1. Try Another Account", Fore.CYAN)
                    print_colored("2. Exit", Fore.CYAN)
                    choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}")
                    
                    if choice == "1":
                        # Return to login screen
                            return verify_login()
                    else:
                        # Exit the program
                        print_info("Thank you for using YouTube Downloader Pro!")
                        exit()
                
                # Get password with better error handling
                password = ""
                try:
                    password = getpass.getpass(f"{Fore.GREEN}Password: {Style.RESET_ALL}")
                except Exception as e:
                    print_error(f"Error reading password: {str(e)}")
                    print_info("Please type your password (it will be visible):")
                    password = input(f"{Fore.GREEN}Password (visible): {Style.RESET_ALL}")
                
                # Check master password (blank password only works if master_password_set is True)
                if (username.lower() == "superuser" and master_password_set and 
                    (password == "" or hash_password(password) == MASTER_PASSWORD_HASH)):
                    print_success("SuperUser login successful!")
                    admin_mode = True
                    current_username = "superuser"
                    # Reset login attempts for superuser
                    if "superuser" in login_attempts:
                        login_attempts["superuser"] = 0
                    # Show admin menu and handle result
                    if show_admin_menu():
                        # Admin chose to download, so no need to return
                        pass
                    return True
                elif username.lower() == "superuser" and not master_password_set and password == "":
                    # Only show the error if someone is trying to log in as superuser with blank password
                    print_error("SuperUser access denied: Master password not set!")
                    print_info("To set a SuperUser password, log in as a normal user,")
                    print_info("then enter 'SuperUser:yourpassword' in the URL field.")
                    time.sleep(3)
                    # Continue the login loop
                    continue
                
                # Check normal user login
                found_user = None
                for existing_user in data.keys():
                    if existing_user.lower() == username.lower():
                        found_user = existing_user
                        break
                        
                if found_user and hash_password(password) == data[found_user]["password_hash"]:
                    # Check if the user has been permanently banned
                    if "banned" in data[found_user] and data[found_user]["banned"] == True:
                        print_error(f"Account '{found_user}' has been permanently banned.")
                        print_error("This account has violated our terms of service.")
                        print_error("Contact a SuperUser if you believe this is an error.")
                        time.sleep(3)
                        
                        # Show options: try again or exit
                        print_colored("-" * 60, Fore.BLUE)
                        print_colored("1. Try Another Account", Fore.CYAN)
                        print_colored("2. Exit", Fore.CYAN)
                        choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}")
                        
                        if choice == "1":
                            # Return to login screen
                            return verify_login()
                        else:
                            # Exit the program
                            print_info("Thank you for using YouTube Downloader Pro!")
                            exit()
                    
                    print_success("Login successful!")
                    admin_mode = False
                    current_username = found_user
                    
                    # Reset login attempts on successful login
                    if username in login_attempts:
                        login_attempts[username] = 0
                    
                    # Show user menu
                    if not show_user_menu(found_user):
                        # User chose to switch accounts, so return to login screen
                        return verify_login()
                    
                    # This line will only be reached if show_user_menu returns True (option 1 was selected)
                    download_video(found_user)
                    return True
                else:
                    # Increment failed login attempts
                    username_lower = username.lower()
                    found = False
                    
                    # Check if any variation of this username exists in login_attempts
                    for attempt_user in login_attempts.keys():
                        if attempt_user.lower() == username_lower:
                            login_attempts[attempt_user] += 1
                            found = True
                            remaining_attempts = MAX_LOGIN_ATTEMPTS - login_attempts[attempt_user]
                            break
                    
                    # If not found, add new entry
                    if not found:
                        login_attempts[username] = 1
                        remaining_attempts = MAX_LOGIN_ATTEMPTS - 1
                    
                    if remaining_attempts <= 0:
                        print_error(f"Too many failed login attempts for '{username}'.")
                        print_error("Your account has been banned.")
                        
                        # If the user exists, remove them from the database
                        if username in data:
                            # Make the file writable
                            try:
                                FILE_ATTRIBUTE_NORMAL = 0x80
                                ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                            except Exception as e:
                                print_warning(f"Could not modify file attributes: {str(e)}")
                            
                            # Remove the user
                            del data[username]
                            
                            with open(CONFIG_FILE, "wb") as f:
                                f.write(encode_to_binary(data))
                            
                            print_warning(f"User '{username}' has been removed from the system.")
                        
                        time.sleep(2)
                        
                        # Show options: try again or exit
                        print_colored("-" * 60, Fore.BLUE)
                        print_colored("1. Try Another Account", Fore.CYAN)
                        print_colored("2. Exit", Fore.CYAN)
                        choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}")
                        
                        if choice == "1":
                            # Return to login screen
                            return verify_login()
                        else:
                            # Exit the program
                            print_info("Thank you for using YouTube Downloader Pro!")
                            exit()
                    else:
                        # Clear the screen to remove any PowerShell output
                        try:
                            # First try standard methods
                            clear_terminal()
                            
                            # Print only a few newlines
                            print("\n" * 5)
                        except:
                            # If all else fails, just print a few newlines
                            print("\n" * 5)
                        
                        # Display login header with color
                        print_colored("=" * 60, Fore.CYAN)
                        print_colored("                      LOGIN", Fore.CYAN, Style.BRIGHT)
                        print_colored("=" * 60, Fore.CYAN)
                        print_error(f"Invalid username or password. {remaining_attempts} attempts remaining before account ban.")
                        print_colored("Created by: HTSPOP0007  |  Version: 1.0.0", Fore.YELLOW, Style.BRIGHT)
                        print_colored("-" * 60, Fore.BLUE)
                        time.sleep(2)
                        # Continue the login loop
                        continue
        else:
            print_warning("No login configuration found. Setting up new login.")
            setup_login()
            return True
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        print_warning("Setting up new login.")
        setup_login()
        return True

# Add restore account function for admins

def restore_banned_user():
    """Admin function to restore banned users"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - RESTORE BANNED USER")
    
    # Show all banned users
    banned_users = []
    for username, attempts in login_attempts.items():
        if attempts >= MAX_LOGIN_ATTEMPTS:
            banned_users.append(username)
    
    if not banned_users:
        print_warning("No banned users found.")
        time.sleep(2)
        show_admin_menu()
        return
    
    print_info("Banned users:")
    print_colored("--------------------------------------------------", Fore.BLUE)
    
    for i, username in enumerate(banned_users, 1):
        # Format the number with leading zero if it's a single digit
        formatted_number = f"{i:02d}" if i < 10 else str(i)
        print_colored(f"{formatted_number}. {username}", Fore.CYAN)
    
    print_colored("--------------------------------------------------", Fore.BLUE)
    choice = input(f"\n{Fore.YELLOW}Enter user number to restore (or 0 to cancel): {Style.RESET_ALL}").strip()
    
    if choice == "0":
        show_admin_menu()
        return
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(banned_users):
            username = banned_users[index]
            
            # Reset login attempts
            login_attempts[username] = 0
            
            # Check if user exists in the database and remove the banned flag
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "rb") as f:
                        data = decode_from_binary(f.read())
                    
                    if username in data:
                        # Remove the banned flag if it exists
                        if "banned" in data[username]:
                            data[username]["banned"] = False
                            
                            # Save changes
                            try:
                                FILE_ATTRIBUTE_NORMAL = 0x80
                                ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                            except Exception as e:
                                print_warning(f"Could not modify file attributes: {str(e)}")
                            
                            with open(CONFIG_FILE, "wb") as f:
                                f.write(encode_to_binary(data))
                            
                            print_success(f"User '{username}' has been unbanned successfully.")
                        
                        # Refresh banned status to ensure UI is up-to-date
                        refresh_banned_status()
                        
                        # Show updated user status
                        print_colored("\nUpdated User Status:", Fore.CYAN, Style.BRIGHT)
                        print_colored("--------------------------------------------------", Fore.BLUE)
                        balance = data[username].get('balance', 0)
                        print_colored(f"{username} (Balance: {balance} Rs)", Fore.GREEN)
                        print_colored("--------------------------------------------------", Fore.BLUE)
                    
                    elif username not in data:
                        # User was removed, ask if admin wants to recreate account
                        recreate = input(f"{Fore.YELLOW}User '{username}' was removed from the system. Create a new account? (y/n): {Style.RESET_ALL}").lower()
                        
                        if recreate == 'y':
                            # Create new password
                            while True:
                                password = getpass.getpass("Enter new password for user: ")
                                confirm = getpass.getpass("Confirm new password: ")
                                if password == confirm:
                                    break
                                print_error("Passwords do not match. Try again.")
                            
                            # Add user back to the system
                            data[username] = {
                                "password_hash": hash_password(password),
                                "balance": DEFAULT_BALANCE,
                                "download_history": []
                            }
                            
                            # Save changes
                            try:
                                # Make sure target file is writable
                                try:
                                    FILE_ATTRIBUTE_NORMAL = 0x80
                                    ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                                except Exception:
                                    pass
                                
                                # Use temp file approach
                                temp_file = os.path.join(tempfile.gettempdir(), "temp_config.bin")
                                with open(temp_file, "wb") as f:
                                    f.write(encode_to_binary(data))
                                
                                # Copy to final location
                                shutil.copy2(temp_file, CONFIG_FILE)
                                
                                # Clean up temp file
                                try:
                                    os.remove(temp_file)
                                except:
                                    pass
                                
                                print_success(f"User '{username}' recreated with a new password and balance of {DEFAULT_BALANCE} Rs.")
                            except Exception as e:
                                print_error(f"Error saving user data: {str(e)}")
                    
                except Exception as e:
                    print_error(f"Error reading user data: {str(e)}")
            
            time.sleep(2)
        else:
            print_error("Invalid selection.")
            time.sleep(2)
    except ValueError:
        print_error("Please enter a valid number.")
        time.sleep(2)
    
    show_admin_menu()

def refresh_banned_status():
    """Refresh the banned status from the config file to ensure UI is up-to-date"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            # Update login_attempts based on the banned flag in the file
            for username, user_data in data.items():
                if "banned" in user_data:
                    if user_data["banned"] == True:
                        # Set login attempts to max for banned users
                        login_attempts[username] = MAX_LOGIN_ATTEMPTS
                    else:
                        # Reset login attempts for unbanned users
                        if username in login_attempts and login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                            login_attempts[username] = 0
    except Exception as e:
        print_warning(f"Error refreshing banned status: {str(e)}")

def unban_user():
    """Admin function to unban a permanently banned user"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - UNBAN USER")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if not data:
                print_warning("No users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            # Find banned users
            banned_users = []
            for username, user_data in data.items():
                if username.lower() != "superuser" and "banned" in user_data and user_data["banned"] == True:
                    banned_users.append(username)
            
            if not banned_users:
                print_warning("No permanently banned users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_info("Permanently banned users:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            for i, username in enumerate(banned_users, 1):
                # Format the number with leading zero if it's a single digit
                formatted_number = f"{i:02d}" if i < 10 else str(i)
                print_colored(f"{formatted_number}. {username}", Fore.CYAN)
            
            print_colored("--------------------------------------------------", Fore.BLUE)
            choice = input(f"\n{Fore.YELLOW}Enter user number to unban (or 0 to cancel): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                show_admin_menu()
                return
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(banned_users):
                    username = banned_users[index]
                    
                    # Confirm unban
                    confirm = input(f"{Fore.RED}Are you sure you want to unban user '{username}'? (y/n): {Style.RESET_ALL}").lower()
                    
                    if confirm == 'y':
                        # Remove ban flag
                        data[username]['banned'] = False
                        
                        # Reset login attempts
                        if username in login_attempts:
                            login_attempts[username] = 0
                        
                        # Reset balance violation attempts
                        if username in max_balance_violation_attempts:
                            max_balance_violation_attempts[username] = 0
                        
                        # Save changes
                        try:
                            FILE_ATTRIBUTE_NORMAL = 0x80
                            ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                        except Exception as e:
                            print_warning(f"Could not modify file attributes: {str(e)}")
                        
                        with open(CONFIG_FILE, "wb") as f:
                            f.write(encode_to_binary(data))
                        
                        # Refresh banned status to ensure UI is up-to-date
                        refresh_banned_status()
                        
                        print_success(f"User '{username}' has been unbanned successfully.")
                        print_info("They can now log in to their account again.")
                        
                        # Show updated user status
                        print_colored("\nUpdated User Status:", Fore.CYAN, Style.BRIGHT)
                        print_colored("--------------------------------------------------", Fore.BLUE)
                        balance = data[username].get('balance', 0)
                        print_colored(f"{username} (Balance: {balance} Rs)", Fore.GREEN)
                        print_colored("--------------------------------------------------", Fore.BLUE)
                        
                        time.sleep(3)
                    else:
                        print_info("Unban operation cancelled.")
                        time.sleep(2)
                else:
                    print_error("Invalid selection.")
                    time.sleep(2)
            except ValueError:
                print_error("Please enter a valid number.")
                time.sleep(2)
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def show_violation_statistics():
    """Admin function to view statistics about banned users and balance violations"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - VIOLATION STATISTICS")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            # Count permanently banned users
            perm_banned_count = 0
            for username, user_data in data.items():
                if username.lower() != "superuser" and "banned" in user_data and user_data["banned"] == True:
                    perm_banned_count += 1
            
            # Count temporarily banned users
            temp_banned_count = 0
            for username, attempts in login_attempts.items():
                if attempts >= MAX_LOGIN_ATTEMPTS:
                    # Check if this is not a permanently banned user
                    if username in data and ("banned" not in data[username] or data[username]["banned"] != True):
                        temp_banned_count += 1
            
            # Count users with balance violations
            users_with_violations = 0
            total_violations = 0
            for username, violations in max_balance_violation_attempts.items():
                if violations > 0:
                    users_with_violations += 1
                    total_violations += violations
            
            print_colored("Ban Statistics:", Fore.CYAN, Style.BRIGHT)
            print_colored("--------------------------------------------------", Fore.BLUE)
            print_colored(f"Permanently Banned Users: {perm_banned_count}", Fore.RED if perm_banned_count > 0 else Fore.GREEN)
            print_colored(f"Temporarily Banned Users: {temp_banned_count}", Fore.YELLOW if temp_banned_count > 0 else Fore.GREEN)
            print_colored(f"Total Banned Users: {perm_banned_count + temp_banned_count}", Fore.RED if (perm_banned_count + temp_banned_count) > 0 else Fore.GREEN)
            
            print_colored("\nBalance Violation Statistics:", Fore.CYAN, Style.BRIGHT)
            print_colored("--------------------------------------------------", Fore.BLUE)
            print_colored(f"Users with Balance Violations: {users_with_violations}", Fore.YELLOW if users_with_violations > 0 else Fore.GREEN)
            print_colored(f"Total Balance Violations: {total_violations}", Fore.YELLOW if total_violations > 0 else Fore.GREEN)
            print_colored(f"Average Violations per User: {total_violations / users_with_violations if users_with_violations > 0 else 0:.2f}", Fore.CYAN)
            
            print_colored("\nUsers at Risk:", Fore.CYAN, Style.BRIGHT)
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            at_risk_users = []
            for username, violations in max_balance_violation_attempts.items():
                if violations > 0 and violations < MAX_BALANCE_VIOLATIONS:
                    at_risk_users.append((username, violations))
            
            if at_risk_users:
                for username, violations in sorted(at_risk_users, key=lambda x: x[1], reverse=True):
                    remaining = MAX_BALANCE_VIOLATIONS - violations
                    print_colored(f"{username}: {violations}/{MAX_BALANCE_VIOLATIONS} violations ({remaining} more until ban)", 
                                 Fore.RED if remaining == 1 else Fore.YELLOW)
            else:
                print_colored("No users currently at risk of being banned.", Fore.GREEN)
            
            print_colored("--------------------------------------------------", Fore.BLUE)
            input("\nPress Enter to return to admin menu...")
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def reset_all_violation_attempts():
    """Admin function to reset balance violation attempts for all users"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - RESET VIOLATION ATTEMPTS")
    
    # Count users with violations
    users_with_violations = 0
    for username, violations in max_balance_violation_attempts.items():
        if violations > 0:
            users_with_violations += 1
    
    if users_with_violations == 0:
        print_warning("No users have any balance violation attempts to reset.")
        time.sleep(2)
        show_admin_menu()
        return
    
    print_info(f"There are {users_with_violations} users with balance violation attempts.")
    print_colored("--------------------------------------------------", Fore.BLUE)
    
    # Show users with violations
    for username, violations in max_balance_violation_attempts.items():
        if violations > 0:
            print_colored(f"{username}: {violations}/{MAX_BALANCE_VIOLATIONS} violations", 
                         Fore.RED if violations >= MAX_BALANCE_VIOLATIONS - 1 else Fore.YELLOW)
    
    print_colored("--------------------------------------------------", Fore.BLUE)
    confirm = input(f"{Fore.YELLOW}Are you sure you want to reset ALL violation attempts? (y/n): {Style.RESET_ALL}").lower()
    
    if confirm == 'y':
        # Clear the violation attempts dictionary
        max_balance_violation_attempts.clear()
        print_success("All balance violation attempts have been reset to zero.")
        print_info("Users can now attempt to exceed the maximum balance without previous penalties.")
        time.sleep(3)
    else:
        print_info("Reset operation cancelled.")
        time.sleep(2)
    
    show_admin_menu()

def toggle_admin_granted_visibility():
    """Admin function to toggle the visibility of 'SuperUser Granted' status for users"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - TOGGLE ADMIN GRANTED VISIBILITY")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            # Find users with admin-granted status
            admin_granted_users = []
            for username, user_data in data.items():
                if username.lower() != "superuser" and "admin_granted" in user_data and user_data["admin_granted"] == True:
                    admin_granted_users.append(username)
            
            if not admin_granted_users:
                print_warning("No users with admin-granted status found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_info("Users with admin-granted status:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            for i, username in enumerate(admin_granted_users, 1):
                # Format the number with leading zero if it's a single digit
                formatted_number = f"{i:02d}" if i < 10 else str(i)
                balance = data[username].get('balance', 0)
                hide_status = data[username].get('hide_admin_granted', False)
                status = "[HIDDEN]" if hide_status else "[VISIBLE]"
                print_colored(f"{formatted_number}. {username} (Balance: {balance} Rs) {status}", 
                             Fore.CYAN)
            
            print_colored("--------------------------------------------------", Fore.BLUE)
            choice = input(f"\n{Fore.YELLOW}Enter user number to toggle visibility (or 0 to cancel): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                show_admin_menu()
                return
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(admin_granted_users):
                    username = admin_granted_users[index]
                    
                    # Toggle the hide_admin_granted flag
                    current_status = data[username].get('hide_admin_granted', False)
                    data[username]['hide_admin_granted'] = not current_status
                    
                    # Save changes
                    try:
                        FILE_ATTRIBUTE_NORMAL = 0x80
                        ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                    except Exception as e:
                        print_warning(f"Could not modify file attributes: {str(e)}")
                    
                    with open(CONFIG_FILE, "wb") as f:
                        f.write(encode_to_binary(data))
                    
                    new_status = "hidden from" if data[username]['hide_admin_granted'] else "visible to"
                    print_success(f"SuperUser Granted status for '{username}' is now {new_status} normal users.")
                    time.sleep(2)
                else:
                    print_error("Invalid selection.")
                    time.sleep(2)
            except ValueError:
                print_error("Please enter a valid number.")
                time.sleep(2)
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def show_admin_menu():
    """Show menu for admin users"""
    while True:
        clear_terminal()
        display_banner()
        print_header("SUPERUSER MENU")
        
        print_colored("01. View All Users", Fore.CYAN)
        print_colored("02. Add New User", Fore.CYAN)
        print_colored("03. Remove User", Fore.CYAN)
        print_colored("04. Add Money to User", Fore.CYAN)
        print_colored("05. Remove Money from User", Fore.CYAN)
        print_colored("06. Ban User", Fore.CYAN)
        print_colored("07. Restore Banned User", Fore.CYAN)
        print_colored("08. Unban Permanently Banned User", Fore.CYAN)
        print_colored("09. View Violation Statistics", Fore.CYAN)
        print_colored("10. Reset All Violation Attempts", Fore.CYAN)
        print_colored("11. Grant Free Remember Me", Fore.CYAN)
        print_colored("12. View Download History", Fore.CYAN)
        print_colored("13. View Hidden Files", Fore.CYAN)
        print_colored("14. Create Backup", Fore.CYAN)
        print_colored("15. Restore Backup", Fore.CYAN)
        print_colored("16. Toggle SuperUser Granted Visibility", Fore.CYAN)
        print_colored("17. Login as User", Fore.CYAN)
        print_colored("18. Download YouTube Video/Playlist", Fore.CYAN)
        print_colored("19. Exit SuperUser Mode", Fore.CYAN)
        
        choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}")
        
        if choice == "1" or choice == "01":
            show_all_users()
        elif choice == "2" or choice == "02":
            add_user_menu()
        elif choice == "3" or choice == "03":
            remove_user_menu()
        elif choice == "4" or choice == "04":
            admin_add_money_to_user()
        elif choice == "5" or choice == "05":
            admin_remove_money_from_user()
        elif choice == "6" or choice == "06":
            ban_user()
        elif choice == "7" or choice == "07":
            restore_banned_user()
        elif choice == "8" or choice == "08":
            unban_user()
        elif choice == "9" or choice == "09":
            show_violation_statistics()
        elif choice == "10":
            reset_all_violation_attempts()
        elif choice == "11":
            admin_grant_remember_me()
        elif choice == "12":
            show_all_download_history()
        elif choice == "13":
            show_hidden_files()
        elif choice == "14":
            # Create backup
            success, result = create_backup()
            if success:
                print_success(f"Backup created successfully: {os.path.basename(result)}")
            else:
                print_error(f"Failed to create backup: {result}")
            time.sleep(2)
        elif choice == "15":
            # Restore backup
            success, result = restore_backup()
            if success:
                print_success(f"Backup restored successfully from: {os.path.basename(result)}")
                print_info("The application will now restart...")
                time.sleep(2)
                # Restart the application
                restart_application()
            else:
                print_error(f"Failed to restore backup: {result}")
                time.sleep(2)
        elif choice == "16":
            # Toggle SuperUser Granted visibility
            toggle_admin_granted_visibility()
        elif choice == "17":
            # Login as a regular user
            admin_login_as_user()
        elif choice == "18":
            # Continue to download function
            download_video("superuser")
            return True
        elif choice == "19":
            print_info("Exiting SuperUser mode...")
            time.sleep(1)
            # Reset admin mode flag
            global admin_mode
            admin_mode = False
            # Return to main menu or login screen
            if current_username and current_username != "superuser":
                show_user_menu(current_username)
            else:
                verify_login()
            return False
        else:
            print_warning("Invalid choice")
            time.sleep(1)

# Add function to check if user is remembered

def check_remembered_user():
    """Check if there's a remembered user and load their info"""
    try:
        if os.path.exists(REMEMBER_ME_FILE):
            # Make sure file is readable
            try:
                FILE_ATTRIBUTE_NORMAL = 0x80
                ctypes.windll.kernel32.SetFileAttributesW(str(REMEMBER_ME_FILE), FILE_ATTRIBUTE_NORMAL)
            except Exception:
                pass
                
            try:
                with open(REMEMBER_ME_FILE, 'rb') as f:
                    data = decode_from_binary(f.read())
                    if 'username' in data:
                        # Check if the user is banned before auto-login
                        username = data['username']
                        
                        # Check temporary ban
                        if username in login_attempts and login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                            print_warning(f"Auto-login for {username} failed: Account is temporarily banned.")
                            return None
                            
                        # Check permanent ban
                        if os.path.exists(CONFIG_FILE):
                            with open(CONFIG_FILE, "rb") as config_f:
                                config_data = decode_from_binary(config_f.read())
                                if username in config_data and "banned" in config_data[username] and config_data[username]["banned"] == True:
                                    print_warning(f"Auto-login for {username} failed: Account is permanently banned.")
                                    # Remove the remember me data since the account is banned
                                    forget_user()
                                    return None
                        
                        print_info(f"Auto-login found for user: {username}")
                        return username
            except Exception as e:
                print_warning(f"Error reading remember me file: {str(e)}")
                # If there's an error reading the file, try to delete it
                try:
                    os.remove(REMEMBER_ME_FILE)
                    print_warning("Corrupted remember me file deleted.")
                except:
                    pass
    except Exception as e:
        print_warning(f"Error checking for remembered user: {str(e)}")
    return None

# Add function to remember user

def remember_user(username, force=False):
    """Save user credentials for auto-login"""
    global current_username
    
    try:
        # Check if the user has enough balance to pay for remember me (if not forced)
        if not force:
            user_balance = get_user_balance(username)
            if user_balance < REMEMBER_ME_COST:
                print_error(f"Insufficient balance! You need {REMEMBER_ME_COST} Rs to enable Remember Me.")
                print_info(f"Your balance: {user_balance} Rs")
                time.sleep(2)
                return False
            
            # Deduct the cost from user's balance
            new_balance = update_user_balance(username, -REMEMBER_ME_COST)
            print_success(f"Remember Me activated! {REMEMBER_ME_COST} Rs deducted from your balance.")
            print_info(f"New balance: {new_balance} Rs")
        else:
            print_success(f"Remember Me activated by admin! (No charge)")
        
        # Save username to remember me file using temp file approach
        data = {'username': username, 'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        # First save to a temporary file
        temp_file = os.path.join(tempfile.gettempdir(), "temp_remember.bin")
        with open(temp_file, "wb") as f:
            f.write(encode_to_binary(data))
        
        # Make sure target file is writable if it exists
        if os.path.exists(REMEMBER_ME_FILE):
            try:
                FILE_ATTRIBUTE_NORMAL = 0x80
                ctypes.windll.kernel32.SetFileAttributesW(str(REMEMBER_ME_FILE), FILE_ATTRIBUTE_NORMAL)
            except Exception:
                pass
        
        # Copy from temp to target
        shutil.copy2(temp_file, REMEMBER_ME_FILE)
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except Exception:
            pass
        
        hide_file_windows(REMEMBER_ME_FILE)
        time.sleep(2)
        return True
    except Exception as e:
        print_error(f"Error setting up Remember Me: {str(e)}")
        time.sleep(2)
        return False

# Add function to forget user

def forget_user():
    """Remove saved user credentials"""
    try:
        if os.path.exists(REMEMBER_ME_FILE):
            os.remove(REMEMBER_ME_FILE)
            print_success("Auto-login disabled. You'll need to log in manually next time.")
            time.sleep(2)
            return True
        return True
    except Exception as e:
        print_error(f"Error removing remembered user: {str(e)}")
        time.sleep(2)
        return False

# Add function for remember me settings

def remember_me_settings(username):
    """Manage remember me settings"""
    clear_terminal()
    print_header("REMEMBER ME SETTINGS")
    
    # Display help information about how Remember Me works
    print_info("The Remember Me feature allows you to automatically log in when you start the application.")
    print_info("When enabled, your username will be remembered for the next time you run the program.")
    print_info(f"Cost: {REMEMBER_ME_COST} Rs (one-time payment, until disabled)")
    print_colored("--------------------------------------------------", Fore.BLUE)
    
    # Check if user is already remembered
    is_remembered = False
    remembered_user = check_remembered_user()
    if remembered_user == username:
        is_remembered = True
    
    if is_remembered:
        print_success("Remember Me is ACTIVE for your account.")
        print_info("Your account will be automatically logged in when you start the application.")
        print_colored("--------------------------------------------------", Fore.BLUE)
        print_colored("1. Disable Remember Me", Fore.CYAN)
        print_colored("2. Back to Menu", Fore.CYAN)
        
        choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}")
        
        if choice == "1":
            forget_user()
        
    else:
        print_warning("Remember Me is NOT ACTIVE for your account.")
        print_info("You need to log in manually each time you start the application.")
        print_colored("--------------------------------------------------", Fore.BLUE)
        print_colored(f"Activation Cost: {REMEMBER_ME_COST} Rs", Fore.YELLOW)
        balance = get_user_balance(username)
        print_colored(f"Your Balance: {balance} Rs", Fore.GREEN)
        print_colored("--------------------------------------------------", Fore.BLUE)
        print_colored("1. Enable Remember Me", Fore.CYAN)
        print_colored("2. Back to Menu", Fore.CYAN)
        
        choice = input(f"{Fore.YELLOW}Select option: {Style.RESET_ALL}")
        
        if choice == "1":
            if balance >= REMEMBER_ME_COST:
                remember_user(username)
            else:
                print_error(f"Insufficient balance! You need {REMEMBER_ME_COST} Rs for Remember Me.")
                print_info(f"Please add more money to your account.")
    time.sleep(2)

# Add admin function to grant free remember me

def admin_grant_remember_me():
    """Admin function to grant free remember me to users"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
                
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - GRANT FREE REMEMBER ME")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if not data:
                print_warning("No users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_info("Available users:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            users_to_show = []
            for i, username in enumerate(data.keys(), 1):
                if username.lower() != "superuser":
                    balance = data[username].get('balance', 0)
                    
                    # Check if this user already has remember me
                    remembered_user = check_remembered_user()
                    status = "[ACTIVE]" if remembered_user == username else ""
                    
                    users_to_show.append(username)
                    # Format the number with leading zero if it's a single digit
                    formatted_number = f"{len(users_to_show):02d}" if len(users_to_show) < 10 else str(len(users_to_show))
                    print_colored(f"{formatted_number}. {username} (Balance: {balance} Rs) {status}", Fore.CYAN)
            
            if not users_to_show:
                print_warning("No regular users found.")
                time.sleep(2)
                show_admin_menu()
                return
                
            print_colored("--------------------------------------------------", Fore.BLUE)
            choice = input(f"\n{Fore.YELLOW}Enter user number to grant Remember Me (or 0 to cancel): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                show_admin_menu()
                return
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(users_to_show):
                    username = users_to_show[index]
                    
                    # Grant free Remember Me
                    if remember_user(username, force=True):
                        print_success(f"Free Remember Me granted to {username}!")
                    else:
                        print_error(f"Failed to grant Remember Me to {username}.")
                    
                    time.sleep(2)
                else:
                    print_error("Invalid selection.")
                    time.sleep(2)
            except ValueError:
                print_error("Please enter a valid number.")
                time.sleep(2)
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def show_all_users():
    """Admin function to view all registered users"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - VIEW ALL USERS")
    
    # Refresh banned status to ensure UI is up-to-date
    refresh_banned_status()
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if not data:
                print_warning("No users found.")
                time.sleep(2)
                show_admin_menu()
                return
                
            print_info("Registered users:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            # Count to keep track of displayed users
            user_count = 0
            
            for i, username in enumerate(data.keys(), 1):
                if username.lower() != "superuser":
                    user_count += 1
                    balance = data[username].get('balance', 0)
                    password_hash = data[username].get('password_hash', '')
                    
                    # Check if user is banned
                    banned_status = ""
                    if "banned" in data[username] and data[username]["banned"] == True:
                        banned_status = " [PERMANENTLY BANNED]"
                    elif username in login_attempts and login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                        banned_status = " [TEMPORARILY BANNED]"
                    
                    # Check if user has admin-granted money
                    admin_granted = ""
                    if "admin_granted" in data[username] and data[username]["admin_granted"] == True:
                        admin_granted = " [ADMIN GRANTED]"
                    
                    # Check if admin wants to hide admin-granted status
                    hide_admin_granted = data[username].get('hide_admin_granted', False)
                    if hide_admin_granted:
                        admin_granted += " [HIDDEN]"
                    
                    # Check balance violation attempts
                    violation_info = ""
                    if username in max_balance_violation_attempts and max_balance_violation_attempts[username] > 0:
                        violations = max_balance_violation_attempts[username]
                        violation_info = f" (Balance violations: {violations}/{MAX_BALANCE_VIOLATIONS})"
                    
                    # Format the number with leading zero if it's a single digit
                    formatted_number = f"{user_count:02d}" if user_count < 10 else str(user_count)
                    
                    # Display user information with password hash
                    print_colored(f"{formatted_number}. {username} (Balance: {balance} Rs){banned_status}{admin_granted}{violation_info}", 
                                 Fore.RED if banned_status else Fore.CYAN)
                    print_colored(f"    Password Hash: {password_hash}", Fore.YELLOW)
            
            if user_count == 0:
                print_warning("No regular users found.")
                
            print_colored("--------------------------------------------------", Fore.BLUE)
            input("\nPress Enter to return to admin menu...")
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def add_user_menu():
    """Admin function to add a new user"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - ADD NEW USER")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
        else:
            data = {}
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
        show_admin_menu()
        return
    
    new_username = input("Enter new username: ").strip()
    if not new_username or new_username.lower() == "superuser":
        print_error("Invalid username. Cannot be empty or 'superuser'.")
        time.sleep(2)
        show_admin_menu()
        return
        
    # Check if username already exists
    if new_username in data:
        print_error(f"Username '{new_username}' already exists.")
        time.sleep(2)
        show_admin_menu()
        return
        
    # Get password
    while True:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password == confirm:
            break
        else:
            print_error("Passwords do not match. Try again.")
            
    # Get initial balance
    balance = input("Enter initial balance (Rs): ")
    try:
        balance = int(balance)
        if balance < 0:
            balance = DEFAULT_BALANCE
            print_warning(f"Invalid balance. Using default: {DEFAULT_BALANCE} Rs")
    except ValueError:
        balance = DEFAULT_BALANCE
        print_warning(f"Invalid balance. Using default: {DEFAULT_BALANCE} Rs")
    
    # Add new user
    data[new_username] = {
        "password_hash": hash_password(password),
        "balance": balance,
        "download_history": []
    }
    
    # Save to config file
    try:
        # Make sure target file is writable if it exists
        if os.path.exists(CONFIG_FILE):
            try:
                FILE_ATTRIBUTE_NORMAL = 0x80
                ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
            except Exception as e:
                print_warning(f"Could not modify file attributes: {str(e)}")
        
        # Write directly to the file
        with open(CONFIG_FILE, "wb") as f:
            f.write(encode_to_binary(data))
        
        # Create automatic backup
        create_backup()
        
        print_success(f"User '{new_username}' created successfully!")
        print_success(f"Starting balance: {balance} Rs")
        print_info("User has been added to the system.")
        time.sleep(2)
    except Exception as e:
        print_error(f"Error creating user account: {str(e)}")
        time.sleep(2)
    
    # Return to admin menu
    show_admin_menu()
def remove_user_menu():
    """Admin function to remove a user"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - REMOVE USER")
    
    try:
        if not os.path.exists(CONFIG_FILE):
            print_warning("No user database found.")
            time.sleep(2)
            show_admin_menu()
            return
            
        with open(CONFIG_FILE, "rb") as f:
            data = decode_from_binary(f.read())
        
        if not data:
            print_warning("No users found.")
            time.sleep(2)
            show_admin_menu()
            return
        
        print_info("Available users:")
        print_colored("--------------------------------------------------", Fore.BLUE)
        
        users = []
        for username in data.keys():
            if username.lower() != "superuser":
                users.append(username)
                balance = data[username].get('balance', 0)
                # Format the number with leading zero if it's a single digit
                formatted_number = f"{len(users):02d}" if len(users) < 10 else str(len(users))
                print_colored(f"{formatted_number}. {username} (Balance: {balance} Rs)", Fore.CYAN)
        
        if not users:
            print_warning("No users to remove.")
            time.sleep(2)
            show_admin_menu()
            return
        
        print_colored("--------------------------------------------------", Fore.BLUE)
        choice = input(f"\n{Fore.YELLOW}Enter user number to remove (or 0 to cancel): {Style.RESET_ALL}").strip()
        
        if choice == "0":
            show_admin_menu()
            return
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(users):
                username = users[index]
                
                # Confirm removal
                confirm = input(f"{Fore.RED}Are you sure you want to remove user '{username}'? (y/n): {Style.RESET_ALL}").lower()
                
                if confirm == 'y':
                    # Create backup before removing user
                    create_backup()
                    
                    # Remove user
                    del data[username]
                    
                    # Save changes
                    try:
                        FILE_ATTRIBUTE_NORMAL = 0x80
                        ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                    except Exception as e:
                        print_warning(f"Could not modify file attributes: {str(e)}")
                    
                    with open(CONFIG_FILE, "wb") as f:
                        f.write(encode_to_binary(data))
                    
                    print_success(f"User '{username}' removed successfully!")
                else:
                    print_info("User removal cancelled.")
                
                time.sleep(2)
            else:
                print_error("Invalid selection.")
                time.sleep(2)
        except ValueError:
            print_error("Please enter a valid number.")
            time.sleep(2)
 
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def admin_add_money_to_user():
    """Admin function to add money to a user's balance"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - ADD MONEY TO USER")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if not data:
                print_warning("No users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_info("Available users:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            users = []
            for username in data.keys():
                if username.lower() != "superuser":
                    users.append(username)
                    balance = data[username].get('balance', 0)
                    admin_granted = data[username].get('admin_granted', False)
                    hide_status = data[username].get('hide_admin_granted', False)
                    
                    status = ""
                    if admin_granted:
                        status = " [ADMIN GRANTED]"
                        if hide_status:
                            status += " [HIDDEN]"
                    
                    # Format the number with leading zero if it's a single digit
                    formatted_number = f"{len(users):02d}" if len(users) < 10 else str(len(users))
                    print_colored(f"{formatted_number}. {username} (Current Balance: {balance} Rs){status}", Fore.CYAN)
            
            if not users:
                print_warning("No users to add money to.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_colored("--------------------------------------------------", Fore.BLUE)
            choice = input(f"\n{Fore.YELLOW}Enter user number to add money to (or 0 to cancel): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                show_admin_menu()
                return
            
            # Process user selection
            try:
                index = int(choice) - 1
                if 0 <= index < len(users):
                    username = users[index]
                    current_balance = data[username].get('balance', 0)
                    
                    print_colored(f"Current balance for '{username}': {current_balance} Rs", Fore.GREEN)
                    amount = input(f"{Fore.YELLOW}Enter amount to add (Rs): {Style.RESET_ALL}")
                    
                    try:
                        amount = int(amount)
                        if amount <= 0:
                            print_error("Amount must be positive.")
                            time.sleep(2)
                            admin_add_money_to_user()
                            return
                        
                        # Check if adding this amount would exceed MAX_BALANCE
                        if current_balance + amount > MAX_BALANCE:
                            # Ask if admin wants to exceed the maximum balance limit
                            print_warning(f"Adding {amount} Rs would exceed the maximum balance limit of {MAX_BALANCE} Rs.")
                            print_info(f"Current balance: {current_balance} Rs")
                            print_info(f"New balance would be: {current_balance + amount} Rs")
                            
                            choice = input(f"{Fore.YELLOW}Do you want to exceed the maximum balance limit? (y/n): {Style.RESET_ALL}").lower()
                            
                            if choice == 'y':
                                # Directly update the balance in the data structure
                                new_balance = current_balance + amount
                                data[username]['balance'] = new_balance
                                data[username]['admin_granted'] = True
                                
                                # Ask if admin wants to hide the SuperUser Granted status
                                hide_choice = input(f"{Fore.YELLOW}Hide 'SuperUser Granted' status from normal users? (y/n): {Style.RESET_ALL}").lower()
                                data[username]['hide_admin_granted'] = (hide_choice == 'y')
                                
                                hide_status = "hidden from" if data[username]['hide_admin_granted'] else "visible to"
                                
                                # Save changes
                                try:
                                    FILE_ATTRIBUTE_NORMAL = 0x80
                                    ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                                except Exception as e:
                                    print_warning(f"Could not modify file attributes: {str(e)}")
                                
                                with open(CONFIG_FILE, "wb") as f:
                                    f.write(encode_to_binary(data))
                                
                                print_success(f"Added {amount} Rs to '{username}'!")
                                print_success(f"Balance set to {new_balance} Rs (exceeds maximum limit)")
                                print_info(f"SuperUser Granted status is now {hide_status} normal users.")
                            else:
                                # Ask if admin wants to set to max instead
                                choice = input(f"{Fore.YELLOW}Set to maximum balance instead? (y/n): {Style.RESET_ALL}").lower()
                                
                                if choice == 'y':
                                    # Set to maximum balance
                                    actual_add = MAX_BALANCE - current_balance
                                    new_balance = update_user_balance(username, actual_add)
                                    print_success(f"Added {actual_add} Rs to '{username}'!")
                                    print_success(f"Balance set to maximum: {new_balance} Rs")
                                else:
                                    # Cancel operation
                                    print_info("Operation cancelled.")
                                    time.sleep(2)
                                    admin_add_money_to_user()
                                    return
                        else:
                            # Update balance normally
                            new_balance = update_user_balance(username, amount)
                            print_success(f"Added {amount} Rs to '{username}'!")
                            print_success(f"New balance: {new_balance} Rs")
                    except ValueError:
                        print_error("Please enter a valid amount.")
                    
                    time.sleep(2)
                else:
                    print_error("Invalid selection.")
                    time.sleep(2)
            except ValueError:
                print_error("Please enter a valid number.")
                time.sleep(2)
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def admin_remove_money_from_user():
    """Admin function to remove money from a user's balance"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - REMOVE MONEY FROM USER")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if not data:
                print_warning("No users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_info("Available users:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            users = []
            for username in data.keys():
                if username.lower() != "superuser":
                    users.append(username)
                    balance = data[username].get('balance', 0)
                    # Format the number with leading zero if it's a single digit
                    formatted_number = f"{len(users):02d}" if len(users) < 10 else str(len(users))
                    print_colored(f"{formatted_number}. {username} (Current Balance: {balance} Rs)", Fore.CYAN)
            
            if not users:
                print_warning("No users to remove money from.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_colored("--------------------------------------------------", Fore.BLUE)
            choice = input(f"\n{Fore.YELLOW}Enter user number to remove money from (or 0 to cancel): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                show_admin_menu()
                return
            
            # Process user selection
            try:
                index = int(choice) - 1
                if 0 <= index < len(users):
                    username = users[index]
                    current_balance = data[username].get('balance', 0)
                    
                    print_colored(f"Current balance for '{username}': {current_balance} Rs", Fore.GREEN)
                    amount = input(f"{Fore.YELLOW}Enter amount to remove (Rs): {Style.RESET_ALL}")
                    
                    try:
                        amount = int(amount)
                        if amount <= 0:
                            print_error("Amount must be positive.")
                            time.sleep(2)
                            admin_remove_money_from_user()
                            return
                        
                        if amount > current_balance:
                            print_warning(f"Amount exceeds current balance. Maximum you can remove is {current_balance} Rs.")
                            confirm_all = input(f"{Fore.YELLOW}Remove all balance? (y/n): {Style.RESET_ALL}").lower()
                            if confirm_all == 'y':
                                amount = current_balance
                            else:
                                time.sleep(2)
                                admin_remove_money_from_user()
                                return
                        
                        # Update balance
                        new_balance = current_balance - amount
                        data[username]['balance'] = new_balance
                        
                        # If balance is now below MAX_BALANCE, remove admin_granted flag if it exists
                        if new_balance <= MAX_BALANCE and 'admin_granted' in data[username]:
                            data[username]['admin_granted'] = False
                            print_info("User no longer has admin-granted money status.")
                        
                        # Save changes
                        try:
                            FILE_ATTRIBUTE_NORMAL = 0x80
                            ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                        except Exception as e:
                            print_warning(f"Could not modify file attributes: {str(e)}")
                        
                        with open(CONFIG_FILE, "wb") as f:
                            f.write(encode_to_binary(data))
                        
                        print_success(f"Removed {amount} Rs from '{username}'!")
                        print_success(f"New balance: {new_balance} Rs")
                    except ValueError:
                        print_error("Please enter a valid amount.")
                    
                    time.sleep(2)
                else:
                    print_error("Invalid selection.")
                    time.sleep(2)
            except ValueError:
                print_error("Please enter a valid number.")
                time.sleep(2)
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def show_all_download_history():
    """Admin function to view download history for all users"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - ALL DOWNLOAD HISTORY")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            total_downloads = 0
            total_download_time = 0
            total_skipped_files = 0
            total_downloaded_files = 0
            
            for username, user_data in data.items():
                if username.lower() != "superuser":
                    history = user_data.get('download_history', [])
                    if history:
                        print_colored(f"User: {username}", Fore.CYAN, Style.BRIGHT)
                        print_colored("--------------------------------------------------", Fore.BLUE)
                        
                        for i, entry in enumerate(history, 1):
                            title = entry.get('title', 'Unknown')
                            date = entry.get('date', 'Unknown')
                            format_type = entry.get('format', 'Unknown')
                            cost = entry.get('cost', 0)
                            summary = entry.get('summary', f"{format_type}")
                            speed_boost = entry.get('speed_boost', False)
                            download_time = entry.get('download_time', "Unknown")
                            download_seconds = entry.get('download_seconds', 0)
                            upload_date = entry.get('upload_date', "Unknown date")
                            skipped = entry.get('skipped_files', 0)
                            downloaded = entry.get('downloaded_files', 0)
                            total = entry.get('total_files', 0)
                            seq_naming = entry.get('sequential_naming', True)
                            
                            print_colored(f"[{i}] {title}", Fore.GREEN)
                            print_colored(f"   Date: {date} | Upload Date: [{upload_date}] | Format: {format_type} | Cost: {cost} Rs", Fore.CYAN)
                            print_colored(f"   Summary: {summary}", Fore.YELLOW)
                            if speed_boost:
                                print_colored(f"   Speed Boost: ENABLED | Download Time: {download_time}", Fore.MAGENTA)
                            else:
                                print_colored(f"   Download Time: {download_time}", Fore.BLUE)
                            
                            # Show file statistics if available
                            if total > 0:
                                naming_str = "Sequential Numbering" if seq_naming else "Title Only"
                                if skipped > 0:
                                    print_colored(f"   Files: {downloaded} new, {skipped} skipped (already existed) | Naming: {naming_str}", Fore.YELLOW)
                                else:
                                    print_colored(f"   Files: {downloaded} downloaded | Naming: {naming_str}", Fore.CYAN)
                            
                            print_colored("--------------------------------------------------", Fore.BLUE)
                            
                            total_downloads += 1
                            total_download_time += download_seconds
                            total_skipped_files += skipped
                            total_downloaded_files += downloaded
            
            if total_downloads == 0:
                print_warning("No download history found for any user.")
            else:
                # Format total download time
                if total_download_time < 60:
                    minutes = 0
                    seconds = int(total_download_time)
                    time_str = f"{seconds} seconds ({minutes}m {seconds}s)"
                elif total_download_time < 3600:
                    minutes = int(total_download_time // 60)
                    seconds = int(total_download_time % 60)
                    time_str = f"{minutes} minutes {seconds} seconds ({minutes}m {seconds}s)"
                else:
                    hours = int(total_download_time // 3600)
                    minutes = int((total_download_time % 3600) // 60)
                    seconds = int(total_download_time % 60)
                    time_str = f"{hours} hours {minutes} minutes {seconds} seconds ({hours}h {minutes}m {seconds}s)"
                
                print_success(f"Total downloads across all users: {total_downloads}")
                print_success(f"Total download time: {time_str}")
                print_success(f"Total files downloaded: {total_downloaded_files} new, {total_skipped_files} skipped")
            
            input("\nPress Enter to return to admin menu...")
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def show_hidden_files():
    """Admin function to view hidden files in the application directory"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - HIDDEN FILES")
    
    try:
        hidden_files = [
            CONFIG_FILE,
            HISTORY_FILE,
            "master_password.bin",
            REMEMBER_ME_FILE
        ]
        
        print_info("Hidden files in application directory:")
        print_colored("--------------------------------------------------", Fore.BLUE)
        
        for i, file in enumerate(hidden_files, 1):
            if os.path.exists(file):
                file_size = os.path.getsize(file)
                last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d %H:%M:%S")
                print_colored(f"{i}. {file}", Fore.CYAN)
                print_colored(f"   Size: {file_size} bytes | Last Modified: {last_modified}", Fore.GREEN)
                print_colored("--------------------------------------------------", Fore.BLUE)
            else:
                print_colored(f"{i}. {file} (Not Found)", Fore.RED)
                print_colored("--------------------------------------------------", Fore.BLUE)
        
        input("\nPress Enter to return to admin menu...")
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def create_hidden_files():
    """Create all necessary hidden files with default values"""
    try:
        # List of files to check and create
        files_to_create = [
            CONFIG_FILE,
            HISTORY_FILE, 
            "master_password.bin",
            REMEMBER_ME_FILE
        ]
        
        # First, make sure all existing files are writable
        for file_path in files_to_create:
            if os.path.exists(file_path):
                try:
                    if platform.system() == "Windows":
                        FILE_ATTRIBUTE_NORMAL = 0x80
                        ctypes.windll.kernel32.SetFileAttributesW(str(file_path), FILE_ATTRIBUTE_NORMAL)
                except Exception as e:
                    print_warning(f"Could not modify attributes for {file_path}: {str(e)}")
        
        # Create CONFIG_FILE if it doesn't exist
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "superuser": {
                    "password_hash": hash_password("admin"),
                    "balance": 9999,
                    "download_history": []
                }
            }
            try:
                # Use temp file approach
                temp_file = os.path.join(tempfile.gettempdir(), "temp_config.bin")
                with open(temp_file, "wb") as f:
                    f.write(encode_to_binary(default_config))
                
                # Copy to final location
                shutil.copy2(temp_file, CONFIG_FILE)
                
                # Clean up temp file
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                hide_file_windows(CONFIG_FILE)
            except Exception as e:
                print_warning(f"Could not create {CONFIG_FILE}: {str(e)}")
        
        # Create HISTORY_FILE if it doesn't exist
        if not os.path.exists(HISTORY_FILE):
            default_history = []
            try:
                # Use temp file approach
                temp_file = os.path.join(tempfile.gettempdir(), "temp_history.bin")
                with open(temp_file, "wb") as f:
                    f.write(encode_to_binary(default_history))
                
                # Copy to final location
                shutil.copy2(temp_file, HISTORY_FILE)
                
                # Clean up temp file
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                hide_file_windows(HISTORY_FILE)
            except Exception as e:
                print_warning(f"Could not create {HISTORY_FILE}: {str(e)}")
            
        # Create master password file if it doesn't exist
        master_file = "master_password.bin"
        if not os.path.exists(master_file):
            default_master = {
                "master_password": hash_password("admin"),
                "is_set": False
            }
            try:
                # Use temp file approach
                temp_file = os.path.join(tempfile.gettempdir(), "temp_master.bin")
                with open(temp_file, "wb") as f:
                    f.write(encode_to_binary(default_master))
                
                # Copy to final location
                shutil.copy2(temp_file, master_file)
                
                # Clean up temp file
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                hide_file_windows(master_file)
            except Exception as e:
                print_warning(f"Could not create {master_file}: {str(e)}")
            
        # Create REMEMBER_ME_FILE if it doesn't exist
        if not os.path.exists(REMEMBER_ME_FILE):
            default_remember = {}
            try:
                # Use temp file approach
                temp_file = os.path.join(tempfile.gettempdir(), "temp_remember.bin")
                with open(temp_file, "wb") as f:
                    f.write(encode_to_binary(default_remember))
                
                # Copy to final location
                shutil.copy2(temp_file, REMEMBER_ME_FILE)
                
                # Clean up temp file
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                hide_file_windows(REMEMBER_ME_FILE)
            except Exception as e:
                print_warning(f"Could not create {REMEMBER_ME_FILE}: {str(e)}")
            
    except Exception as e:
        print_error(f"Error creating hidden files: {str(e)}")

def first_time_setup():
    """Handle first-time setup of the application"""
    clear_terminal()
    
    # Display the banner
    display_banner()
    
    print_header("FIRST TIME SETUP")
    print_info("Welcome to YouTube Downloader Pro!")
    print_info("This appears to be your first time running the application.")
    print_info("Let's set up your account...")
    
    # Create all necessary hidden files
    create_hidden_files()
    
    # Force setup login to create a real user account
    print_info("Now you need to create your user account.")
    print_info("This will be used to log in to the application.")
    time.sleep(12)  # Reduced wait time
    
    # Get username and password directly here instead of in setup_login
    clear_terminal()
    print_header("CREATE YOUR USER ACCOUNT")
    
    username = input("Enter username: ").strip()
    while not username or username.lower() == "superuser":
        print_error("Invalid username. Cannot be empty or 'superuser'.")
        username = input("Enter username: ").strip()
    
    # Get password
    while True:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password == confirm:
            break
        print_error("Passwords do not match. Try again.")
    
    # Create or update the config file with the new user
    try:
        if os.path.exists(CONFIG_FILE):
            # Make the file writable first
            try:
                FILE_ATTRIBUTE_NORMAL = 0x80
                ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
            except Exception as e:
                print_warning(f"Could not modify file attributes: {str(e)}")
                
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
        else:
            data = {}
        
        # Add the new user
        data[username] = {
            "password_hash": hash_password(password),
            "balance": DEFAULT_BALANCE,
            "download_history": []
        }
        
        # Save to config file using temp file approach
        try:
            # First save to a temporary file
            temp_file = os.path.join(tempfile.gettempdir(), "temp_config.bin")
            with open(temp_file, "wb") as f:
                f.write(encode_to_binary(data))
            
            # Make sure target file is writable if it exists
            if os.path.exists(CONFIG_FILE):
                try:
                    FILE_ATTRIBUTE_NORMAL = 0x80
                    ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                except Exception:
                    pass
            
            # Copy from temp to target
            shutil.copy2(temp_file, CONFIG_FILE)
            
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Create initial backup
            create_backup()
            
            # Enable remember me by default
            remember_user(username, force=True)
            
            print_success(f"User '{username}' created successfully!")
            print_success(f"Starting balance: {DEFAULT_BALANCE} Rs")
            print_info("Remember Me has been enabled by default for your convenience.")
            print_info("You can switch between accounts anytime using the 'Switch Account' option in the menu.")
            time.sleep(14)  # Show the message for 14 seconds
            print_info("The application will now restart...")
            time.sleep(2)
            
            # Prompt for manual restart
            print("\n" + "=" * 60)
            print("           APPLICATION RESTART REQUIRED")
            print("=" * 60)
            print("Setup complete! Please restart the program manually:")
            print("1. Close this window")
            print("2. Run the program again: Youtube Downloder.exe")
            print("=" * 60)
            input("Press Enter to exit...")
            sys.exit(0)
        except Exception as e:
            print_error(f"Error creating user account: {str(e)}")
            print_error("Setup failed. Please try again.")
            time.sleep(2)
            sys.exit(1)
    except Exception as e:
        print_error(f"Error creating user account: {str(e)}")
        print_error("Setup failed. Please try again.")
        time.sleep(2)
        sys.exit(1)

# Update main to check for remembered user

def display_banner():
    """Display the YouTube Downloader ASCII art banner"""
#     print_colored("""__   __         _____      _           ______                    _                 _           
#   \\ \\ / /        |_   _|    | |          |  _  \\                  | |               | |          
#    \\ V /___  _   _ | |_   _ | |__   ___  | | | |_____      ___ __ | | ___   __ _  __| | ___ _ __ 
#     \\ // _ \\| | | || | | | || '_ \\ / _ \\ | | | / _ \\ \\ /\\ / / '_ \\| |/ _ \\ / _` |/ _` |/ _ \\ '__|
#     | | (_) | |_| || | |_| || |_) |  __/ | |/ / (_) \\ V  V /| | | | | (_) | (_| | (_| |  __/ |   
#     \\_/\\___/ \\__,_\\_/\\__,_||_.__/ \\___| |___/ \\___/ \\_/\\_/ |_| |_|_|\\___/ \\__,_|\\__,_|\\___|_|""", Fore.CYAN, Style.BRIGHT)
    
    print_header("Welcome to YouTube Downloader Pro")
    print_colored("This tool lets you download videos and playlists from YouTube", Fore.GREEN)
    print_colored("Created by: HTSPOP0007", Fore.YELLOW, Style.BRIGHT)
    print_colored("Version: 1.0.0", Fore.YELLOW, Style.BRIGHT)
    print_colored("--------------------------------------------------", Fore.BLUE)

def main():
    global MASTER_PASSWORD_HASH, admin_mode, master_password_set, current_username, login_attempts, max_balance_violation_attempts
    
    # Initialize admin_mode to False at start
    admin_mode = False
    
    # Make sure we start with a clean terminal - use improved clear_terminal
    clear_terminal()
    
    # Display welcome message with cool ASCII art
    display_banner()
    
    # Create all hidden files if they don't exist
    try:
        create_hidden_files()
    except Exception as e:
        print_warning(f"Error initializing files: {str(e)}")
    
    # Ensure all configuration files are hidden first
    config_files = [CONFIG_FILE, HISTORY_FILE, "master_password.bin", REMEMBER_ME_FILE]
    for file in config_files:
        if os.path.exists(file):
            hide_file_windows(file)
    
    # Load banned users from config file
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            # Load banned status into login_attempts
            for username, user_data in data.items():
                if "banned" in user_data and user_data["banned"] == True:
                    login_attempts[username] = MAX_LOGIN_ATTEMPTS
    except Exception as e:
        print_warning(f"Error loading banned users: {str(e)}")
    
    # Create daily backup if needed
    try:
        if os.path.exists(CONFIG_FILE):
            # Check if we need to create a daily backup
            create_daily_backup = False
            
            # Check if backup directory exists
            if not os.path.exists(BACKUP_DIR):
                create_daily_backup = True
            else:
                # Check if we have a backup from today
                today = datetime.datetime.now().strftime("%Y%m%d")
                today_backups = glob.glob(os.path.join(BACKUP_DIR, f"backup_{today}*.zip"))
                
                if not today_backups:
                    create_daily_backup = True
            
            if create_daily_backup:
                create_backup()
    except Exception:
        # Silently ignore backup errors during startup
        pass
    
    # Check if this is the first time running the program or no users exist
    first_time = False
    if not os.path.exists(CONFIG_FILE):
        first_time = True
    else:
        try:
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            # Check if there are any user accounts (excluding superuser)
            user_accounts = [user for user in data.keys() if user != "superuser"]
            if not user_accounts:
                first_time = True
        except Exception as e:
            print_warning(f"Error reading config file: {str(e)}")
            first_time = True
    
    if first_time:
        print_info("First time running the application or no user accounts found.")
        first_time_setup()
        return  # The program will restart after setup
        
    # Try to load master password from file
    master_file = "master_password.bin"
    if os.path.exists(master_file):
        try:
            with open(master_file, "rb") as f:
                data = decode_from_binary(f.read())
                if "master_password" in data:
                    MASTER_PASSWORD_HASH = data["master_password"]
                if "is_set" in data:
                    master_password_set = data["is_set"]
        except Exception:
            pass
    
    # Check for remembered user
    remembered_username = check_remembered_user()
    if remembered_username:
        print_success(f"Welcome back, {remembered_username}!")
        print_info("Auto-login active. Logging you in...")
        print_colored("You can switch between accounts anytime using the 'Switch Account' option in the menu", Fore.GREEN)
        time.sleep(14)  # Show the message for 14 seconds
            
        try:
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
                
            if remembered_username in data:
                # Auto-login the user
                current_username = remembered_username
                admin_mode = False
                
                # Main application loop
                while True:
                # Show user menu
                    menu_result = show_user_menu(remembered_username)
                    
                    if menu_result == True:
                        # User selected option 1 (download)
                        download_result = download_video(remembered_username)
                        # If download returns False, it means go back to main menu
                        continue
                    elif menu_result == False:
                        # User selected to switch accounts, go to login screen
                        verify_login()
                        break
            else:
                print_warning(f"Remembered user '{remembered_username}' not found in database.")
                print_info("Please log in manually.")
                time.sleep(2)
                forget_user()
                verify_login()
        except Exception as e:
            print_error(f"Auto-login error: {str(e)}")
            print_info("Please log in manually.")
            time.sleep(2)
            verify_login()
    else:
        # Login system
        try:
            # Main application loop
            while True:
                login_result = verify_login()
                if not login_result:
                    # If login fails or user exits, break the loop
                    break
        except Exception as e:
            print_warning(f"Login system error: {str(e)}")
            print_info("Continuing without login...")
            time.sleep(2)
            setup_login()

def process_command(command, username):
    """Process special commands entered in the URL field"""
    global MASTER_PASSWORD_HASH, master_password_set, admin_mode
    
    # Admin activation command
    if command.startswith("SuperUser:Mode") and username != "superuser":
        print_info("SuperUser mode activation requested...")
        password = getpass.getpass("Enter SuperUser password: ")
        if hash_password(password) == MASTER_PASSWORD_HASH:
            print_success("SuperUser mode activated!")
            admin_mode = True
            time.sleep(1)
            show_admin_menu()
            return True
        else:
            print_error("Invalid SuperUser password.")
            time.sleep(1)
            return False
    
    # Set master password command
    elif command.startswith("SuperUser:") and len(command) > 10 and not command.startswith("SuperUser:Mode"):
        new_password = command[10:]
        MASTER_PASSWORD_HASH = hash_password(new_password)
        master_password_set = True
        
        # Save to master password file
        master_file = "master_password.bin"
        master_data = {
            "master_password": MASTER_PASSWORD_HASH,
            "is_set": True
        }
        
        try:
            # First make sure the file is writable if it exists
            if os.path.exists(master_file):
                try:
                    FILE_ATTRIBUTE_NORMAL = 0x80
                    ctypes.windll.kernel32.SetFileAttributesW(str(master_file), FILE_ATTRIBUTE_NORMAL)
                except Exception:
                    pass
            
            # Use temp file approach
            temp_file = os.path.join(tempfile.gettempdir(), "temp_master.bin")
            with open(temp_file, "wb") as f:
                f.write(encode_to_binary(master_data))
            
            # Copy to final location
            try:
                shutil.copy2(temp_file, master_file)
            except PermissionError:
                print_warning("Permission denied. Trying alternative method...")
                # Try direct write if copy fails
                with open(master_file, "wb") as f:
                    f.write(encode_to_binary(master_data))
            
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
    
            hide_file_windows(master_file)
            print_success(f"SuperUser password set successfully!")
        except Exception as e:
            print_error(f"Error setting SuperUser password: {str(e)}")
            print_info("Try running the program as administrator or check file permissions.")
        
        time.sleep(2)
        return True
    
    # Money add command
    elif command == MONEY_COMMAND:
        if username:
            # Check if user data exists
            try:
                with open(CONFIG_FILE, "rb") as f:
                    data = decode_from_binary(f.read())
                
                if username in data:
                    current_balance = data[username].get('balance', 0)
                    admin_granted = data[username].get('admin_granted', False)
                    
                    # Define the amount to add
                    add_amount = 600
                    
                    # Check if adding this amount would exceed MAX_BALANCE
                    if username.lower() != "superuser" and current_balance >= MAX_BALANCE and not admin_granted:
                        # Track violation attempt
                        if username not in max_balance_violation_attempts:
                            max_balance_violation_attempts[username] = 1
                        else:
                            max_balance_violation_attempts[username] += 1
                        
                        # Check if user has reached the violation limit
                        if max_balance_violation_attempts[username] >= MAX_BALANCE_VIOLATIONS:
                            # Ban the user
                            login_attempts[username] = MAX_LOGIN_ATTEMPTS
                            
                            # Save the ban status to make it permanent
                            try:
                                if os.path.exists(CONFIG_FILE):
                                    with open(CONFIG_FILE, "rb") as f:
                                        data = decode_from_binary(f.read())
                                    
                                    if username in data:
                                        data[username]['banned'] = True
                                        
                                        # Create a new account with the same username + "_new"
                                        new_username = username + "_new"
                                        
                                        # Check if the new username already exists
                                        counter = 1
                                        while new_username in data:
                                            new_username = f"{username}_new{counter}"
                                            counter += 1
                                        
                                        # Create new account with default balance
                                        data[new_username] = {
                                            "password_hash": data[username]["password_hash"],  # Same password
                                            "balance": DEFAULT_BALANCE,
                                            "download_history": []
                                        }
                                        
                                        # Make the file writable
                                        try:
                                            FILE_ATTRIBUTE_NORMAL = 0x80
                                            ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                                        except Exception as e:
                                            print_warning(f"Could not modify file attributes: {str(e)}")
                                        
                                        with open(CONFIG_FILE, "wb") as f:
                                            f.write(encode_to_binary(data))
                                        
                                        # Refresh banned status to ensure UI is up-to-date
                                        refresh_banned_status()
                                        
                                        print_error(f"Your account has been permanently banned for attempting to exceed the maximum balance limit {MAX_BALANCE_VIOLATIONS} times!")
                                        print_error("This is a serious violation of our terms of service.")
                                        print_success(f"However, a new account '{new_username}' has been created for you with default balance.")
                                        print_success(f"You can use the same password to log in to your new account.")
                                        print_info("You will be logged out in 5 seconds...")
                                        time.sleep(5)
                                        
                                        # Force logout
                                        verify_login()
                                        return True
                            except Exception as e:
                                print_warning(f"Could not save ban status: {str(e)}")
                            
                            print_error(f"Your account has been permanently banned for attempting to exceed the maximum balance limit {MAX_BALANCE_VIOLATIONS} times!")
                            print_error("This is a serious violation of our terms of service.")
                            print_error("Contact a SuperUser if you believe this is an error.")
                            time.sleep(5)
                            
                            # Force logout
                            print_info("You will be logged out in 5 seconds...")
                            time.sleep(5)
                            verify_login()
                            return True
                        
                        # Warning message with attempt count
                        remaining_attempts = MAX_BALANCE_VIOLATIONS - max_balance_violation_attempts[username]
                        print_warning(f"Your balance is already at the maximum limit of {MAX_BALANCE} Rs!")
                        print_warning(f"Attempting to exceed the maximum balance is a violation of our terms of service.")
                        print_error(f"WARNING: You have {remaining_attempts} more attempts before your account is permanently banned!")
                        print_colored(f"Current balance: {current_balance} Rs", Fore.GREEN)
                        time.sleep(4)  # Give them time to read the warning
                        return True
                    elif username.lower() != "superuser" and current_balance + add_amount > MAX_BALANCE and not admin_granted:
                        # Calculate how much can be added without exceeding MAX_BALANCE
                        actual_add = MAX_BALANCE - current_balance
                        new_balance = update_user_balance(username, actual_add)
                        print_success(f"Added {actual_add} Rs to your account!")
                        print_warning(f"You've reached the maximum balance limit of {MAX_BALANCE} Rs!")
                        print_colored(f"New balance: {new_balance} Rs", Fore.GREEN)
                        time.sleep(2)
                        return True
                    else:
                        # Regular case - add the full amount
                        new_balance = update_user_balance(username, add_amount)
                        print_success(f"Added {add_amount} Rs to your account!")
                        print_colored(f"New balance: {new_balance} Rs", Fore.GREEN)
                        time.sleep(2)
                        return True
            except Exception as e:
                print_error(f"Error processing command: {str(e)}")
                time.sleep(2)
                return False
        else:
            print_error("You must be logged in to use this command.")
            time.sleep(1)
            return False# Speed boost command (hidden)
    elif command == "Speed:Boost":
        if username:
            current_balance = get_user_balance(username)
            if current_balance >= SPEED_BOOST_COST:
                new_balance = update_user_balance(username, -SPEED_BOOST_COST)
                print_success(f"Speed boost activated! {SPEED_BOOST_COST} Rs deducted.")
                print_colored(f"New balance: {new_balance} Rs", Fore.GREEN)
                time.sleep(2)
                return True
            else:
                print_error(f"Insufficient balance! You need {SPEED_BOOST_COST} Rs for speed boost.")
                time.sleep(1)
                return False
        else:
            print_error("You must be logged in to use this command.")
            time.sleep(1)
            return False
            
    # Show version info (hidden)
    elif command == "Version:Info":
        print_header("VERSION INFORMATION")
        print_info("YouTube Downloader Pro")
        print_info("Version: 1.0.0")
        print_info("Created by: HTSPOP0007")
        print_info("Last Updated: May 2025")
        time.sleep(3)
        return True
    
    # No valid command found
    return False

def process_hidden_commands(username):
    """Process hidden commands directly from the menu"""
    clear_terminal()
    print_header("COMMAND CONSOLE")
    print_info("Enter a command or type 'exit' to return to menu")
    
    command = input(f"{Fore.YELLOW}Command: {Style.RESET_ALL}").strip()
    
    if command.lower() == 'exit':
        return
    
    # Process the command using the existing function
    process_command(command, username)
    
    input("\nPress Enter to return to the menu...")

# Add backup system functions

def create_backup():
    """Create a backup of all configuration files"""
    try:
        # Create backup directory if it doesn't exist
        if not os.path.exists(BACKUP_DIR):
            try:
                os.makedirs(BACKUP_DIR, exist_ok=True)
                hide_file_windows(BACKUP_DIR)
            except Exception as e:
                print_warning(f"Could not create backup directory: {str(e)}")
                return False, "Could not create backup directory"
        
        # Get timestamp for backup filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")
        
        # Files to backup
        files_to_backup = [
            CONFIG_FILE,
            HISTORY_FILE,
            "master_password.bin",
            REMEMBER_ME_FILE
        ]
        
        # Only backup files that exist
        existing_files = [f for f in files_to_backup if os.path.exists(f)]
        
        if not existing_files:
            return False, "No files to backup"
        
        # Create zip file
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in existing_files:
                zipf.write(file)
        
        # Hide the backup file
        hide_file_windows(backup_file)
        
        # Clean up old backups (keep only 5 most recent)
        backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.zip")))
        if len(backup_files) > 5:
            for old_file in backup_files[:-5]:
                try:
                    os.remove(old_file)
                except:
                    pass
        
        return True, backup_file
    except Exception as e:
        print_warning(f"Backup error: {str(e)}")
        return False, str(e)

def restore_backup():
    """Restore configuration from a backup file"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return False
    
    try:
        if not os.path.exists(BACKUP_DIR):
            return False, "No backups found"
        
        # Get list of backup files
        backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.zip")))
        
        if not backup_files:
            return False, "No backup files found"
        
        clear_terminal()
        print_header("RESTORE FROM BACKUP")
        print_info("Available backups:")
        
        for i, backup in enumerate(backup_files, 1):
            # Extract timestamp from filename
            filename = os.path.basename(backup)
            timestamp = filename.replace("backup_", "").replace(".zip", "")
            try:
                # Convert timestamp to readable format
                date = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                date_str = date.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_str = timestamp
                
            print_colored(f"{i}. Backup from {date_str}", Fore.CYAN)
        
        choice = input(f"\n{Fore.YELLOW}Enter backup number to restore (or 0 to cancel): {Style.RESET_ALL}").strip()
        
        if choice == "0":
            return False, "Cancelled by user"
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(backup_files):
                selected_backup = backup_files[index]
                
                # Confirm restoration
                confirm = input(f"{Fore.RED}Are you sure you want to restore this backup? Current data will be overwritten. (y/n): {Style.RESET_ALL}").lower()
                
                if confirm != 'y':
                    return False, "Cancelled by user"
                
                # Make sure all target files are writable
                files_to_restore = [
                    CONFIG_FILE,
                    HISTORY_FILE,
                    "master_password.bin",
                    REMEMBER_ME_FILE
                ]
                
                for file_path in files_to_restore:
                    if os.path.exists(file_path):
                        try:
                            FILE_ATTRIBUTE_NORMAL = 0x80
                            ctypes.windll.kernel32.SetFileAttributesW(str(file_path), FILE_ATTRIBUTE_NORMAL)
                        except:
                            pass
                
                # Extract the backup
                with zipfile.ZipFile(selected_backup, 'r') as zipf:
                    zipf.extractall()
                
                # Hide the files again
                for file_path in files_to_restore:
                    if os.path.exists(file_path):
                        hide_file_windows(file_path)
                
                return True, selected_backup
            else:
                return False, "Invalid selection"
        except ValueError:
            return False, "Please enter a valid number"
            
    except Exception as e:
        return False, str(e)

def restart_application():
    """Prompt the user to restart the application manually instead of doing it automatically"""
    try:
        print("\n" + "=" * 60)
        print("           APPLICATION RESTART REQUIRED")
        print("=" * 60)
        print("Changes have been made that require restarting the application.")
        print("Please manually restart the program by:")
        print("1. Closing this window")
        print("2. Running the program again: python Youtube_Downloder.py")
        print("=" * 60)
        input("Press Enter to exit...")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Error during restart: {str(e)}")
        print("Please restart the application manually.")
        time.sleep(3)
        sys.exit(1)

def ban_user():
    """Admin function to manually ban a user"""
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - BAN USER")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if not data:
                print_warning("No users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_info("Available users:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            users = []
            for username in data.keys():
                if username.lower() != "superuser":
                    users.append(username)
                    # Check if user is already banned
                    banned = False
                    for attempt_user, attempts in login_attempts.items():
                        if attempt_user.lower() == username.lower() and attempts >= MAX_LOGIN_ATTEMPTS:
                            banned = True
                            break
                    
                    status = "[BANNED]" if banned else ""
                    # Format the number with leading zero if it's a single digit
                    formatted_number = f"{len(users):02d}" if len(users) < 10 else str(len(users))
                    print_colored(f"{formatted_number}. {username} {status}", Fore.CYAN)
            
            if not users:
                print_warning("No users to ban.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_colored("--------------------------------------------------", Fore.BLUE)
            choice = input(f"\n{Fore.YELLOW}Enter user number to ban (or 0 to cancel): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                show_admin_menu()
                return
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(users):
                    username = users[index]
                    
                    # Check if already banned
                    already_banned = False
                    for attempt_user, attempts in login_attempts.items():
                        if attempt_user.lower() == username.lower() and attempts >= MAX_LOGIN_ATTEMPTS:
                            already_banned = True
                            break
                    
                    if already_banned:
                        print_warning(f"User '{username}' is already banned.")
                        time.sleep(2)
                        ban_user()
                        return
                    
                    # Confirm ban
                    confirm = input(f"{Fore.RED}Are you sure you want to ban user '{username}'? (y/n): {Style.RESET_ALL}").lower()
                    
                    if confirm == 'y':
                        # Set login attempts to max
                        login_attempts[username] = MAX_LOGIN_ATTEMPTS
                        
                        # Also set the banned flag in the config file for permanent ban
                        try:
                            if os.path.exists(CONFIG_FILE):
                                with open(CONFIG_FILE, "rb") as f:
                                    file_data = decode_from_binary(f.read())
                                
                                if username in file_data:
                                    file_data[username]['banned'] = True
                                    
                                    # Make the file writable
                                    try:
                                        FILE_ATTRIBUTE_NORMAL = 0x80
                                        ctypes.windll.kernel32.SetFileAttributesW(str(CONFIG_FILE), FILE_ATTRIBUTE_NORMAL)
                                    except Exception as e:
                                        print_warning(f"Could not modify file attributes: {str(e)}")
                                    
                                    with open(CONFIG_FILE, "wb") as f:
                                        f.write(encode_to_binary(file_data))
                                    
                                    # Refresh banned status to ensure UI is up-to-date
                                    refresh_banned_status()
                        except Exception as e:
                            print_warning(f"Could not update ban status in file: {str(e)}")
                        
                        print_success(f"User '{username}' has been banned successfully.")
                        time.sleep(2)
                    else:
                        print_info("Ban operation cancelled.")
                        time.sleep(2)
                else:
                    print_error("Invalid selection.")
                    time.sleep(2)
            except ValueError:
                print_error("Please enter a valid number.")
                time.sleep(2)
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

def admin_login_as_user():
    """Admin function to login as another user"""
    global current_username, admin_mode
    
    if not admin_mode:
        print_error("This function is only available to SuperUsers.")
        return
    
    clear_terminal()
    display_banner()
    print_header("SUPERUSER - LOGIN AS USER")
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "rb") as f:
                data = decode_from_binary(f.read())
            
            if not data:
                print_warning("No users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_info("Available users:")
            print_colored("--------------------------------------------------", Fore.BLUE)
            
            users = []
            for username in data.keys():
                if username.lower() != "superuser":
                    users.append(username)
                    balance = data[username].get('balance', 0)
                    
                    # Check if user is banned
                    banned_status = ""
                    if "banned" in data[username] and data[username]["banned"] == True:
                        banned_status = " [PERMANENTLY BANNED]"
                    elif username in login_attempts and login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                        banned_status = " [TEMPORARILY BANNED]"
                    
                    # Format the number with leading zero if it's a single digit
                    formatted_number = f"{len(users):02d}" if len(users) < 10 else str(len(users))
                    
                    print_colored(f"{formatted_number}. {username} (Balance: {balance} Rs){banned_status}", 
                                 Fore.RED if banned_status else Fore.CYAN)
            
            if not users:
                print_warning("No regular users found.")
                time.sleep(2)
                show_admin_menu()
                return
            
            print_colored("--------------------------------------------------", Fore.BLUE)
            choice = input(f"\n{Fore.YELLOW}Enter user number to login as (or 0 to cancel): {Style.RESET_ALL}").strip()
            
            if choice == "0":
                show_admin_menu()
                return
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(users):
                    username = users[index]
                    
                    # Check if user is banned
                    is_banned = False
                    if "banned" in data[username] and data[username]["banned"] == True:
                        is_banned = True
                    elif username in login_attempts and login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                        is_banned = True
                    
                    if is_banned:
                        print_warning(f"User '{username}' is currently banned.")
                        confirm = input(f"{Fore.YELLOW}Do you still want to login as this user? (y/n): {Style.RESET_ALL}").lower()
                        if confirm != 'y':
                            admin_login_as_user()
                            return
                    
                    # Store the current admin status to restore later
                    previous_admin = admin_mode
                    previous_username = current_username
                    
                    # Login as the selected user
                    current_username = username
                    admin_mode = False
                    
                    print_success(f"Successfully logged in as '{username}'.")
                    print_info("You are now operating with this user's permissions and balance.")
                    print_info("Note: You can return to SuperUser mode from the main menu.")
                    time.sleep(3)
                    
                    # Show user menu
                    if not show_user_menu(username):
                        # User chose to switch accounts, restore admin status
                        admin_mode = previous_admin
                        current_username = previous_username
                        show_admin_menu()
                        return
                    
                    # If user selected download option, proceed with download
                    download_video(username)
                    
                    # After download, restore admin status
                    admin_mode = previous_admin
                    current_username = previous_username
                    show_admin_menu()
                    return
                else:
                    print_error("Invalid selection.")
                    time.sleep(2)
            except ValueError:
                print_error("Please enter a valid number.")
                time.sleep(2)
        else:
            print_warning("No user database found.")
            time.sleep(2)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        time.sleep(2)
    
    show_admin_menu()

if __name__ == "__main__":
    main()
