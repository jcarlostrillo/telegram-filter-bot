import telebot
from infrastructure.logger import logger
from domain.keywords import load_keywords, save_keywords
from config.constants import BOT_TOKEN, DESTINATION_CHANNEL_ID

bot = telebot.TeleBot(BOT_TOKEN)

def send_via_bot(message_text):
    """Send messages via Telegram bot."""
    try:
        logger.info("Before send message bot")
        bot.send_message(chat_id=DESTINATION_CHANNEL_ID, text=message_text, parse_mode='HTML')
        logger.info("Message sent successfully via bot.")
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Error sending message via bot: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in send_via_bot: {e}")

@bot.message_handler(commands=['view_keywords'])
def view_keywords(message):
    """Send the list of keywords."""
    keywords = load_keywords()
    response = "📌 Current Keywords:\n" + "\n".join(f"- {keyword}" for keyword in keywords) if keywords else "No keywords found."
    bot.reply_to(message, response)

@bot.message_handler(commands=['add_keyword'])
def add_keyword(message):
    """Add a new keyword."""
    user_input = message.text.split(' ', 1)
    if len(user_input) < 2:
        bot.reply_to(message, "Usage: /add_keyword keyword")
        return
    keyword = user_input[1].strip().lower()
    keywords = load_keywords()
    if keyword in keywords:
        bot.reply_to(message, f"The keyword '{keyword}' already exists.")
    else:
        keywords.append(keyword)
        save_keywords(keywords)
        bot.reply_to(message, f"Keyword '{keyword}' added.")

def start_bot():
    """Start bot polling."""
    logger.info("Starting the bot...")
    bot.polling(none_stop=True)
