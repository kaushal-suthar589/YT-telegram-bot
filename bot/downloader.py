import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
import yt_dlp
from telegram import Message
from bot.config import YTDL_OPTS, DOWNLOADS_DIR

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = YTDL_OPTS.copy()
        if not os.path.exists(DOWNLOADS_DIR):
            os.makedirs(DOWNLOADS_DIR)

    async def update_progress(self, d: Dict[str, Any], status_message: Message) -> None:
        """Update download progress message"""
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    await status_message.edit_text(
                        f"⏬ Downloading: {percent:.1f}%\n"
                        f"💾 Size: {total/1024/1024:.1f}MB"
                    )
            except Exception as e:
                logger.error(f"Error updating progress: {e}")

    @staticmethod
    def get_format_description(format: Dict[str, Any]) -> Optional[str]:
        """Generate format description for video quality"""
        if not format.get('height'):
            return None

        height = format.get('height', 0)
        filesize = format.get('filesize', 0)
        filesize_mb = filesize / (1024 * 1024) if filesize else 0

        standard_resolutions = [144, 240, 360, 480, 720, 1080]
        closest_resolution = min(standard_resolutions, key=lambda x: abs(x - height))

        has_video = format.get('vcodec') != 'none'

        if not has_video:
            return None

        if filesize:
            size_text = f"{filesize_mb:.1f}MB"
            if filesize_mb > 1000:
                size_text += " ⚠️"
            return f"{closest_resolution}p ({size_text})"
        else:
            return f"{closest_resolution}p"

    def extract_video_info(self, url: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extract video information and available formats"""
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                return formats, info
            except Exception as e:
                logger.error(f"Format extraction error: {e}")
                raise

    def group_formats_by_quality(self, formats: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """Group video formats by quality"""
        quality_groups: Dict[int, Optional[Dict[str, Any]]] = {
            1080: None,
            720: None,
            480: None,
            360: None,
            240: None,
            144: None
        }

        for format in formats:
            if format.get('vcodec') != 'none':
                height = format.get('height', 0)
                standard_resolutions = [1080, 720, 480, 360, 240, 144]
                closest_resolution = min(standard_resolutions, key=lambda x: abs(x - height))

                desc = self.get_format_description(format)
                if desc:
                    if not quality_groups[closest_resolution] or \
                       (format.get('tbr', 0) > quality_groups[closest_resolution]['format'].get('tbr', 0)):
                        quality_groups[closest_resolution] = {
                            'format': format,
                            'description': desc
                        }

        return quality_groups

    async def download_video(self, url: str, format_id: str, status_message: Message) -> str:
        """Download video with selected format"""
        download_opts = self.ydl_opts.copy()
        download_opts['format'] = f'{format_id}+bestaudio[ext=m4a]/best'
        download_opts['outtmpl'] = os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s')
        download_opts['progress_hooks'] = [
            lambda d: asyncio.create_task(self.update_progress(d, status_message))
        ]

        with yt_dlp.YoutubeDL(download_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)