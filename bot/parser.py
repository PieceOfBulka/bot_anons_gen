import requests
from bs4 import BeautifulSoup
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChannel
from bot.config import Config

def web_parser(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Получение всей текстовой информации
    promt=soup.get_text()

    return promt


async def telegram_parser(url: str) -> str:
    api_id = Config.TG_API_ID
    api_hash = Config.API_HASH

    # Получаем ID поста и канала
    post_id = int(url.split('/')[-1])
    channel = url.split('/')[-2]

    client = TelegramClient('my_session', api_id, api_hash)

    async with client:
        if channel.isdigit():
            channel_peer_id=int(channel)
            entity = None

            async for dialog in client.iter_dialogs():
                if dialog.entity.id == channel_peer_id:
                    entity = dialog.entity
                    break

            if not entity:
                raise Exception(f"Чат с peer_id {channel_peer_id} не найден. Убедись, что ты участник группы/канала.")
        else:
            entity = await client.get_entity(channel)  # можно использовать @username

        message = await client.get_messages(entity, ids=post_id)

        return message.text


if __name__=='__main__':
    s=input()
    telegram_parser(s)
