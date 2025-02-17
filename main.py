import asyncio
import atexit
import logging
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.config import BOT_TOKEN, logger
from bot.handlers import start, broadcast, handle_youtube_link, handle_callback
from bot.utils import check_single_instance, cleanup_pid, check_ffmpeg

# Patch asyncio to allow nested event loops
nest_asyncio.apply()

async def main() -> None:
    """Start the bot"""
    try:
        logger.info("Starting bot with token prefix: %s...", BOT_TOKEN[:8] if BOT_TOKEN else "None")

        if not check_single_instance():
            logger.error("Another instance is already running")
            return

        if not check_ffmpeg():
            logger.error("FFmpeg is not properly installed")
            return

        # Register cleanup
        atexit.register(cleanup_pid)

        # Build application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))
        application.add_handler(CallbackQueryHandler(handle_callback))

        # Start polling
        logger.info("Starting polling...")
        await application.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
    finally:
        cleanup_pid()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)