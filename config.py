import os

# Determine project root (adjust if using complex folder structures)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the .env file
ENV_PATH = os.path.join(BASE_DIR, 'CorrectKeyboard', '.env')
