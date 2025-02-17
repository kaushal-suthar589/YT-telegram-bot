import asyncio
import atexit
import logging
import time
import signal
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bot.config import BOT_TOKEN, logger
from bot.handlers import start, broadcast, handle_youtube_link, handle_callback
from bot.utils import check_single_instance, cleanup_pid, check_ffmpeg

# Patch asyncio to allow nested event loops
nest_asyncio.apply()

# Flag to control the bot's running state
running = True

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global running
    logger.info(f"Received signal {signum}")
    running = False

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
        await application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
    finally:
        cleanup_pid()

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    retry_count = 0
    max_retries = 3
    retry_delay = 10

    while running:
        try:
            asyncio.run(main())
            if not running:  # Clean exit
                break
            retry_count = 0  # Reset counter on successful run
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Fatal error (attempt {retry_count}/{max_retries}): {e}", exc_info=True)

            if retry_count >= max_retries:
                logger.critical(f"Maximum retry attempts ({max_retries}) reached. Restarting fresh...")
                retry_count = 0
                time.sleep(30)  # Longer delay before fresh start
            else:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)