#!/bin/sh

# Activate the Python virtual environment
source /shared/telegram-filter-bot/venv/bin/activate

# Change to the directory where the script is located
cd /shared/telegram-filter-bot

# Start the Python script in the background
python /shared/telegram-filter-bot/analyze_channels.py &
