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

# File paths
DOWNLOADS_DIR = "downloads"
USER_DATA_FILE = "user_data.json"
PID_FILE = "bot.pid"

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
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
