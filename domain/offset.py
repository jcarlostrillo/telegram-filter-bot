import json
import os

CONFIG_FOLDER = 'config'
OFFSET_FILE = os.path.join(CONFIG_FOLDER, 'offset.json')

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
