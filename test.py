import json

from together import Together
from dotenv import load_dotenv
from bot.config import Config
import requests

# LLM_TOKEN=os.getenv("LLM_TOKEN")
#
# # API-ключ
# client = Together(api_key=LLM_TOKEN)
#
# response = client.chat.completions.create(
#     model="meta-llama/Llama-Vision-Free",
#     messages=[{"role": "system", "content": "пользователь дает тебе ссылку на пост в телеграме. оформляй текст в виде поста для телеграм канала, в котором анонсируются мероприятия"},
#               {"role": "user", "content": ""}],
# )
# print(response.choices[0].message.content)


# url = "https://openrouter.ai/api/v1/chat/completions"
#
# headers = {
#     "Authorization": f"Bearer {Config.API_KEY}",
#     "Content-Type": "application/json"
# }
#
# data = {
#     "model": "qwen/qwen2.5-vl-72b-instruct:free",
#     "messages": [
#         {"role": "user", "content": input()}
#     ]
# }
#
# response = requests.post(url, headers=headers, json=data)
# print(response.json()["choices"][0]["message"]["content"])


with open("posts.json", "r", encoding="utf-8") as f:
    posts=json.load(f)
    print(json.dumps(posts["111"],ensure_ascii=False, indent=2))