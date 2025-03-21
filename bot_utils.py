import json
import logging
import telebot
import os
import psutil
from datetime import datetime, timedelta
from time import sleep


# Define directories for configuration
CONFIG_FOLDER = 'config'
OUTPUT_FOLDER = 'output'

LOG_FOLDER = os.path.join(OUTPUT_FOLDER, 'log')
LOG_FILE_ANALYZE_CHANNELS = os.path.join(LOG_FOLDER, 'analyze_channels.log')

OFFSET_FILE = os.path.join(CONFIG_FOLDER, 'offset.json')
KEYWORDS_FILE = os.path.join(CONFIG_FOLDER, 'keywords.txt')
os.makedirs(CONFIG_FOLDER, exist_ok=True)

# Initialize the bot
BOT_TOKEN = '8008042594:AAHi9AgtbO_wIOXeZJc_Cy5gmUMo8ANo7u4'
bot = telebot.TeleBot(BOT_TOKEN)

DESTINATION_CHANNEL_ID = -4644186100

# Function to read the last offset_id for each channel from the JSON file
def read_offsets():
    try:
        with open(OFFSET_FILE, 'r') as file:
            return json.load(file)  # Load the JSON content
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # If no file or invalid JSON, return an empty dictionary

# Function to save the offset data to the JSON file
def save_offsets(offsets):
    with open(OFFSET_FILE, 'w') as file:
        json.dump(offsets, file, indent=4)

# Ensure keywords file exists as an empty list
if not os.path.exists(KEYWORDS_FILE):
    with open(KEYWORDS_FILE, 'w') as file:
        json.dump([], file, indent=4)

# Function to load keywords
def load_keywords():
    try:
        with open(KEYWORDS_FILE, 'r') as file:
            keywords = [line.strip().lower() for line in file.readlines()]
            logging.info(f"Keywords loaded: {keywords}")
            return keywords
    except (FileNotFoundError, IOError) as e:
        logging.error(f"Error loading keywords: {e}")
        return []

# Function to save keywords
def save_keywords(keywords):
    try:
        with open(KEYWORDS_FILE, 'w') as file:
            for keyword in keywords:
                file.write(f"{keyword}\n")
        logging.info(f"Keywords saved: {keywords}")
    except Exception as e:
        logging.error(f"Error saving keywords: {e}")

# Function to send messages via the bot
def send_via_bot(message_text):
    try:
        logging.info("Before send message bot")
        bot.send_message(chat_id=DESTINATION_CHANNEL_ID, text=message_text, parse_mode='HTML') # or 'Markdown'
        logging.info("Message sent successfully via bot.")
    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Error sending message via bot: {e}")
        logging.error(f"Failed message text: {message_text}") #log the message
    except Exception as e:
        logging.error(f"An unexpected error occurred in send_via_bot: {e}")

# Function to check if the script is running
def is_script_running(script_name):
    for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            if script_name in ' '.join(process.info['cmdline']):
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False

# Function to check for errors in the log file
def get_recent_errors(hours=10):
    try:
        with open(LOG_FILE_ANALYZE_CHANNELS, 'r') as file:
            lines = file.readlines()
            errors = []
            now = datetime.now()
            cutoff_time = now - timedelta(hours=hours)

            # Read lines in reverse order to process recent entries first
            for line in reversed(lines):
                try:
                    if ("ERROR" in line) or ("CRITICAL" in line):
                        timestamp_str = line.split(" - ")[0]
                        log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                        if log_time >= cutoff_time:
                            # Format the error line with a prefix
                            formatted_line = f"⚠️ {line.strip()}" 
                            errors.append(formatted_line)
                            if len(errors) >= 5:  # Limit to 5 recent errors
                                break
                except (IndexError):
                    continue
            return errors
    except FileNotFoundError:
        return None

# ++++++++++++++++ HANDLERS ++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++

# Command to check if analyze_channels.py is running
@bot.message_handler(commands=['check_status'])
def check_status(message):
    script_name = "analyze_channels.py"
    script_status_response = f"✅  The script *{script_name}* is currently running." if is_script_running(script_name) else f"❌  The script *{script_name}* is NOT running."

    error_lines = get_recent_errors(hours=10)
    errors_response = ""

    if error_lines is None:
        errors_response = "❌ Log file not found."
    elif error_lines:
        max_error_lines = 5
        error_subset = error_lines[:max_error_lines]
        errors_response = (
            f"⚠️ Recent Errors in the Log File (showing first {max_error_lines} lines):\n\n"
            + "\n".join(error_subset)
        )
        if len(error_lines) > max_error_lines:
            errors_response += "\n... (truncated)"
    else:
        errors_response = "✅ No errors found in the log file in the last 10 hours."

    # Combine script status and errors response into a single message
    response = script_status_response + "\n\n" + errors_response

    # Telegram message limit is 4096 characters, so split if necessary
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            bot.reply_to(message, response[i:i + 4096], parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, response, parse_mode='MarkdownV2')


# Command to view current keywords
@bot.message_handler(commands=['view_keywords'])
def view_keywords(message):
    keywords = load_keywords()
    if keywords:
        response = "📌 Current Keywords:\n" + "\n".join(f"- {keyword}" for keyword in keywords)
    else:
        response = "No keywords have been added yet. Use /add_keyword to add a new keyword."
    bot.reply_to(message, response)

# Command to add a new keyword
@bot.message_handler(commands=['add_keyword'])
def add_keyword(message):
    user_input = message.text.split(' ', 1)
    if len(user_input) < 2 or not user_input[1].strip():
        bot.reply_to(message, "Please provide a keyword to add. Example: /add_keyword xiaomi")
        return

    new_keyword = user_input[1].strip().lower()
    keywords = load_keywords()
    if new_keyword in keywords:
        bot.reply_to(message, f"The keyword '{new_keyword}' already exists.")
    else:
        keywords.append(new_keyword)
        save_keywords(keywords)
        bot.reply_to(message, f"Keyword '{new_keyword}' has been added.")

# Command to remove an existing keyword
@bot.message_handler(commands=['remove_keyword'])
def remove_keyword(message):
    user_input = message.text.split(' ', 1)
    if len(user_input) < 2 or not user_input[1].strip():
        bot.reply_to(message, "Please provide a keyword to remove. Example: /remove_keyword xiaomi")
        return

    keyword_to_remove = user_input[1].strip().lower()
    keywords = load_keywords()
    if keyword_to_remove in keywords:
        keywords.remove(keyword_to_remove)
        save_keywords(keywords)
        bot.reply_to(message, f"Keyword '{keyword_to_remove}' has been removed.")
    else:
        bot.reply_to(message, f"The keyword '{keyword_to_remove}' does not exist.")

# Command to reset all keywords
@bot.message_handler(commands=['reset_keywords'])
def reset_keywords(message):
    save_keywords([])
    bot.reply_to(message, "All keywords have been reset. The list is now empty.")
