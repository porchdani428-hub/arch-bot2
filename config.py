import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

ARCHITECT_NAME = os.getenv('ARCHITECT_NAME', 'MK ARCHVIZ').strip()
ARCHITECT_HANDLE = os.getenv('ARCHITECT_HANDLE', '@MK.ARCHVIZ').strip()

# GPT Image 2.5 Flare / OpenAI Image API
IMAGE_API_KEY = os.getenv('IMAGE_API_KEY', '').strip()
IMAGE_BASE_URL = os.getenv('IMAGE_BASE_URL', '').strip() or None
IMAGE_MODEL = os.getenv('IMAGE_MODEL', 'gpt-image-2.5-flare').strip()
