from os import getenv
from dotenv import load_dotenv

load_dotenv(".env")

BOT_TOKEN = getenv("BOT_TOKEN")
BOT_PREFIX = getenv("BOT_PREFIX")
