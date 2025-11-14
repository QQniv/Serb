import os
from dotenv import load_dotenv

# Загружаем переменные из .env (токены и ключи)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Часовой пояс — для напоминаний и расписания
TIMEZONE = "Europe/Moscow"
