from config.constants import KEYWORDS_FILE

from infrastructure.logger import logger

# Function to load keywords
def load_keywords():
    try:
        with open(KEYWORDS_FILE, 'r') as file:
            keywords = [line.strip().lower() for line in file.readlines()]
            logger.info(f"Keywords loaded: {keywords}")
            return keywords
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Error loading keywords: {e}")
        return []
