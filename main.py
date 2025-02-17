import asyncio
import atexit
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, Update
from bot.config import BOT_TOKEN, logger
from bot.handlers import start, broadcast, handle_youtube_link
from bot.utils import check_single_instance, cleanup_pid, check_ffmpeg

async def main() -> None:
    """Start the bot"""
    if not check_single_instance():
        return

    if not check_ffmpeg():
        logger.error("FFmpeg is not properly installed. Video processing may fail.")
        return

    # Register cleanup
    atexit.register(cleanup_pid)

    # Initialize bot with proper error handling
    try:
        # Build the application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))

        # Start bot
        logger.info("Starting bot application...")
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        cleanup_pid()
        return

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        cleanup_pid()