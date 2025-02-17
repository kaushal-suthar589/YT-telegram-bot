import os
import json
import time
import logging
import subprocess
from functools import lru_cache
from typing import Dict, Any
from bot.config import USER_DATA_FILE, PID_FILE, logger

def check_single_instance() -> bool:
    """Ensure only one instance of the bot is running"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                try:
                    old_pid = int(f.read().strip())
                    try:
                        os.kill(old_pid, 0)
                        logger.error(f"Bot is already running with PID {old_pid}")
                        return False
                    except OSError:
                        os.remove(PID_FILE)
                except ValueError:
                    os.remove(PID_FILE)

        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        logger.error(f"Error in check_single_instance: {e}")
        return False

def cleanup_pid() -> None:
    """Remove PID file on exit"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                if pid == os.getpid():
                    os.remove(PID_FILE)
                    logger.info("Cleaned up PID file")
    except Exception as e:
        logger.error(f"Error cleaning up PID file: {e}")

def load_user_data() -> Dict[str, Any]:
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        return {'users': []}
    except Exception as e:
        logger.error(f"Error loading user data: {e}")
        return {'users': []}

def save_user_data(data: Dict[str, Any]) -> None:
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

def track_user(user_id: int, username: str, first_name: str) -> None:
    user_data = load_user_data()
    if user_id not in [u['id'] for u in user_data['users']]:
        user_data['users'].append({
            'id': user_id,
            'username': username,
            'first_name': first_name,
            'joined_date': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        save_user_data(user_data)

def check_ffmpeg() -> bool:
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("FFmpeg is installed and accessible")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"FFmpeg check failed: {e}")
        return False

@lru_cache(maxsize=100)
def get_video_filesize(filepath: str) -> float:
    """Get video file size in MB"""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error getting file size: {e}")
        return 0.0
