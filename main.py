import logging
import asyncio
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.config import Config
from bot.handlers import router
from bot.storage import cleanup_old_posts

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler()


async def auto_cleanup_task():
    while True:
        cleanup_old_posts()
        await asyncio.sleep(24 * 60 * 60)  # 24 часа


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)  # Пропускаем старые сообщения

    scheduler.start()  # <-- Запуск планировщика

    asyncio.create_task(auto_cleanup_task())  # Запуск фоновой задачи
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
