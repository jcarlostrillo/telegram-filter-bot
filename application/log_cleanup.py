import os
from infrastructure.logger import logger
import time
from config.constants import LOG_FILE, LOG_CLEANUP_INTERVAL_DAYS

def clean_up_log_file():
    """Deletes log file if older than specified interval."""
    if os.path.exists(LOG_FILE):
        age_days = (time.time() - os.path.getmtime(LOG_FILE)) / (60 * 60 * 24)
        if age_days >= LOG_CLEANUP_INTERVAL_DAYS:
            os.remove(LOG_FILE)
            logger.info("Old log file removed.")
