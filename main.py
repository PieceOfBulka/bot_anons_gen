import logging
import asyncio
from aiogram import Bot, Dispatcher
from bot.config import Config
from bot.handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)  # Пропускаем старые сообщения

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
