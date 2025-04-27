import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()  # Default to INFO if not set

API_ID = int(os.getenv("API_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
SOURCE_CHANNEL_IDS = list(map(int, os.getenv("SOURCE_CHANNEL_IDS").split(',')))
DESTINATION_CHANNEL_ID = -4644186100

OUTPUT_FOLDER = '/shared/telegram-filter-bot/output'
LOG_FOLDER = os.path.join(OUTPUT_FOLDER, 'log')
SESSION_FILE = os.path.join(OUTPUT_FOLDER, 'telegram_user.session')

LOG_FILE = os.path.join(LOG_FOLDER, 'analyze_channels.log')
LOG_CLEANUP_INTERVAL_DAYS = 2  # Days before log cleanup

CONFIG_FOLDER = 'config'
KEYWORDS_FILE = os.path.join(CONFIG_FOLDER, 'keywords.txt')
