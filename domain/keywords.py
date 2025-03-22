from config.constants import KEYWORDS_FILE
from infrastructure.logger import logger

def load_keywords():
    """Load keywords from file."""
    try:
        with open(KEYWORDS_FILE, 'r') as file:
            keywords = [line.strip().lower() for line in file.readlines()]
            logger.info(f"Keywords loaded: {keywords}")
            return keywords
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Error loading keywords: {e}")
        return []

def save_keywords(keywords):
    """Save keywords to file."""
    try:
        with open(KEYWORDS_FILE, 'w') as file:
            for keyword in keywords:
                file.write(f"{keyword}\n")
        logger.info(f"Keywords saved: {keywords}")
    except Exception as e:
        logger.error(f"Error saving keywords: {e}")
