from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from dotenv import load_dotenv
import os


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Отправь мне любое сообщение, и я преобразую его.\n"
        "Попробуй отправить текст, и ты увидишь магию!"
    )


async def transform_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ответа бота"""
    user_message = update.message.text
    user = update.effective_user

    transformed_text = (
        f"🔹 Ваше оригинальное сообщение:\n{user_message}\n\n"
        f"🔹 Длина сообщения: {len(user_message)} символов\n"
        f"🔹 Первые 5 символов: '{user_message[:5]}...'\n"
        f"🔹 Сообщение заглавными буквами:\n{user_message.upper()}\n\n"
        f"Спасибо, {user.first_name}, за ваше сообщение! 😊"
    )

    await update.message.reply_text(transformed_text)


if __name__=="__main__":
    # загрузка переменных окружения
    load_dotenv()
    BOT_TOKEN=os.getenv("BOT_TOKEN")

    # создаем бота и регистрируем обработчики
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, transform_message))

    print("Бот запущен...")
    app.run_polling()