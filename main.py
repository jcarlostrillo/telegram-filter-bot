from datetime import datetime
from infrastructure.logger import logger
import time
import asyncio
import signal
import threading
from infrastructure.telegram_client import client, authenticate
from application.message_processor import analyze_and_forward
from application.log_cleanup import clean_up_log_file
from domain.services import send_daily_summary
from infrastructure.bot import bot

def handle_shutdown(signal_received, frame):
    """Handles shutdown."""
    logger.info("Shutdown signal received. Disconnecting client...")
    asyncio.create_task(client.disconnect())
    exit(0)

def start_bot():
    while True:
        try:
            logger.info("Starting the bot...")
            bot.polling(none_stop=True, timeout=20)
        except Exception as e:
            logger.critical(f"Bot polling encountered an error: {e}")
            logger.info("Retrying bot polling after 5 minutes...")
            time.sleep(300)

async def main():
    if not await authenticate():
        logger.error("Failed authentication. Exiting...")
        return

    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    while True:
        clean_up_log_file()
        await analyze_and_forward()

        # Send summary at 1:00 AM
        if datetime.now().hour == 1 and datetime.now().minute == 0:
            send_daily_summary()

        logger.info("Sleeping for 5 minutes...")
        await asyncio.sleep(300)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    with client:
        try:
            client.loop.run_until_complete(main())
        except (KeyboardInterrupt, SystemExit):
            logger.info("Manual exit. Disconnecting client...")
            client.loop.run_until_complete(client.disconnect())
            logger.info("Client disconnected cleanly.")
