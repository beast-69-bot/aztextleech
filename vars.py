import os
from dotenv import load_dotenv

load_dotenv()

API_ID_ENV = os.environ.get("API_ID", "34894897")
API_ID = int(API_ID_ENV) if API_ID_ENV else 25793090

API_HASH  = os.environ.get("API_HASH", "c17393d2c160bf3305b366747bcdb7e3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8572066127:AAE5HemuYGuqkNFHpk1elO4B6DT1l7xi9vo") 

WEBHOOK = False  # True only on VPS/Heroku
PORT = int(os.environ.get("PORT", 8080))
