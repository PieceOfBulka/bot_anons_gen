from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import json


def download_posts():
    with open("posts.json", "r", encoding="utf-8") as f:
        return json.load(f)


def upload_posts(posts: dict):
    with open("posts.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(posts, ensure_ascii=False, indent=2))


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
    scheduler = AsyncIOScheduler()
    posts = download_posts()

    for post_id in posts:
        if posts[post_id]["scheduled_time"] is None: continue
        post_time = datetime.strptime(posts[post_id]["scheduled_time"], "%Y-%m-%d %H:%M")
        scheduler.add_job(bot.send_message, "date", run_date=post_time,
                          args=[chat_id, posts[post_id]["text"]], kwargs={"parse_mode": "HTML"})

    scheduler.start()