from infrastructure.logger import logger
from config.constants import API_ID, API_HASH, PHONE_NUMBER, SESSION_FILE, DESTINATION_CHANNEL_ID
import os
import telebot
from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError, ChannelInvalidError, SessionPasswordNeededError
)
from infrastructure.bot import bot

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def authenticate():
    """Handles authentication for the user account."""
    await client.connect()
    
    if not await client.is_user_authorized():
        logger.info("Authorizing user account...")
        try:
            code = os.getenv("TELEGRAM_CODE")  # Fetch login code from .env
            if not code:
                logger.error("Login code required but missing.")
                return False
            await client.sign_in(PHONE_NUMBER, code)
        except SessionPasswordNeededError:
            password = os.getenv("TELEGRAM_PASSWORD")
            if not password:
                logger.error("Two-Step Verification password missing.")
                return False
            await client.sign_in(password=password)
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    return True

async def get_entity_safe(channel_id):
    """Retrieve a Telegram entity safely."""
    try:
        return await client.get_input_entity(channel_id)
    except (ChannelPrivateError, ChannelInvalidError) as e:
        logger.error(f"Error accessing channel {channel_id}: {e}")
        return None

# Function to send messages via the bot
def send_via_bot(message_text):
    try:
        logger.info("Before send message bot")
        bot.send_message(chat_id=DESTINATION_CHANNEL_ID, text=message_text, parse_mode='HTML') # or 'Markdown'
        logger.info("Message sent successfully via bot.")
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Error sending message via bot: {e}")
        logger.error(f"Failed message text: {message_text}") #log the message
    except Exception as e:
        logger.error(f"An unexpected error occurred in send_via_bot: {e}")
