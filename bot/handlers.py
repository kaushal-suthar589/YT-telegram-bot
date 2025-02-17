from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import os
from bot.config import ADMIN_IDS, REQUIRED_CHANNELS
from bot.utils import track_user, load_user_data
from bot.downloader import VideoDownloader

logger = logging.getLogger(__name__)
downloader = VideoDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    logger.info("Start command received")

    try:
        if not update.message:
            logger.error("No message in update")
            return

        user = update.message.from_user
        if not user:
            logger.error("No user in message")
            return

        logger.info(f"Processing start command for user {user.id}")
        track_user(user.id, user.username or "", user.first_name)

        welcome_msg = (
            f"👋 नमस्ते {user.first_name} YouTube वीडियो डाउनलोड बॉट में आपका स्वागत है 🫶\n\n"
            "⏩ पहले दिए गए चैनल्स को join करें और फिर आप कोई भी वीडियो डाउनलोड कर सकते हैं 📷"
        )

        keyboard = [
            [InlineKeyboardButton("Join", url=f"https://t.me/{channel}") for channel in REQUIRED_CHANNELS],
            [InlineKeyboardButton("Joined ✅", callback_data="joined")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.info(f"Sending welcome message to user {user.id}")
        sent_message = await update.message.reply_text(welcome_msg, reply_markup=reply_markup)
        logger.info(f"Welcome message sent successfully to user {user.id}")

    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        if update and update.message:
            await update.message.reply_text("कृपया थोड़ी देर बाद फिर से कोशिश करें।")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in update")
            return

        logger.info(f"Handling callback query with data: {query.data}")
        await query.answer()

        if query.data == "joined":
            await query.message.edit_text(
                "अब आप कोई भी YouTube वीडियो लिंक भेज सकते हैं।\n"
                "मैं इसे डाउनलोड करके आपको भेज दूंगा। 📥"
            )
            logger.info(f"User {query.from_user.id} completed joining process")

    except Exception as e:
        logger.error(f"Error in handle_callback: {e}", exc_info=True)

async def check_member(bot, user_id: int, channel: str) -> bool:
    """Check if user is member of required channel"""
    try:
        member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle broadcast command for admins"""
    if not update.message:
        return

    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        broadcast_message = ' '.join(context.args)
        if not broadcast_message:
            await update.message.reply_text(
                "Please provide a message to broadcast.\n"
                "Usage: /broadcast <message>"
            )
            return

        user_data = load_user_data()
        success_count = 0
        fail_count = 0

        for user in user_data['users']:
            try:
                await context.bot.send_message(
                    chat_id=user['id'],
                    text=broadcast_message
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user['id']}: {e}")
                fail_count += 1

        await update.message.reply_text(
            f"Broadcast completed!\n"
            f"✅ Successfully sent: {success_count}\n"
            f"❌ Failed: {fail_count}"
        )

    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await update.message.reply_text(f"Error during broadcast: {str(e)}")

async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle YouTube video links"""
    if not update.message:
        return

    message = update.message.text

    if 'youtube.com' not in message and 'youtu.be' not in message:
        await update.message.reply_text('Please provide a valid YouTube link')
        return

    user_id = update.message.from_user.id
    for channel in REQUIRED_CHANNELS:
        if not await check_member(context.bot, user_id, channel):
            keyboard = [
                [InlineKeyboardButton("Join", url=f"https://t.me/{channel}")]
                for channel in REQUIRED_CHANNELS
            ]
            keyboard.append([InlineKeyboardButton("Joined ✅", callback_data="joined")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "❌ Join the required channels first",
                reply_markup=reply_markup
            )
            return

    status_message = await update.message.reply_text('⌛ Fetching video information...')

    try:
        formats, info = downloader.extract_video_info(message)
        quality_groups = downloader.group_formats_by_quality(formats)

        keyboard = []
        for height, data in quality_groups.items():
            if data:
                keyboard.append([InlineKeyboardButton(
                    f"📺 {data['description']}",
                    callback_data=f"format_{message}_{data['format']['format_id']}"
                )])

        if not keyboard:
            await status_message.edit_text(
                'Sorry, no available quality options found for this video.\n'
                'Please try another link.'
            )
            return

        reply_markup = InlineKeyboardMarkup(keyboard)
        await status_message.edit_text(
            f'Title: {info.get("title")}\n\n'
            'Select video quality:\n'
            '(Available quality: 144p to 1080p)\n'
            '⚠️ = File size larger than 1000MB',
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error in handle_youtube_link: {str(e)}")
        await status_message.edit_text(
            'Error getting video information.\n'
            'Please try another link or try again later.'
        )
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboard buttons"""
    if not update.callback_query:
        return

    query = update.callback_query
    await query.answer()

    if query.data == "joined":
        # Check if user has actually joined all channels
        for channel in REQUIRED_CHANNELS:
            if not await check_member(context.bot, query.from_user.id, channel):
                await query.message.reply_text(
                    "❌ Please join all required channels first!"
                )
                return

        await query.message.reply_text(
            "✅ Thank you for joining! You can now send YouTube links to download videos."
        )
        return

    if query.data.startswith("format_"):
        try:
            _, url, format_id = query.data.split("_")
            status_msg = await query.message.reply_text("⬇️ Downloading video...")
            
            video_path = await downloader.download_video(url, format_id)
            if not video_path:
                await status_msg.edit_text("❌ Failed to download video")
                return

            await status_msg.edit_text("📤 Uploading to Telegram...")
            with open(video_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    caption="✅ Downloaded using @YourBotUsername"
                )
            await status_msg.delete()
            
            # Cleanup
            if os.path.exists(video_path):
                os.remove(video_path)

        except Exception as e:
            logger.error(f"Error in handle_callback: {e}")
            await query.message.reply_text("❌ Error processing your request")
