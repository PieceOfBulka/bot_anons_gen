import os
from dotenv import load_dotenv

# загрузка переменных из окружения
load_dotenv()


class Config:
    # токен тг бота
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    # токен модели LLM
    LLM_TOKEN = os.getenv("LLM_TOKEN")
    API_KEY = os.getenv("API_KEY")
    # id канала для автопостинга
    CHAT_ID = os.getenv("CHAT_ID")
    # api телеграм парсер
    API_HASH = os.getenv("API_HASH")
    TG_API_ID = os.getenv("TG_API_ID")
