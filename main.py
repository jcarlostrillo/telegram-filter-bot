import os
import logging
import asyncio
import signal
import sys
from datetime import datetime
from infrastructure.logger import logger  # Assuming this imports the configured logger
from infrastructure.telegram_client import client, authenticate
from application.message_processor import analyze_and_forward
from application.log_cleanup import clean_up_log_file
from domain.services import send_daily_summary
import pytz

timezone = pytz.timezone("Europe/Madrid")

# Ensure the log file and directory exist
from config.constants import LOG_FILE

log_dir = os.path.dirname(LOG_FILE)
os.makedirs(log_dir, exist_ok=True)

print(f"Log file path: {LOG_FILE}")


# Set up logging configuration to ensure it writes to the file
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,  # Use DEBUG to capture all logs
    format='%(asctime)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Get logger
logger = logging.getLogger("telegram_bot")

# Example shutdown handler
def handle_shutdown(sig, frame):
    logger.info("Shutdown signal received. Cancelling all tasks...")
    loop = asyncio.get_event_loop()
    tasks = asyncio.all_tasks(loop)
    for task in tasks:
        task.cancel()
    logger.info("All tasks cancelled. Stopping event loop...")
    loop.stop()
    logger.info("Event loop stopped. Exiting...")
    sys.exit(0)

async def start_bot():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _poll_bot)

def _poll_bot():
    while True:
        try:
            logger.info("Starting the bot from main...")
            bot.polling(none_stop=True, timeout=20)
        except Exception as e:
            logger.error(f"Bot polling encountered an unexpected error: {e}")
            logger.info("Retrying bot polling in 30 seconds...")
            time.sleep(30)

async def main():
    logger.info("Inside main function...")
    if not await authenticate():
        logger.error("Failed authentication. Exiting...")
        return

    asyncio.create_task(start_bot())  # Start bot polling as a background task

    last_sent_date = None

    while True:
        try:
            if not client.is_connected():
                logger.warning("Client disconnected. Reconnecting...")
                await client.connect()
                if not client.is_user_authorized():
                    await authenticate()

            clean_up_log_file()
            await analyze_and_forward()

            now = datetime.now(timezone)
            today = date.today()

            if now.hour == 1 and now.minute == 0 and last_sent_date != today:
                await send_daily_summary()
                last_sent_date = today  # Mark as sent for today
                logger.info("Daily summary sent.")

            logger.debug("Sleeping for 5 minutes...")
            await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            await asyncio.sleep(60)  # Short wait before retrying

if __name__ == "__main__":
    logger.info("Starting the event loop...")
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    with client:
        try:
            logger.info("Running client loop...")
            client.loop.run_until_complete(main())
        except (KeyboardInterrupt, SystemExit):
            logger.info("Manual exit. Disconnecting client...")
            client.loop.run_until_complete(client.disconnect())
            logger.info("Client disconnected cleanly.")
