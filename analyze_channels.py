import os
import asyncio
import logging
import time
import signal
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, ChannelInvalidError, SessionPasswordNeededError
import threading
from dotenv import load_dotenv
from bot_utils import read_offsets, save_offsets, send_via_bot, load_keywords, bot

# Load environment variables from .env file
load_dotenv()

# Read config values from environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
SOURCE_CHANNEL_IDS = list(map(int, os.getenv("SOURCE_CHANNEL_IDS").split(',')))  # Convert to list of integers

# Define directories for logs and session files
OUTPUT_FOLDER = 'output'
LOG_FOLDER = os.path.join(OUTPUT_FOLDER, 'log')
SESSION_FILE = os.path.join(OUTPUT_FOLDER, 'telegram_user.session')

# Define log file and cleanup interval
LOG_FILE = os.path.join(LOG_FOLDER, 'analyze_channels.log')
LOG_CLEANUP_INTERVAL_DAYS = 2  # Interval to clean up the log file

# Ensure necessary directories exist
os.makedirs(LOG_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize the Telegram client
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

# Handle Ctrl+C and other termination signals
def handle_shutdown(signal_received, frame):
    logging.info("Shutdown signal received. Disconnecting client...")
    asyncio.create_task(client.disconnect())
    exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_shutdown) # Termination signal

async def authenticate_user():
    """Handles authentication for the user account without manual input."""
    await client.connect()
    
    if not await client.is_user_authorized():
        logging.info("Authorizing user account...")

        try:
            # Send the login request
            sent_code = await client.send_code_request(PHONE_NUMBER)
            
            # Automatically retrieve the code (Replace this with a more secure method)
            code = os.getenv("TELEGRAM_CODE")  # Store the login code in the .env file (if running in a known environment)
            
            if not code:
                logging.error("Login code required but not found. Please enter it manually.")
                return False
            
            await client.sign_in(PHONE_NUMBER, code)
        
        except SessionPasswordNeededError:
            password = os.getenv("TELEGRAM_PASSWORD")
            if not password:
                logging.error("Two-Step Verification enabled but no password found in environment variables.")
                return False
            await client.sign_in(password=password)
        
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            return False

    return True


async def get_entity_safe(channel_id):
    try:
        entity = await client.get_input_entity(channel_id)
        return entity
    except ChannelPrivateError:
        logging.error(f"Private channel error: You need to be a member of channel {channel_id}.")
        return None
    except ChannelInvalidError:
        logging.error(f"Invalid channel error: The channel {channel_id} is invalid or non-existent.")
        return None
    except Exception as e:
        logging.error(f"Error resolving entity for channel ID {channel_id}: {e}")
        return None

async def analyze_and_forward():
    message_count, forwarded_count = 0, 0  # Reset counters

    try:
        offsets = read_offsets()
        keywords = load_keywords()

        for source_channel_id in SOURCE_CHANNEL_IDS:
            source_entity = await get_entity_safe(source_channel_id)
            if not source_entity:
                logging.error(f"Could not resolve source channel {source_channel_id}")
                continue

            offset_id = offsets.get(str(source_channel_id), None)
            logging.info(f"Processing source channel: {source_channel_id}")

            try:
                if offset_id is None:
                    logging.info("Fetching latest messages (no offset found).")
                    messages = await client.get_messages(source_entity, limit=50)
                else:
                    logging.info(f"Fetching messages from offset {offset_id}")
                    messages = await client.get_messages(source_entity, limit=50, min_id=offset_id)

                max_offset_id = offset_id or 0
                for message in messages:
                    message_count += 1
                    if message.text and any(keyword.lower() in message.text.lower() for keyword in keywords):
                        logging.info(f"Forwarding message from channel {source_channel_id}: {message.text[:100]}...")
                        send_via_bot(message.text)
                        forwarded_count += 1

                    max_offset_id = max(max_offset_id, message.id)

                offsets[str(source_channel_id)] = max_offset_id
                save_offsets(offsets)

            except Exception as e:
                logging.error(f"[Channel ID {source_channel_id}] Error: {e}. Skipping this channel.")

    except Exception as e:
        logging.error(f"Error in analyze_and_forward: {e}. Retrying after 1 minute...")
        await asyncio.sleep(60)

def clean_up_log_file():
    if os.path.exists(LOG_FILE):
        last_modified = os.path.getmtime(LOG_FILE)
        age_days = (time.time() - last_modified) / (60 * 60 * 24)
        if age_days >= LOG_CLEANUP_INTERVAL_DAYS:
            os.remove(LOG_FILE)
            logging.info("Log file removed due to age.")

def send_daily_summary():
    summary_message = (
        "📊 Daily Summary:\n"
        "✅ Messages Processed: {}\n"
        "✅ Messages Forwarded: {}\n"
        "🚀 The bot is running smoothly!"
    )
    send_via_bot(summary_message)
    logging.info("Daily summary sent.")

def start_bot():
    while True:
        try:
            logging.info("Starting the bot...")
            bot.polling(none_stop=True, timeout=20)
        except Exception as e:
            logging.critical(f"Bot polling encountered an error: {e}")
            logging.info("Retrying bot polling after 5 minutes...")
            time.sleep(300)

async def main():
    # Authenticate user
    if not await authenticate_user():
        logging.error("Failed to authenticate. Exiting...")
        return

    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    message_started = "🚀 The bot is up and running!"
    logging.info(message_started)
    send_via_bot(message_started)

    try:
        while True:
            clean_up_log_file()
            await analyze_and_forward()

            current_time = datetime.now()
            if current_time.hour == 1 and current_time.minute == 0:
                send_daily_summary()
                await asyncio.sleep(60)

            logging.info("Waiting for 5 minutes before the next run...")
            await asyncio.sleep(300)
    except asyncio.CancelledError:
        logging.info("Shutdown requested. Disconnecting client...")
        await client.disconnect()
        logging.info("Client disconnected cleanly.")

with client:
    try:
        client.loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Manual exit requested. Disconnecting client...")
        client.loop.run_until_complete(client.disconnect())
        logging.info("Client disconnected cleanly.")