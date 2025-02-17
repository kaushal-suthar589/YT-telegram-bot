import asyncio
import atexit
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.config import BOT_TOKEN, logger
from bot.handlers import start, broadcast, handle_youtube_link
from bot.utils import check_single_instance, cleanup_pid, check_ffmpeg

async def handle_callback(update, context):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()

    if query.data == "joined":
        await query.message.edit_text(
            "Now you can send any YouTube video link.\n"
            "I will download and send it to you. 📥"
        )

async def main() -> None:
    """Start the bot"""
    logger.info("Starting bot...")

    if not check_single_instance():
        logger.error("Another instance is already running")
        return

    if not check_ffmpeg():
        logger.error("FFmpeg is not properly installed")
        return

    # Register cleanup
    atexit.register(cleanup_pid)

    try:
        # Build and configure the application
        logger.info("Building application...")
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        logger.info("Adding handlers...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))
        application.add_handler(CallbackQueryHandler(handle_callback))

        # Start the bot
        logger.info("Starting polling...")
        await application.initialize()
        await application.start()
        await application.run_polling()

    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
        cleanup_pid()
    finally:
        logger.info("Shutting down...")
        cleanup_pid()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        cleanup_pid()