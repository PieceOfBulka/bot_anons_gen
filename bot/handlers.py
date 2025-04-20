import asyncio
import json

from aiogram import Router, F, Bot, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ChatAction
from bot.services import llama_reply, openrouter_reply
from bot.parser import web_parser, telegram_parser
from bot.storage import download_posts, upload_posts, update_post, add_post, schedule_posts
from bot.config import Config
from datetime import datetime, timedelta

router = Router()

choice_waiters={}
user_step = {}

# ───────────── Команды ─────────────

@router.message(Command("start"))
async def handle_start(message: Message):
    """ Обработчик команды /start"""
    await message.answer("Этот бот предназначен для генерации, хранения и управления постами.\nДля работы напишите команду /menu")


@router.message(Command("menu"))
async def start_menu(message: Message, bot: Bot):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Сгенерировать пост", callback_data="new")],
        [InlineKeyboardButton(text="📋 Мои посты", callback_data="view")]
    ])

    await message.answer("Выберите действие:", reply_markup=keyboard)


# ───────────── Сообщения ─────────────


@router.message()
async def handle_message(message: Message, bot: Bot):
    if user_step=={}:
        await message.reply("Выберите действие через /menu")
        return

    user_id=message.from_user.id
    data = user_step.get(user_id)

    if data["step"] == "awaiting_link":
        await generate_post(message, bot)
        await message.answer("Напишите ID для поста, уникально отображающий его информацию")

    elif data["step"] == "awaiting_post_id":
        post_id = message.text.strip()

        user_step[user_id]["step"] = "awaiting_time"
        user_step[user_id]["post_id"] = post_id

        add_post(post_id=post_id, text=user_step[user_id]["text"],
                 post_type=user_step[user_id]["post_type"], source=user_step[user_id]["source"])

        await message.answer("Напишите дату публикации в формате Год-Месяц-День часы:минуты")

    elif isinstance(data, dict) and data["step"] == "awaiting_time":
        scheduled_time = message.text.strip()
        try:
            scheduled_time = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M")
        except ValueError:
            await message.reply("Неверный формат времени. Попробуй ещё раз.")
            return

        update_post(post_id=user_step[user_id]["post_id"], scheduled_time=scheduled_time)
        user_step[user_id]["step"]="editing"
        await message.answer(f"✅ Пост **{user_step[user_id]['post_id']}** полностью сохранён")

        # логика для моментального editing
        try:
            momentum_editing = await handle_momentum_edit_choice(message, bot)
        except asyncio.TimeoutError:
            await message.reply("⏳ Время на выбор истекло.")
            return
        if momentum_editing=="yes":
            user_step[user_id]["step"]="momentum_editing"
            await message.answer("Пришлите исправленный вариант поста")
        else:
            user_step.pop(user_id)
            await message.answer("🎉Поздравляю с созданием нового поста!🎉\nДля новых действий вызовите /menu")

    elif isinstance(data, dict) and user_step[user_id]["step"] == "momentum_editing":
        try:
            await post_edit(post_id=user_step[user_id]["post_id"], new_text=message.text)
            await message.answer(f"Пост **{user_step[user_id]['post_id']}** успешно обновлен!")
            user_step.pop(user_id)
        except Exception as e:
            await message.reply(f"Произошла ошибка при обновлении: {e} \nПопробуйте редактировать через меню")

    elif data["step"] == "post_editing":
        await post_edit(post_id=user_step[user_id]["post_id"], new_text=message.text)
        await message.answer(f"✅ Пост **{user_step[user_id]['post_id']}** успешно обновлен")
        user_step.pop(user_id)

    elif data["step"] == "time_editing":
        try:
            date = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
            update_post(post_id=user_step[user_id]["post_id"], scheduled_time=date)
            await message.answer(f"✅ Пост **{user_step[user_id]['post_id']}** успешно обновлен")
            user_step.pop(user_id)
        except ValueError:
            await message.answer("❌ Неверный формат даты. Пример: `2025-04-15 14:30`")
            return

    else:
        await message.reply("Что-то пошло не так. Попробуйте запустить /menu заново")
        user_step.pop(user_id)

    schedule_posts(bot=bot, chat_id=Config.CHAT_ID)


# ───────────── Генерация поста ─────────────
async def generate_post(message: Message, bot: Bot):
    """Обработчик запросов пользователя на генерацию постов"""

    # 1. Проверка ввода
    user_input = message.text
    if not user_input:
        await message.answer("Пожалуйста, отправьте ссылку на источник.")
        return


    # 2. Выбор типа поста
    try:
        post_type = await handle_post_type_choice(bot, message)
    except asyncio.TimeoutError:
        await message.reply("⏳ Время на выбор истекло.")
        return
    await message.answer(f"Вы выбрали: {post_type}")


    # 3. Оповещение, что бот работает - отправляем временное сообщение
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    temp = await message.answer("Формирую пост...")


    # 4. Получение результатов парсинга
    if "t.me" in user_input:
        data = await telegram_parser(user_input)
    else:
        data = web_parser(user_input)

    data += "Ссылка на источник: " + user_input


    # 5. Генерация ответа
    try:
        formatted_text = await llama_reply(data, post_type)
    except Exception as e:
        await message.reply(f"Произошла ошибка при генерации: {e}")
        # Удаляем "Формирую пост..." даже при ошибке
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=temp.message_id)
        except Exception:
            pass
        return

    # 6. Удаление временного сообщения
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=temp.message_id)
    except Exception:
        pass

    # 7. Сохраняем информацию о посте
    user_step[message.from_user.id] = {"step": "awaiting_post_id",
                                       "text": formatted_text,
                                       "post_type": post_type,
                                       "source": user_input}


    # 8. Отправка результата генерации
    await message.reply(formatted_text, parse_mode="HTML")


async def handle_post_type_choice(bot: Bot, message: Message) -> str:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Анонс", callback_data="anons")],
        [InlineKeyboardButton(text="📰 Новости", callback_data="news")]
    ])

    sent_msg = await message.answer("Выберите тип поста:", reply_markup=keyboard)

    loop = asyncio.get_event_loop()
    future = loop.create_future()
    choice_waiters[message.from_user.id] = future

    try:
        # Ждем выбора пользователя (макс. 30 сек)
        choice = await asyncio.wait_for(future, timeout=30.0)
        return choice
    finally:
        # Чистим за собой
        choice_waiters.pop(message.from_user.id, None)
        await bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)


# ───────────── Processing постов ─────────────

async def post_edit(post_id: str, new_text: str):
    update_post(post_id=post_id, text=new_text)


async def handle_momentum_edit_choice(message: Message, bot: Bot):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ДА", callback_data="yes")],
        [InlineKeyboardButton(text="НЕТ", callback_data="no")]
    ])

    choice_waiters.clear()

    sent_msg = await message.answer("Хотите что-то изменить в тексте поста?", reply_markup=keyboard)

    loop = asyncio.get_event_loop()
    future = loop.create_future()
    choice_waiters[message.from_user.id] = future

    try:
        # Ждем выбора пользователя (макс. 30 сек)
        choice = await asyncio.wait_for(future, timeout=30.0)
        return choice
    finally:
        # Чистим за собой
        choice_waiters.pop(message.from_user.id, None)
        await bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)


# ───────────── Callback'и ─────────────
@router.callback_query(F.data.in_({"anons", "news"}))
async def on_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    future = choice_waiters.get(user_id)

    if future and not future.done():
        future.set_result(callback.data)

    await callback.answer()


@router.callback_query(F.data == "new")
async def handle_new_post(callback: CallbackQuery, bot: Bot):
    await callback.message.answer("Пришли ссылку на источник")
    user_step[callback.from_user.id] = {"step": "awaiting_link"}  # Переход в шаг генерации поста
    await callback.answer()


@router.callback_query(F.data == "view")
async def handle_view_posts(callback: CallbackQuery, bot: Bot):
    posts = download_posts()
    if not posts:
        await bot.send_message(callback.from_user.id,"У тебя пока нет активных постов.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=post_id,
                                  callback_data=f"select_post_{post_id}")]
            for post_id in posts
        ]
    )

    await bot.send_message(callback.from_user.id, "Выбери пост для взаимодействия:", reply_markup=keyboard)

    user_step[callback.from_user.id] = "posts_design"  # Переход в шаг процессинга постов
    await callback.answer()


# Выбор поста
@router.callback_query(F.data.startswith("select_post_"))
async def post_action_choice(callback: CallbackQuery, bot: Bot):
    post_id = callback.data.replace("select_post_", "")
    posts = download_posts()

    post = posts.get(post_id)
    if not post:
        await callback.message.answer("⚠️ Пост не найден.")
        return


    output=f"📌 Данные поста **{post_id}**\n" + json.dumps(post, ensure_ascii=False, indent=2)

    await callback.message.answer(output)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{post_id}")],
        [InlineKeyboardButton(text="✏ Изменить текст", callback_data=f"edit_text_{post_id}")],
        [InlineKeyboardButton(text="🕓 Изменить дату", callback_data=f"edit_date_{post_id}")],
        [InlineKeyboardButton(text="📤 Выложить через минуту", callback_data=f"publish_{post_id}")]
    ])

    await callback.message.answer("Выберите действие с постом", reply_markup=keyboard)
    await callback.answer()

# Удаление поста
@router.callback_query(F.data.startswith("delete_"))
async def delete_post(callback: CallbackQuery, bot: Bot):
    post_id = callback.data.replace("delete_", "")
    posts = download_posts()
    if post_id in posts:
        del posts[post_id]
        upload_posts(posts)
        await callback.message.answer(f"✅ Пост **{post_id}** удалён.")
    else:
        await callback.message.answer("⚠️ Пост не найден.")

    schedule_posts(bot=bot,chat_id=Config.CHAT_ID)
    await callback.answer()

# Публикация через минуту (имитация)
@router.callback_query(F.data.startswith("publish_"))
async def publish_post(callback: CallbackQuery, bot: Bot):
    post_id = callback.data.replace("publish_", "")
    posts = download_posts()
    post = posts.get(post_id)
    if not post:
        await callback.message.answer("⚠️ Пост не найден.")
        return

    update_post(post_id, scheduled_time=datetime.now() + timedelta(minutes=1))
    await callback.message.answer("⏱ Пост будет опубликован через минуту...")

    schedule_posts(bot=bot, chat_id=Config.CHAT_ID)
    await callback.answer()

# Редактирование текста поста
@router.callback_query(F.data.startswith("edit_text_"))
async def ask_new_text(callback: CallbackQuery, bot: Bot):
    post_id = callback.data.replace("edit_text_", "")
    await callback.message.answer(f"✏ Отправь новый текст для поста {post_id}")
    user_step[callback.from_user.id]={"step": "post_editing", "post_id": post_id}

    await callback.answer()


# Редактирование даты публикации
@router.callback_query(F.data.startswith("edit_date_"))
async def ask_new_date(callback: CallbackQuery, state: dict):
    post_id = callback.data.replace("edit_date_", "")
    await callback.message.answer("📅 Введи новую дату и время в формате `YYYY-MM-DD HH:MM`")
    user_step[callback.from_user.id] = {"step": "time_editing", "post_id": post_id}
    await callback.answer()


@router.callback_query(F.data.in_({"yes", "no"}))
async def edit_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    future = choice_waiters.get(user_id)

    if future and not future.done():
        future.set_result(callback.data)

    await callback.answer()