import os
from dotenv import load_dotenv

load_dotenv()

# Use environment variables for security. Do not hardcode secrets here.
API_ID_ENV = os.environ.get("API_ID")
API_ID = int(API_ID_ENV) if API_ID_ENV else None

API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN") 

WEBHOOK = os.environ.get("WEBHOOK", "False").lower() == "true"
PORT = int(os.environ.get("PORT", 8080))
