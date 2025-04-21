from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import json

scheduler = AsyncIOScheduler()

def download_posts():
    with open("posts.json", "r", encoding="utf-8") as f:
        return json.load(f)


def upload_posts(posts: dict):
    with open("posts.json", 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def update_post(post_id: str, text: str =None, post_type: str =None, source: str =None, scheduled_time: datetime =None):
    posts = download_posts()
    if post_id not in posts:
        return "Такого поста не существует"

    if text is None: text=posts[post_id]["text"]
    if post_type is None: post_type=posts[post_id]["post_type"]
    if source is None: source=posts[post_id]["source"]
    if scheduled_time is None: scheduled_time=posts[post_id]["scheduled_time"]
    created_time=posts[post_id]["created_time"]

    posts[post_id] = {
        "text": text,
        "post_type": post_type,
        "source": source,
        "scheduled_time": scheduled_time if isinstance(scheduled_time, str) else scheduled_time.strftime("%Y-%m-%d %H:%M"),
        "created_time": created_time
    }
    upload_posts(posts)


def get_post(key: str):
    posts=download_posts()
    if key not in posts:
        return "Такого поста не существует"
    return posts[key]


def add_post(post_id: str, text: str, post_type: str, source: str):
    posts = download_posts()
    if posts == '':
        posts={}
    if post_id in posts:
        return "Пост с таким ключом уже существует"
    posts[post_id] = {
        "text": text,
        "post_type": post_type,
        "source": source,
        "scheduled_time": None,
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    upload_posts(posts)


def delete_post(key: str):
    posts=download_posts()
    if key not in posts:
        return "Такого поста не существует"
    posts.pop(key)
    upload_posts(posts)


def schedule_posts(bot, chat_id):
    posts = download_posts()

    # обновляем данные по публикации постов
    for post_id in posts:
        # Удаляем предыдущее задание, если оно есть
        job_id = f"job_{post_id}"
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)

        # приводим дату к типу datetime
        scheduled_time = posts[post_id].get("scheduled_time")
        if not scheduled_time:
            print(f"[!] Пост {post_id} не имеет scheduled_time, пропускаем.")
            continue

        post_time = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M")

        # Добавляем новое задание
        scheduler.add_job(
            bot.send_message,
            "date",
            run_date=post_time,
            args=[chat_id, posts[post_id]["text"]],
            kwargs={"parse_mode": "HTML"},
            id=job_id  # <-- указываем ID
        )


def cleanup_old_posts():
    posts = download_posts()

    updated_posts = {
        post_id: post
        for post_id, post in posts.items()
        if datetime.strptime(post["scheduled_time"], "%Y-%m-%d %H:%M") < datetime.now() and
           datetime.now() - datetime.strptime(post["scheduled_time"], "%Y-%m-%d %H:%M") > timedelta(days=7)
    }

    if len(updated_posts) != len(posts):
        upload_posts(updated_posts)