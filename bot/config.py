import os
import logging

# Bot Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# Channel Configuration
REQUIRED_CHANNELS = [
    "YouTube_Downloder95",
    "bot_Creator95"
]

# Admin Configuration
ADMIN_IDS = [7847143133]

# File paths - Using absolute paths for persistence
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
USER_DATA_FILE = os.path.join(BASE_DIR, "user_data.json")
PID_FILE = os.path.join(BASE_DIR, "bot.pid")
LOG_FILE = os.path.join(BASE_DIR, "bot.log")

# Create necessary directories
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# YT-DLP Configuration
YTDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'format': 'best',
    'merge_output_format': 'mp4',
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
    'verbose': True
}

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Set higher file size limits for downloads (2GB)
MAX_DOWNLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2GB in bytes