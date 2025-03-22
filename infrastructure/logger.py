from config.constants import LOG_FILE, LOG_LEVEL
import logging

# Set up logging configuration
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(filename)s - Line %(lineno)d - %(message)s",
)

def get_logger(name="telegram_bot"):
    """Creates and returns a logger with console + file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Only add handlers if there are none already attached
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - Line %(lineno)d - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Create the logger instance
logger = get_logger()