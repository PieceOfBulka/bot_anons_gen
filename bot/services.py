from together import Together
from bot.config import Config

import unicodedata

client_ll = Together(api_key=Config.LLM_TOKEN)


def clean_text(text: str) -> str:
    """
    Удаляет или заменяет неподдерживаемые символы.
    """
    # Попытка нормализовать текст, чтобы избежать ошибок с кодировками
    normalized_text = unicodedata.normalize('NFKD', text)
    clean_text = normalized_text.encode('ascii', 'ignore').decode('ascii')
    return clean_text


async def llama_reply(user_input: str, gen_mode: str) -> str:
    """ Ответ модели"""
    if gen_mode == "anons":
        instruction = open("instructions/anons/final_instruction.txt", encoding='utf-8').readlines()
    else:
        instruction = open("instructions/news_inst.txt", encoding='utf-8').readlines()

    response = client_ll.chat.completions.create(
        model="meta-llama/Llama-Vision-Free",
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content


import requests
import time


async def openrouter_reply(data: str, gen_mode: str) -> str:
    if gen_mode == "anons":
        instruction = open("instructions/anons/final_instruction.txt", encoding='utf-8').readlines()
    else:
        instruction = open("instructions/news_inst.txt", encoding='utf-8').readlines()

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {Config.API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": [
            {"role": "system", "content": ' '.join(instruction)},
            {"role": "user", "content": data}
        ]
    }

    start = time.time()
    response = requests.post(url, headers=headers, json=data)
    print(time.time() - start)

    if response.status_code == 200:
        try:
            content = response.json()["choices"][0]["message"]["content"]
            return content.strip() if content else "⚠️ Пустой ответ от модели."
        except Exception as e:
            return f"⚠️ Ошибка обработки ответа: {str(e)}"
    else:
        return f"❌ Ошибка {response.status_code}: {response.text}"
